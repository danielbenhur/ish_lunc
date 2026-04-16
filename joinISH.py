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

# Converte apenas colunas específicas (ou todas exceto algumas)
def convert_columns(df, columns=None, exclude=[]):
    """
    columns: lista de colunas a converter (se None, converte todas exceto 'exclude')
    exclude: lista de colunas a ignorar
    """
    if columns is None:
        columns = [col for col in df.columns if col not in exclude]
    
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Gera o GPKG de ISH para um cenário e aplica recortes opcionais")
    parser.add_argument("cenario", help="Nome do cenário (ex: atlas2035)")
    parser.add_argument("-r", "--recorte", action="append", default=[],
                        help="Nome do recorte (arquivo .gpkg dentro de recortes/) sem extensão. Pode repetir para vários recortes.")
    parser.add_argument("-s", "--scenario-file", default=None,
                        help="(opcional) arquivo YAML de cenário. Se informado, parametros do YAML (bho.path, bho.layer, base_dir, dimensions, output.folder) serão usados.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria executado, mas NÃO roda nada e não salva arquivos.")
  
    args = parser.parse_args()

    nome_cenario = args.cenario
    recortes_escolhidos = args.recorte  # lista de strings, pode ser vazia
    scenario_yaml = args.scenario_file
    scenario = None
    dry_run = args.dry_run
    # se foi especificado um YAML de cenário, carregue e valide
    if scenario_yaml:
        if yaml is None:
            print("ERRO: 'pyyaml' não está instalado. Instale com 'pip install pyyaml' para usar --scenario-file.")
            sys.exit(1)
        try:
            scenario_path = Path(scenario_yaml).expanduser().resolve()
            with open(scenario_path, "r", encoding="utf-8") as sf:
                scenario = yaml.safe_load(sf)
            print("Cenário YAML carregado de:", scenario_path)
        except Exception as e:
            print("Erro ao ler o YAML de cenário:", e)
            sys.exit(1)
    if dry_run:
        print("\n==============================")
        print("        DRY RUN ATIVO")
        print("==============================\n")
    
    # Define a pasta base do cenário e cria as subpastas necessárias
    root_folder = os.getcwd()
    # se o YAML definiu base_dir, use-o (resolvido relativo ao YAML); senão use o padrão ./cnr_<nome_cenario>
    if scenario and scenario.get("base_dir"):
        base_dir_raw = scenario.get("base_dir")
        # se caminho for relativo, resolva em relação ao diretório do YAML
        yaml_dir = Path(scenario_yaml).parent if scenario_yaml else Path(root_folder)
        base_dir = str((yaml_dir / base_dir_raw).resolve()) if not os.path.isabs(base_dir_raw) else base_dir_raw
    else:
        base_dir = os.path.expanduser(f"{root_folder}/cnr_{nome_cenario}")
    if dry_run:
        print(f"[dry-run] Base dir seria: {base_dir}")
    for subfolder in ["input", "output"]:
        os.makedirs(os.path.join(base_dir, subfolder), exist_ok=True)

    # Define as pastas de input e output (possíveis overrides via YAML)
    input_folder = os.path.join(base_dir, "input")
    output_folder = os.path.join(base_dir, "output")
    if scenario and scenario.get("output") and scenario["output"].get("folder"):
        out_raw = scenario["output"].get("folder")
        yaml_dir = Path(scenario_yaml).parent if scenario_yaml else Path(root_folder)
        output_folder = str((yaml_dir / out_raw).resolve()) if not os.path.isabs(out_raw) else out_raw
        os.makedirs(output_folder, exist_ok=True)

    # O arquivo GeoPackage do BHO: prefer value do YAML, senão o padrão input/BHO_area.gpkg
    if scenario and scenario.get("bho") and scenario["bho"].get("path"):
        bho_raw = scenario["bho"].get("path")
        yaml_dir = Path(scenario_yaml).parent if scenario_yaml else Path(root_folder)
        gpkg_file = str((yaml_dir / bho_raw).resolve()) if not os.path.isabs(bho_raw) else bho_raw
    else:
        gpkg_file = os.path.join(input_folder, "BHO_area.gpkg")
    if dry_run:
        print(f"[dry-run] BHO GPKG seria: {gpkg_file}")
    
    # Lista e exibe as camadas disponíveis e o schema para diagnóstico
    layers = fiona.listlayers(gpkg_file)
    print("Camadas disponíveis:", layers)
    # camada do BHO: pode ser sobrescrita no YAML
    layer = "bho_area"  # default
    if scenario and scenario.get("bho") and scenario["bho"].get("layer"):
        layer = scenario["bho"].get("layer")
    
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
    
    # Procura por arquivos CSV de dimensão.
    # Se o YAML tiver 'dimensions', respeitamos essa lista (cada item pode ter 'path' ou 'file_glob').
    csv_files = []
    if scenario and scenario.get("dimensions"):
        yaml_dir = Path(scenario_yaml).parent if scenario_yaml else Path(root_folder)
        for dim in scenario.get("dimensions", []):
            if dim is None:
                continue
            # item pode ser string path ou dict
            if isinstance(dim, str):
                # interpret as path relative ao base_dir / yaml_dir
                p = Path(dim)
                if not p.is_absolute():
                    p = (yaml_dir / dim)
                csv_files.append(str(p))
            elif isinstance(dim, dict):
                if dim.get("path"):
                    p = Path(dim["path"])
                    if not p.is_absolute():
                        p = (yaml_dir / dim["path"])
                    csv_files.append(str(p))
                elif dim.get("file_glob"):
                    pat = dim["file_glob"]
                    p = Path(pat)
                    if not p.is_absolute():
                        pat = str((yaml_dir / pat))
                    matches = glob.glob(pat)
                    csv_files.extend(matches)
    # fallback: procura padrão dim_*.csv dentro da pasta input
    if not csv_files:
        csv_pattern = os.path.join(input_folder, f"dim_*.csv")
        csv_files = glob.glob(csv_pattern)
    if dry_run:
        print("[dry-run] Arquivos CSV detectados:")
        for c in csv_files:
            print("   -", c)
    
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
        
        df = convert_columns(df, exclude=['cobacia'])
        gdf = gdf.merge(df, on="cobacia", how="left")
    
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
    # nome do gpkg final: pode ser sobrescrito no YAML (output.gpkg_name), senão usa padrão
    gpkg_name = f"ish_cnr_{nome_cenario}.gpkg"
    if scenario and scenario.get("output") and scenario["output"].get("gpkg_name"):
        gpkg_name = scenario["output"].get("gpkg_name")
    output_file = os.path.join(output_folder, gpkg_name)

    if dry_run:
        print(f"[dry-run] Arquivo final GPKG seria salvo em: {output_file}")
        print("\n[dry-run] Nada será executado. Finalizando.")
        sys.exit(0)    
    
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

