#!/usr/bin/env python3
import argparse
import os
import glob
import sys
import pandas as pd
import geopandas as gpd
import fiona
from pathlib import Path
import json
import yaml
from scripts.aplica_recortes import aplica_recortes_gpkg
from function_modules_ish_hum.convertion_functions import *

def load_gpkg_with_fid(filename, layer):
    """
    Lê um GeoPackage usando fiona e inclui o FID (feature id)
    no dicionário de propriedades como 'cobacia'
    """
    features = []
    with fiona.open(filename, layer=layer) as src:
        for feat in src:
            # Converte as propriedades para um dicionário
            props = dict(feat['properties'])
            try:
                # O campo 'id' vem como string; convertemos para inteiro.
                props['cobacia'] = int(feat['id'])
            except ValueError:
                props['cobacia'] = feat['id']
            features.append({
                "properties": props,
                "geometry": feat["geometry"]
            })
        crs = src.crs
    return gpd.GeoDataFrame.from_features(features, crs=crs)

def compute_cs_ish(gdf, dim_cols):
    """
    Recebe um GeoDataFrame e uma lista de colunas de dimensão (por exemplo,
    ['ire_cs_hum', 'ire_cs_eco', ...]). Retorna uma Series contendo a média
    das colunas, considerando apenas valores maiores que 0.0 (ignorando zeros e NaN).
    Quando não tiver valores na linha, o cs_ish será 0
    """
    df_numeric = gdf[dim_cols].apply(pd.to_numeric, errors='coerce')
    # Para cada linha, filtra apenas valores > 0 e calcula a média

    return df_numeric.apply(lambda row: row[row > 0.0].mean() if (row[row > 0.0].count() > 0) else 0.0, axis=1)

# Converte apenas colunas específicas (ou todas exceto algumas)
def convert_columns(df, columns=None, exclude=[]):
    if columns is None:
        columns = [col for col in df.columns if col not in exclude]
    
    for col in columns:
        if col in df.columns:
            def clean_value(x):
                if pd.isna(x):
                    return x
                
                s = str(x).strip()
                
                # Verifica se parece um número (com vírgula/ponto)
                # Aceita padrões: 123, 123.45, 1.234,56, 1234,56
                import re
                # Remove espaços e R$ se existir
                s = s.replace('R$', '').replace(' ', '').strip()
                
                # Se tem letras, mantém como está
                if re.search(r'[A-Za-zÀ-ÿ]', s) and not re.match(r'^[\d\.,]+$', s):
                    return x  # Retorna o valor original
                
                # Tenta converter
                try:
                    # Caso "1.234,56"
                    if '.' in s and ',' in s and s.rfind(',') > s.rfind('.'):
                        s = s.replace('.', '').replace(',', '.')
                    # Caso "1234,56"
                    elif ',' in s and '.' not in s:
                        s = s.replace(',', '.')
                    
                    return pd.to_numeric(s)
                except:
                    return x  # Se falhar, mantém original
            
            df[col] = df[col].apply(clean_value)
    
    return df


def main():
    yaml_file_path = "parameters.yaml"
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)
    dry_run = False
    if dry_run:
        print("\n==============================")
        print("        DRY RUN ATIVO")
        print("==============================\n")
    
    # print(config)
    # Define a pasta base do cenário e cria as subpastas necessárias
    root_folder = os.getcwd()
    
    
    # o base_dir precisa ser um parametro dentro do arquivo yaml (não iremos criar pastas nesse código)
    base_dir = config.get('base_dir')
    
    if dry_run:
        print(f"[dry-run] Base dir seria: {base_dir}")

    # TODO: ajustar o input e o output para englobar direito o que se uer fazer no YAML
    for subfolder in ["input", "output"]:
        os.makedirs(os.path.join(base_dir, subfolder), exist_ok=True) # TODO: entender como isso será plenamente usado
        # proposta de colocar input como padrão obrigatório com os arquivos base definidos (o jeito que está agora não propõe isso)

    gpkg_file = config['bho'].get('path') # bho é pra definir gpkg

    if dry_run:
        print(f"[dry-run] BHO GPKG seria: {gpkg_file}")
    
    # Lista e exibe as camadas disponíveis e o schema para diagnóstico
    layers = fiona.listlayers(gpkg_file)
    print("Camadas disponíveis:", layers)
    # camada do BHO: pode ser sobrescrita no YAML
    layer = "bho_area"  # default
    if config["bho"].get("layer"):
        layer = config["bho"].get("layer")
    
    try:
        with fiona.open(gpkg_file, layer=layer) as src:
            print("Schema da camada:", src.schema)
            print("Atributos presentes:", src.schema['properties'])
    except Exception as e:
        print(f"Erro ao abrir o arquivo {gpkg_file} com fiona: {e}")
        sys.exit(1)
    
    # Carrega o GeoPackage utilizando a função que extrai a FID como 'cobacia'
    gdf = load_gpkg_with_fid(gpkg_file, layer)
    
    # Padroniza os nomes das colunas para letras minúsculas
    gdf.columns = gdf.columns.str.strip().str.lower()
    
    # Imprime um preview do arquivo BHO_area.gpkg antes do processamento das colunas
    print("\nPreview (head) do arquivo BHO_area.gpkg (antes do processamento das colunas):")
    print(gdf.head())
    
    # Define a coluna de geometria ativa para "geometry"
    if "geometry" in gdf.columns:
        gdf = gdf.set_geometry("geometry")
        print("Coluna de geometria ativa:", gdf.geometry.name)
    else:
        print("Erro: Coluna 'geometry' não encontrada!")
        sys.exit(1)
    
    # Imprime um preview após a inclusão da coluna 'cobacia'
    print("\nPreview (head) do arquivo BHO_area.gpkg (depois do processamento das colunas):")
    print(gdf.head())
    
    # Define ou converte o CRS para EPSG:4674 (SIRGAS 2000)
    if gdf.crs is None:
        gdf.set_crs(epsg=4674, inplace=True)
    else:
        gdf = gdf.to_crs(epsg=4674)
    
    # Aqui usaremos as funções de convertion_functions.py para calcular as dimensões
    dimensions = config['dimensions']
    functions_to_work = []
    
    dados_entregues = None
    for dimensao in dimensions:
        functions_to_work.extend(list_functions(dimensao))
        df_temp = pd.read_csv(dimensao['path'],
            decimal=',',  # trata vírgula como separador decimal
            thousands='.'  # trata ponto como separador de milhar (se necessário)
        )

        if dados_entregues is None:
            dados_entregues = df_temp
        else:
            dados_entregues = pd.concat([dados_entregues, df_temp], ignore_index=True)

    # A QUANTIDADE DE LINHAS COM VALORES CORRESPONDENTES DE COBACIA NÃO ESTÀ COORDENADO ENTRE geodataframe e os arquivos csv

    coluna_cobacia_csv = 'COBACIA' 
    coluna_cobacia_gdf = 'cobacia'
    dados_entregues = dados_entregues[dados_entregues[coluna_cobacia_csv].isin(gdf[coluna_cobacia_gdf])].copy()

    if coluna_cobacia_csv in dados_entregues.columns:
        dados_entregues = dados_entregues.groupby(coluna_cobacia_csv).first().reset_index()

    for item in functions_to_work:
        funcao = globals()[item['indicador']]
        parametros_colunas = []
        # print(funcao)
        for dependencia in item['depends_on']:
            if(dependencia == 'dmu_nu_popurbana'):
                print(dados_entregues[dependencia])
            if dependencia in gdf.columns:
                parametros_colunas.append(gdf[dependencia])
            elif dependencia in dados_entregues.columns:
                parametros_colunas.append(dados_entregues[dependencia])
            else:
                # Converte para número se for constante
                try:
                    valor_constante = float(dependencia)
                except (ValueError, TypeError):
                    print(f"Erro: {dependencia} não é uma coluna nem um número")
                    valor_constante = 0
                coluna_constante = pd.Series([valor_constante] * len(dados_entregues), index=dados_entregues.index)
                parametros_colunas.append(coluna_constante)
    
        if 'column' in item:
            print(f"{item['indicador']} {item['depends_on']}")
            # dados_entregues[item['column']] = funcao(parametros_colunas)
            gdf[item['column']] = funcao(parametros_colunas)
        else:
            # dados_entregues[item['indicador']] = funcao(parametros_colunas)
            gdf[item['indicador']] = funcao(parametros_colunas)


    # Seleciona todas as colunas que começam com "ire_cs_"
    dimension_cols = [col for col in gdf.columns if col.startswith("ire_cs_")]
    # Cria a coluna "cs_ish" a partir da média das dimensões não nulas
    gdf["cs_ish"] = compute_cs_ish(gdf, dimension_cols)
    
    # Monta lista final de colunas para manter no arquivo de saída:
    # 'cobacia' + colunas de dimensão + 'cs_ish' + geometria
    cols_to_keep = ["cobacia"] + dimension_cols + ["cs_ish", "geometry"]
    gdf_final = gdf[cols_to_keep]
    
    # Imprime o cabeçalho (head) do GeoDataFrame final para verificação
    print("\nPreview (head) do GeoDataFrame final:")
    print(gdf.head())
    
    print(config['id'])
    # Salva a camada "regiao_completa"
    # nome do gpkg final: pode ser sobrescrito no YAML (output.gpkg_name), senão usa padrão
    gpkg_name = f"ish_cnr_{config['id']}.gpkg"
    output_folder = "./"
    if config and config.get("output") and config["output"].get("gpkg_name"):
        gpkg_name = config["output"].get("gpkg_name")
        output_folder = config["output"].get('folder')
    output_file = os.path.join(output_folder, gpkg_name)

    if dry_run:
        print(f"[dry-run] Arquivo final GPKG seria salvo em: {output_file}")
        print("\n[dry-run] Nada será executado. Finalizando.")
        sys.exit(0)    
    
    if os.path.isfile(output_file):
        os.remove(output_file)
    gdf.to_file(output_file, driver="GPKG", layer="regiao_completa")
    gdf.to_csv("./output/my_data.csv", index=False)
    print(f"Arquivo salvo em {output_file}")

    ## Chama a função do script externo para gerar as demais camadas de recorte
    # recs = aplica_recortes_gpkg(root_folder, recortes_escolhidos)
    # if recs:
        # print("###### Recortes aplicados:", ", ".join(recs))
    # else:
        # print("###### Nenhum recorte aplicado.")
        
if __name__ == "__main__":
    main()

