#!/usr/bin/env python3
"""
scripts/plot_bho.py

Plota a camada BHO (ex.: 'bho_area') de um GeoPackage e salva um PNG.
Também expõe a função plot_bho_gpkg(...) para ser chamada por outros scripts (ex.: joinISH.py).

Uso (CLI):
 python -m scripts.plot_bho /caminho/para/BHO_area.gpkg --layer bho_area --output bho_plot.png

Exemplo dentro do joinISH.py:
 from scripts.plot_bho import plot_bho_gpkg
 plot_bho_gpkg("/full/path/to/cnr_atlas2035/middle/BHO_area.gpkg", layer="bho_area", output_png="/tmp/bho.png", show=False)
"""
import os
import argparse
import geopandas as gpd
import matplotlib.pyplot as plt

def _ensure_projected_for_area(gdf):
    """
    Retorna uma cópia projetada apropriada para cálculo de área.
    Prefere EPSG:3857 se gdf não estiver projetado.
    """
    if gdf.crs is None:
        raise ValueError("A camada não possui CRS definido.")
    if gdf.crs.is_projected:
        return gdf.to_crs(gdf.crs)  # já projetado
    else:
        return gdf.to_crs(epsg=3857)  # mercator como fallback para medir áreas

def plot_bho_gpkg(bho_gpkg_path,
                  layer="bho_area",
                  output_png=None,
                  compute_area_km2=False,
                  show=False,
                  figsize=(10, 10),
                  linewidth=0.6,
                  edgecolor="black",
                  facecolor="none",
                  cmap="viridis"):
    """
    Lê BHO (GeoPackage) e plota.
    - bho_gpkg_path: caminho para .gpkg contendo a camada BHO
    - layer: nome da camada dentro do gpkg (default 'bho_area')
    - output_png: caminho para salvar o PNG (se None salva bho_plot.png no mesmo diretório do gpkg)
    - compute_area_km2: se True, cria coluna 'area_km2' e colore polígonos por área
    - show: se True, chama plt.show()
    """
    if not os.path.exists(bho_gpkg_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {bho_gpkg_path}")

    # carrega camada
    print(f"Carregando {bho_gpkg_path} (layer={layer}) ...")
    gdf = gpd.read_file(bho_gpkg_path, layer=layer)
    if gdf.empty:
        raise ValueError("GeoDataFrame carregado está vazio.")

    # opcional: calcula área (em km2) projetando para CRS apropriado
    if compute_area_km2:
        gdf_area = _ensure_projected_for_area(gdf)
        gdf["area_km2"] = gdf_area.geometry.area / 1e6

    # Decide coluna de cor
    column = "area_km2" if compute_area_km2 and "area_km2" in gdf.columns else None

    # plot
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    if column:
        gdf.plot(ax=ax, column=column, cmap=cmap, edgecolor=edgecolor, linewidth=linewidth, legend=True)
        ax.set_title(f"{os.path.basename(bho_gpkg_path)} — {layer} (área km²)")
    else:
        gdf.plot(ax=ax, facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth)
        ax.set_title(f"{os.path.basename(bho_gpkg_path)} — {layer}")

    ax.set_axis_off()

    # output path default
    if output_png is None:
        outdir = os.path.dirname(os.path.abspath(bho_gpkg_path))
        output_png = os.path.join(outdir, "bho_plot.png")

    # salva figura
    fig.tight_layout()
    fig.savefig(output_png, dpi=300)
    print("Plot salvo em:", output_png)

    if show:
        plt.show()
    plt.close(fig)

    return output_png


# ---- CLI ----
def cli():
    parser = argparse.ArgumentParser(description="Plota BHO_area de um GeoPackage")
    parser.add_argument("bho_gpkg", help="Caminho para o GeoPackage contendo a camada BHO")
    parser.add_argument("--layer", default="bho_area", help="Nome da camada dentro do gpkg (padrão: bho_area)")
    parser.add_argument("--output", default=None, help="PNG de saída (se omitido salva bho_plot.png na pasta do gpkg)")
    parser.add_argument("--area", action="store_true", dest="compute_area", help="Calcular e colorir por área (km²)")
    parser.add_argument("--show", action="store_true", help="Mostrar a figura após salvar")
    args = parser.parse_args()

    plot_bho_gpkg(args.bho_gpkg, layer=args.layer, output_png=args.output, compute_area_km2=args.compute_area, show=args.show)

if __name__ == "__main__":
    cli()
