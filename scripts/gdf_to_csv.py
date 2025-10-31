#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gdf_to_csv.py

Converte um arquivo vetorial (gpkg/shp/geojson/...) para CSV e salva no mesmo diretório.
Uso:
  python scripts/gpkg_to_csv.py /caminho/para/arquivo.gpkg
  python scripts/gpkg_to_csv.py /caminho/para/arquivo.gpkg --layer regiao_completa --geom centroid --to-wgs84

Opções:
  --layer LAYER        : nome da layer dentro do GPKG (se aplicável)
  --geom {wkt,centroid,x_y,none} : como incluir geometria no CSV (default: wkt)
  --to-wgs84           : reprojetar para EPSG:4326 antes de extrair centroid/coords
  --overwrite          : sobrescrever CSV de saída se existir
  --encoding ENCODING  : encoding do CSV (default utf-8)
"""
import argparse
import os
from pathlib import Path

import geopandas as gpd

def main():
    p = argparse.ArgumentParser(description="Converter vetor -> CSV (mesma pasta, mesmo nome).")
    p.add_argument("input", help="Caminho para o arquivo vetorial (.gpkg .shp .geojson ...)")
    p.add_argument("--layer", help="Nome da layer (apenas para GPKG). Se omitido e houver >1 layer, usa a primeira.")
    p.add_argument("--geom", choices=["wkt", "centroid", "x_y", "none"], default="wkt",
                   help="Como salvar a geometria no CSV. default=wkt")
    p.add_argument("--to-wgs84", action="store_true", help="Reprojetar para EPSG:4326 antes de extrair centroid/coords")
    p.add_argument("--overwrite", action="store_true", help="Sobrescrever CSV de saída se já existir")
    p.add_argument("--encoding", default="utf-8", help="Encoding do CSV (default utf-8)")
    args = p.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Arquivo não encontrado: {input_path}")

    # decide a camada (se gpkg)
    layer = args.layer
    if input_path.suffix.lower() == ".gpkg":
        try:
            import fiona
            layers = fiona.listlayers(str(input_path))
        except Exception as e:
            # se fiona não puder ser importado, dar uma mensagem clara
            raise SystemExit(
                "Erro ao listar layers do arquivo. O módulo 'fiona' não está disponível ou falhou ao importar.\n"
                f"Detalhes: {e}\n\n"
                "Correção sugerida: instale fiona/GDAL via conda-forge:\n"
                "  mamba install -y -c conda-forge fiona geopandas gdal\n"
                "ou (menos recomendável) instale dependências do sistema e pip:\n"
                "  sudo apt-get install -y gdal-bin libgdal-dev libproj-dev proj-bin\n"
                "  pip install fiona geopandas\n"
            )
        if len(layers) == 0:
            raise SystemExit("Nenhuma layer encontrada no GPKG.")
        if layer is None:
            if len(layers) > 1:
                print(f"Aviso: GPKG contém várias layers. Usando a primeira: '{layers[0]}'. Use --layer para escolher outra.")
            layer = layers[0]

    # leitura
    if layer:
        gdf = gpd.read_file(str(input_path), layer=layer)
    else:
        gdf = gpd.read_file(str(input_path))

    # output path: mesma pasta, mesmo nome (se gpkg com várias layers, adiciona layer ao nome)
    if input_path.suffix.lower() == ".gpkg" and args.layer is None and len(gpd.io.file.fiona.listlayers(str(input_path))) > 1:
        # se usuário não indicou layer e gpkg tem várias layers, já avisamos; inclua layer no nome para evitar sobreposição
        out_name = f"{input_path.stem}__{layer}.csv"
    else:
        out_name = f"{input_path.stem}.csv"
    out_path = input_path.with_name(out_name)

    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"Arquivo de saída já existe: {out_path}. Use --overwrite para sobrescrever.")

    # opcional reprojeção para WGS84 se usuário pediu (aplica quando geom output é centroid ou x_y)
    if args.to_wgs84:
        try:
            gdf = gdf.to_crs(epsg=4326)
        except Exception as e:
            print("Aviso: erro ao reprojetar para EPSG:4326:", e)

    # preparar dataframe para exportar (copiar atributos)
    df = gdf.drop(columns=[gdf.geometry.name]).copy()

    # incluir geometria conforme opção
    geom_mode = args.geom
    if geom_mode == "wkt":
        # adicionar coluna 'geometry' como WKT
        df["geometry"] = gdf.geometry.to_wkt()
    elif geom_mode == "centroid":
        centroids = gdf.geometry.centroid
        # adiciona coluna 'centroid_x' e 'centroid_y' ou 'centroid'?
        df["centroid_x"] = centroids.x
        df["centroid_y"] = centroids.y
    elif geom_mode == "x_y":
        # cria duas colunas x,y do ponto representativo (centroid)
        centroids = gdf.geometry.representative_point()  # representative_point é mais robusto que centroid em alguns casos
        df["x"] = centroids.x
        df["y"] = centroids.y
    elif geom_mode == "none":
        pass

    # tenta converter colunas com listas/dicts para string para evitar erros no CSV
    for col in df.columns:
        if df[col].apply(lambda v: isinstance(v, (list, dict))).any():
            df[col] = df[col].apply(lambda v: str(v) if v is not None else "")

    # salva CSV
    df.to_csv(out_path, index=False, encoding=args.encoding)
    print(f"Salvo: {out_path}  (linhas: {len(df)})")

if __name__ == "__main__":
    main()
