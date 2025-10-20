# --- aplica_recortes.py ---

import os
import glob
import geopandas as gpd

def load_all_recortes(root_folder, recorte_args):
    import glob
    from shapely.ops import unary_union
    recortes_dir = os.path.join(root_folder, "recortes")
    if not os.path.isdir(recortes_dir):
        return {}
    if recorte_args:
        arquivos = []
        for nome in recorte_args:
            gpkg_path = os.path.join(recortes_dir, nome + ".gpkg")
            if os.path.isfile(gpkg_path):
                arquivos.append(gpkg_path)
    else:
        return {}
    resultado = {}
    for fp in arquivos:
        rg = gpd.read_file(fp)
        if rg.crs is None:
            rg.set_crs(epsg=4674, inplace=True)
        else:
            rg = rg.to_crs(epsg=4674)
        geom = rg.unary_union
        nome_base = os.path.splitext(os.path.basename(fp))[0]
        resultado[nome_base] = geom
    return resultado

def aplica_recortes_gpkg(gpkg_path, recorte_args):
    """
    Abre o GPKG existente, assume que tem camada 'regiao_completa',
    carrega recortes via load_all_recortes(), e para cada recorte:
    recorta e grava camada no mesmo GPKG.
    """
    if not os.path.isfile(gpkg_path):
        raise FileNotFoundError(f"GPKG não encontrado: {gpkg_path}")

    # 1) lê somente a camada 'regiao_completa'
    gdf_regiao = gpd.read_file(gpkg_path, layer="regiao_completa")

    # 2) pega root_folder como a pasta pai de scripts/
    root_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    recortes_dict = load_all_recortes(root_folder, recorte_args)
    for rec_name, geom_diss in recortes_dict.items():
        gdf_rec = gpd.clip(gdf_regiao, geom_diss)
        # sobrescreve/adiciona camada no mesmo GPKG
        gdf_rec.to_file(gpkg_path, layer=rec_name, driver="GPKG")
    return list(recortes_dict.keys())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Aplica recortes ao GPKG de ISH existente")
    parser.add_argument("cenario", help="Nome do cenário (ex: atlas2035)")
    parser.add_argument("-r", "--recorte", action="append", default=[],
                        help="Nome do recorte (sem .gpkg). Se não passar, aplica todos existentes.")
    args = parser.parse_args()

    nome_cenario = args.cenario
    recortes_escolhidos = args.recorte

    # monta caminho para o GPKG de ish final
    gpkg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                             f"cnr_{nome_cenario}", "output", f"ish_cnr_{nome_cenario}.gpkg")
    gpkg_path = os.path.normpath(gpkg_path)

    try:
        adicionados = aplica_recortes_gpkg(gpkg_path, recortes_escolhidos)
        if adicionados:
            print(f"Recortes aplicados: {', '.join(adicionados)}")
        else:
            print("Nenhum recorte encontrado para aplicar.")
    except Exception as e:
        print("Erro ao aplicar recortes:", e)

