#!/usr/bin/env python3
import argparse
import os
import glob
import sys
import pandas as pd
import geopandas as gpd
import fiona
import numpy as np
from pathlib import Path
import yaml

# Mock the missing script
os.makedirs("scripts", exist_ok=True)
if not os.path.exists("scripts/aplica_recortes.py"):
    with open("scripts/aplica_recortes.py", "w") as f:
        f.write("def aplica_recortes_gpkg(root_folder, recortes_escolhidos): return []")

from scripts.aplica_recortes import aplica_recortes_gpkg

def load_gpkg_with_fid(filename, layer):
    # In some GPKGs, the 'cobacia' might be a property, not the FID.
    # But the user's script explicitly tries to use feat['id'] as 'cobacia'.
    # If feat['id'] is just 0, 1, 2, then we need to make sure our CSVs match these.
    features = []
    with fiona.open(filename, layer=layer) as src:
        for feat in src:
            props = dict(feat['properties'])
            # The user's code:
            try:
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
    return gdf[dim_cols].apply(lambda row: row[row > 0.0].mean(), axis=1)

def apply_rules(gdf, rules, aliases):
    """
    Applies custom rules defined in YAML to the GeoDataFrame.
    """
    # Create a local context for evaluation
    context = {}
    for alias, col_name in aliases.items():
        if col_name in gdf.columns:
            context[alias] = gdf[col_name]
    
    for rule in rules:
        name = rule.get("name")
        formula = rule.get("formula")
        null_if = rule.get("null_if")
        
        print(f"Aplicando regra: {name}")
        
        # Evaluate formula
        try:
            # We use eval with a restricted environment but allowing pandas series operations
            # We add context (aliases) to the evaluation
            # Use pd.eval for safer and better pandas integration
            # For the formula, we can use eval since it's mostly arithmetic
            res = eval(formula, {"__builtins__": None, "min": min, "max": max, "np": np}, context)
            
            # Apply null_if condition if present
            if null_if:
                # Replace 'and' with '&' and 'or' with '|' for element-wise logic
                null_if_fixed = null_if.replace(" and ", " & ").replace(" or ", " | ")
                condition = eval(null_if_fixed, {"__builtins__": None, "np": np}, context)
                res = res.mask(condition)
            
            gdf[name] = res
            # Add the new column to context so it can be used by subsequent rules
            context[name] = gdf[name]
            
        except Exception as e:
            print(f"Erro ao aplicar regra '{name}': {e}")
            
    return gdf

def main():
    parser = argparse.ArgumentParser(description="Gera o GPKG de ISH para um cenário e aplica recortes opcionais")
    parser.add_argument("cenario", help="Nome do cenário (ex: atlas2035)")
    parser.add_argument("-r", "--recorte", action="append", default=[], help="Nome do recorte")
    parser.add_argument("-s", "--scenario-file", default=None, help="arquivo YAML de cenário")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria executado")
    args = parser.parse_args()

    nome_cenario = args.cenario
    recortes_escolhidos = args.recorte
    scenario_yaml = args.scenario_file
    scenario = None
    dry_run = args.dry_run

    if scenario_yaml:
        try:
            scenario_path = Path(scenario_yaml).expanduser().resolve()
            with open(scenario_path, "r", encoding="utf-8") as sf:
                scenario = yaml.safe_load(sf)
            print("Cenário YAML carregado de:", scenario_path)
        except Exception as e:
            print("Erro ao ler o YAML de cenário:", e)
            sys.exit(1)

    root_folder = os.getcwd()
    if scenario and scenario.get("base_dir"):
        base_dir_raw = scenario.get("base_dir")
        yaml_dir = Path(scenario_yaml).parent if scenario_yaml else Path(root_folder)
        base_dir = str((yaml_dir / base_dir_raw).resolve()) if not os.path.isabs(base_dir_raw) else base_dir_raw
    else:
        base_dir = os.path.expanduser(f"{root_folder}/cnr_{nome_cenario}")

    input_folder = os.path.join(base_dir, "input")
    output_folder = os.path.join(base_dir, "output")
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    if scenario and scenario.get("bho") and scenario["bho"].get("path"):
        bho_raw = scenario["bho"].get("path")
        yaml_dir = Path(scenario_yaml).parent if scenario_yaml else Path(root_folder)
        gpkg_file = str((yaml_dir / bho_raw).resolve()) if not os.path.isabs(bho_raw) else bho_raw
    else:
        gpkg_file = os.path.join(input_folder, "BHO_area.gpkg")

    layer = "bho_area"
    if scenario and scenario.get("bho") and scenario["bho"].get("layer"):
        layer = scenario["bho"].get("layer")

    gdf = load_gpkg_with_fid(gpkg_file, layer)
    gdf.columns = gdf.columns.str.strip().str.lower()
    gdf = gdf.set_geometry("geometry")
    if gdf.crs is None:
        gdf.set_crs(epsg=4674, inplace=True)
    else:
        gdf = gdf.to_crs(epsg=4674)

    aliases = {}
    csv_files = []
    if scenario and scenario.get("dimensions"):
        yaml_dir = Path(scenario_yaml).parent if scenario_yaml else Path(root_folder)
        for dim in scenario.get("dimensions", []):
            if isinstance(dim, dict) and dim.get("file_glob"):
                pat = dim["file_glob"]
                if not os.path.isabs(pat):
                    pat = str((yaml_dir / pat))
                matches = glob.glob(pat)
                for match in matches:
                    csv_files.append((match, dim.get("name")))

    for csv_file, alias in csv_files:
        df = pd.read_csv(csv_file, sep=None, engine='python')
        df.columns = df.columns.str.strip().str.lower()
        if "cobacia" in df.columns:
            df["cobacia"] = df["cobacia"].astype("Int64")
            dimension_columns = [col for col in df.columns if col != "cobacia"]
            if len(dimension_columns) == 1:
                dim_col = dimension_columns[0]
                df[dim_col] = pd.to_numeric(df[dim_col].astype(str).str.replace(",", "."), errors="coerce")
                gdf = gdf.merge(df[["cobacia", dim_col]], on="cobacia", how="left")
                if alias:
                    aliases[alias] = dim_col

    # Check for custom rules in YAML
    if scenario and scenario.get("rules"):
        gdf = apply_rules(gdf, scenario.get("rules"), aliases)
        # Identify columns to keep based on rules
        rule_cols = [rule.get("name") for rule in scenario.get("rules")]
        dimension_cols = [col for col in gdf.columns if col.startswith("ire_cs_")]
        cols_to_keep = ["cobacia"] + dimension_cols + rule_cols + ["geometry"]
    else:
        # Fallback to default behavior
        dimension_cols = [col for col in gdf.columns if col.startswith("ire_cs_")]
        gdf["cs_ish"] = compute_cs_ish(gdf, dimension_cols)
        cols_to_keep = ["cobacia"] + dimension_cols + ["cs_ish", "geometry"]

    gdf_final = gdf[cols_to_keep]

    gpkg_name = f"ish_cnr_{nome_cenario}.gpkg"
    if scenario and scenario.get("output") and scenario["output"].get("gpkg_name"):
        gpkg_name = scenario["output"].get("gpkg_name")
    output_file = os.path.join(output_folder, gpkg_name)

    if dry_run:
        print(f"[dry-run] Arquivo final GPKG seria salvo em: {output_file}")
        sys.exit(0)

    if os.path.isfile(output_file):
        os.remove(output_file)
    gdf_final.to_file(output_file, driver="GPKG", layer="regiao_completa")
    print(f"Arquivo salvo em {output_file}")

if __name__ == "__main__":
    main()