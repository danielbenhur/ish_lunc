#!/usr/bin/env python3
import argparse
import os
import glob
import sys
import pandas as pd
import geopandas as gpd
import fiona
from scripts.aplica_recortes import aplica_recortes_gpkg

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
    """
    # Para cada linha, filtra apenas valores > 0 e calcula a média
    return gdf[dim_cols].apply(lambda row: row[row > 0.0].mean(), axis=1)

def main():
    parser = argparse.ArgumentParser(
        description="Gera o GPKG de ISH para um cenário e aplica recortes opcionais")
    parser.add_argument("cenario", help="Nome do cenário (ex: atlas2035)")
    parser.add_argument("-r", "--recorte", action="append", default=[],
                        help="Nome do recorte (arquivo .gpkg dentro de recortes/) sem extensão. Pode repetir para vários recortes.")
    args = parser.parse_args()

    nome_cenario = args.cenario
    recortes_escolhidos = args.recorte  # lista de strings, pode ser vazia
    
    # Define a pasta base do cenário e cria as subpastas necessárias
    root_folder = os.getcwd()
    base_dir = os.path.expanduser(f"{root_folder}/cnr_{nome_cenario}")
    for subfolder in ["input", "output"]:
#    for subfolder in ["input", "output", "middle", "layout", "scripts"]:
        os.makedirs(os.path.join(base_dir, subfolder), exist_ok=True)
    
    # Define as pastas de input e output
    input_folder = os.path.join(base_dir, "input")
    output_folder = os.path.join(base_dir, "output")
    
    # O arquivo GeoPackage está dentro da pasta "input"
    gpkg_file = os.path.join(input_folder, "BHO_area.gpkg")
    
    # Lista e exibe as camadas disponíveis e o schema para diagnóstico
    layers = fiona.listlayers(gpkg_file)
    print("Camadas disponíveis:", layers)
    layer = "bho_area"  # Certifique-se de que esta é a camada correta
    
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
    
    # Procura por arquivos CSV de dimensão no diretório "input"
    csv_pattern = os.path.join(input_folder, f"dim_*.csv")
    csv_files = glob.glob(csv_pattern)
    
    # Itera sobre cada arquivo CSV: imprime preview e faz o merge com o GeoDataFrame
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, sep=None, engine='python')
        except Exception as e:
            print(f"Erro ao ler o arquivo {csv_file}: {e}")
            continue
        
        # Padroniza os nomes das colunas para letras minúsculas
        df.columns = df.columns.str.strip().str.lower()
        print(f"\nPreview (head) do arquivo CSV '{os.path.basename(csv_file)}':")
        print(df.head())
        
        if "cobacia" not in df.columns:
            print(f"Aviso: A coluna 'cobacia' não foi encontrada no arquivo {csv_file}.")
            continue
        try:
            df["cobacia"] = df["cobacia"].astype("Int64")

        except Exception as e:
            print(f"Erro convertendo 'cobacia' no CSV {csv_file} para int: {e}")
            continue
        
        # Identifica a coluna de dimensão (excluindo 'cobacia')
        dimension_columns = [col for col in df.columns if col != "cobacia"]
        if len(dimension_columns) != 1:
            print(f"Aviso: O arquivo {csv_file} não possui exatamente uma coluna de dimensão.")
            continue
        
        dim_col = dimension_columns[0]
        # Converte os valores da dimensão para float, tratando vírgulas como separador decimal
        df[dim_col] = pd.to_numeric(df[dim_col].astype(str).str.replace(",", "."), errors="coerce")
        
        # Realiza a junção (merge) com o GeoDataFrame usando a coluna "cobacia"
        gdf = gdf.merge(df[["cobacia", dim_col]], on="cobacia", how="left")
    
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
    print(gdf_final.head())
    
    # Salva a camada "regiao_completa"
    output_file = os.path.join(output_folder, f"ish_cnr_{nome_cenario}.gpkg")
    if os.path.isfile(output_file):
        os.remove(output_file)
    gdf_final.to_file(output_file, driver="GPKG", layer="regiao_completa")
    print(f"Arquivo salvo em {output_file}")

    ## Chama a função do script externo para gerar as demais camadas de recorte
    # recs = aplica_recortes_gpkg(root_folder, recortes_escolhidos)
    # if recs:
        # print("###### Recortes aplicados:", ", ".join(recs))
    # else:
        # print("###### Nenhum recorte aplicado.")
        
if __name__ == "__main__":
    main()

