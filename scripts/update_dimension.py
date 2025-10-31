#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update single dimension in an existing scenario GeoPackage and recompute cs_ish.

Usage examples:
  # Replace the 'ire_cs_inu' column using CSV and overwrite the same gpkg (backup made)
  python scripts/update_dimension.py \
    --gpkg ./cnr_2020/output/ish_cnr_2020.gpkg \
    --layer regiao_completa \
    --csv ./cnr_2020/input/dim_inu_cnr_2020.csv \
    --csv-id cobacia \
    --csv-dim ire_cs_inu

  # If you omit --csv-dim, script tries to auto-detect a column in the CSV that contains "inu" or starts with "ire_cs"
  python scripts/update_dimension.py --gpkg ish_cnr_2020.gpkg --csv dim_inu_cnr_2020.csv

Options:
  --gpkg            path to scenario gpkg (required)
  --csv             path to csv with the new dimension (required)
  --csv-id          id column name in csv (default tries 'cobacia' then 'COBACIA')
  --csv-dim         column name in csv with dimension values (if omitted, auto-detect)
  --id-field        id field name in gpkg layer (default auto detect 'cobacia' variants)
  --layer           layer in gpkg to update (default: 'regiao_completa')
  --out             output gpkg (if omitted, overwrite original after creating a backup)
  --backup-dir      where to write backup of original gpkg (default same folder ./backup_update/)
  --dry-run         only show what would be done (no writes)
  --dim-prefix      prefix used to find all dimension columns (default: 'ire_cs_')
  --cs-col          name of the final ish column to compute (default: 'cs_ish')
  --keep-zero       treat zeros as valid values in averaging (default: ignore zeros)
  --verbose         more printing
"""
import argparse
import os
import shutil
import sys
import tempfile
from datetime import datetime

import geopandas as gpd
import pandas as pd
import fiona

# ---------- Utility functions ----------

def normalize_key_series(s):
    """Return series of strings usable for robust join/comparison.
       Numeric -> int -> str; strings -> stripped lower.
    """
    if pd.api.types.is_numeric_dtype(s):
        # convert floats like 7796133.0 -> int -> str
        def tostr(x):
            try:
                if pd.isna(x):
                    return ""
                xi = int(x)
                return str(xi)
            except Exception:
                return str(x)
        return s.map(tostr).astype(str)
    else:
        # convert to str and strip whitespace
        return s.fillna("").astype(str).str.strip()

def find_best_id_field(gdf, csv_df, prefer=None):
    """Try to find matching id field between gdf and csv_df.
       prefer: user-provided id-field name to try first.
       Returns (gdf_id_field_name, csv_id_field_name)
    """
    g_candidates = [prefer] if prefer else []
    g_candidates += ["cobacia", "COBACIA"]
    g_candidates += list(gdf.columns)
    csv_candidates = ["cobacia", "COBACIA"]
    csv_candidates += list(csv_df.columns)

    # normalize names lowercase for matching
    g_set = {c.lower(): c for c in g_candidates if c}
    csv_set = {c.lower(): c for c in csv_candidates if c}

    # intersection by name
    for name_low in ["cobacia", "ace_cd"]:
        if name_low in g_set and name_low in csv_set:
            return g_set[name_low], csv_set[name_low]

    # otherwise try default guesses
    for name_low, name in g_set.items():
        if name_low in csv_set:
            return name, csv_set[name_low]

    # as last resort, pick first numeric-like column in gdf and csv
    def numeric_like(cols, df):
        for c in cols:
            if pd.api.types.is_numeric_dtype(df[c]):
                return c
        return None

    gnum = numeric_like(list(gdf.columns), gdf)
    csnum = numeric_like(list(csv_df.columns), csv_df)
    if gnum and csnum:
        return gnum, csnum

    # fallback to first column in both (not ideal)
    return list(gdf.columns)[0], list(csv_df.columns)[0]

def detect_dimension_column(csv_df, hint=None):
    """Try to detect the dimension column in CSV automatically.
       Prioritizes columns containing 'ire_cs' or the hint string.
    """
    cols = list(csv_df.columns)
    # direct hits
    for c in cols:
        cl = c.lower()
        if "ire_cs" in cl:
            return c
    # hint checking (e.g., 'inu' for inundacao)
    if hint:
        for c in cols:
            if hint.lower() in c.lower():
                return c
    # fallback: if CSV has only two columns, assume the second is dimension
    if len(cols) == 2:
        return cols[1]
    # otherwise None
    return None

def compute_cs_ish(gdf, dim_prefix="ire_cs_", out_col="cs_ish", keep_zero=False, verbose=False):
    """
    Compute cs_ish as mean of all columns that start with dim_prefix,
    considering only values > 0 (unless keep_zero True).
    The function returns the new series.
    """
    dim_cols = [c for c in gdf.columns if c.startswith(dim_prefix)]
    if verbose:
        print("Detected dimension columns for averaging:", dim_cols)
    if not dim_cols:
        # no dimension columns found -> create NaN series
        return pd.Series([pd.NA] * len(gdf), index=gdf.index)

    # convert to numeric
    df_vals = gdf[dim_cols].apply(pd.to_numeric, errors="coerce")
    if keep_zero:
        mask = ~df_vals.isna()
    else:
        mask = df_vals > 0

    # compute mean across columns where mask True
    def row_mean(row_vals, row_mask):
        valid = row_vals[row_mask]
        if len(valid) == 0:
            return pd.NA
        return float(valid.mean())

    means = []
    for idx in df_vals.index:
        row_vals = df_vals.loc[idx]
        row_mask = mask.loc[idx]
        mv = row_mean(row_vals, row_mask)
        means.append(mv)
    return pd.Series(means, index=gdf.index, name=out_col)

# ---------- Main workflow ----------

def main(argv=None):
    p = argparse.ArgumentParser(description="Update a single dimension in a scenario GPKG and recompute cs_ish")
    p.add_argument("--gpkg", required=True, help="Path to scenario GeoPackage (input, will be overwritten unless --out specified)")
    p.add_argument("--csv", required=True, help="CSV with new dimension values (must contain id column and dimension column)")
    p.add_argument("--csv-id", default=None, help="ID column name in CSV (default tries cobacia/COBACIA or auto-detect)")
    p.add_argument("--csv-dim", default=None, help="Dimension column name in CSV (e.g. ire_cs_inu). If omitted auto-detect.")
    p.add_argument("--id-field", default=None, help="ID field name in gpkg layer (auto-detect if omitted)")
    p.add_argument("--layer", default="regiao_completa", help="Layer in gpkg to update (default regiao_completa)")
    p.add_argument("--out", default=None, help="Output gpkg path; if omitted, original gpkg will be replaced (backup created)")
    p.add_argument("--backup-dir", default=None, help="Where to store backup of original gpkg (default ./backup_update/ in gpkg folder)")
    p.add_argument("--dry-run", action="store_true", help="Do not write any file; just print planned operations")
    p.add_argument("--dim-prefix", default="ire_cs_", help="Prefix to detect dimension columns (default ire_cs_)")
    p.add_argument("--cs-col", default="cs_ish", help="Result column name for computed ish (default cs_ish)")
    p.add_argument("--keep-zero", action="store_true", help="Treat zeros as valid for averaging (default ignore zeros)")
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    args = p.parse_args(argv)

    gpkg_in = args.gpkg
    csv_path = args.csv
    layer = args.layer
    out_gpkg = args.out
    backup_dir = args.backup_dir
    dry_run = args.dry_run
    verbose = args.verbose

    if not os.path.exists(gpkg_in):
        print("Error: gpkg not found:", gpkg_in)
        sys.exit(1)
    if not os.path.exists(csv_path):
        print("Error: csv not found:", csv_path)
        sys.exit(1)

    # read csv
    if verbose:
        print("Reading CSV:", csv_path)
    # try to read with default comma sep; allow semicolon if needed
    try:
        csv_df = pd.read_csv(csv_path)
    except Exception:
        # try semicolon
        csv_df = pd.read_csv(csv_path, sep=";")

    # detect csv-dim if needed
    csv_dim = args.csv_dim
    if csv_dim is None:
        # hint by filename: try 'inu' or other token
        hint = None
        bn = os.path.basename(csv_path).lower()
        for token in ["inu", "inund", "res", "hum", "eco", "amb", "inu"]:
            if token in bn:
                hint = token
                break
        csv_dim = detect_dimension_column(csv_df, hint=hint)
        if verbose:
            print("Auto-detected csv-dim:", csv_dim)
        if csv_dim is None:
            print("Could not auto-detect the dimension column in CSV. Please provide --csv-dim")
            print("CSV columns:", list(csv_df.columns))
            sys.exit(1)
    else:
        if csv_dim not in csv_df.columns:
            print(f"CSV does not contain requested column '{csv_dim}'. Available columns:", list(csv_df.columns))
            sys.exit(1)

    # open target layer from gpkg
    if verbose:
        print("Listing layers in gpkg:", gpkg_in)
    layers = fiona.listlayers(gpkg_in)
    if verbose:
        print("Layers found:", layers)
    if layer not in layers:
        print(f"Layer '{layer}' not found in {gpkg_in}. Available layers: {layers}")
        sys.exit(1)

    # read target layer into gdf
    if verbose:
        print(f"Reading layer '{layer}' from {gpkg_in} ...")
    gdf = gpd.read_file(gpkg_in, layer=layer)

    # detect id field names
    g_id_field, csv_id_field = find_best_id_field(gdf, csv_df, prefer=args.id_field or args.csv_id)
    if verbose:
        print("Using id fields -> gpkg layer:", g_id_field, ", csv:", csv_id_field)
    # normalize keys
    key_g = normalize_key_series(gdf[g_id_field])
    key_csv = normalize_key_series(csv_df[csv_id_field])

    # prepare CSV subset with only id and new dim
    csv_sub = csv_df[[csv_id_field, csv_dim]].copy()
    csv_sub = csv_sub.assign(_key=key_csv)

    # merge: create mapping dict from key->_value
    mapping = {}
    for _, row in csv_sub.iterrows():
        k = str(row["_key"])
        mapping[k] = row[csv_dim]

    # create key column in gdf
    gdf = gdf.copy()
    gdf["_key"] = key_g

    # if dimension column exists in gdf, keep a backup column
    if csv_dim in gdf.columns:
        gdf[f"{csv_dim}_orig_backup"] = gdf[csv_dim]

    # apply mapping: only replace where key found and value not null
    replaced = 0
    for idx in gdf.index:
        k = str(gdf.at[idx, "_key"])
        if k and k in mapping:
            newval = mapping[k]
            # attempt numeric conversion
            try:
                newval_num = pd.to_numeric(newval, errors="coerce")
                gdf.at[idx, csv_dim] = newval_num
            except Exception:
                gdf.at[idx, csv_dim] = newval
            replaced += 1

    if verbose:
        print(f"Replaced/updated {replaced} features with new '{csv_dim}' values out of {len(gdf)} features.")

    # compute cs_ish
    cs_series = compute_cs_ish(gdf, dim_prefix=args.dim_prefix, out_col=args.cs_col, keep_zero=args.keep_zero, verbose=verbose)
    gdf[args.cs_col] = cs_series

    # drop _key helper
    gdf = gdf.drop(columns=["_key"], errors="ignore")

    # decide output path
    if out_gpkg is None:
        # overwrite original: create backup first
        orig_dir = os.path.dirname(os.path.abspath(gpkg_in))
        if backup_dir is None:
            backup_dir = os.path.join(orig_dir, "backup_update")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"{os.path.basename(gpkg_in)}.backup.{timestamp}")
        print("Backing up original gpkg to:", backup_path)
        if not dry_run:
            shutil.copy2(gpkg_in, backup_path)
        out_gpkg = gpkg_in + ".tmp.gpkg"
    else:
        # writing to a new gpkg path
        out_gpkg = os.path.abspath(out_gpkg)

    # write all layers to a new gpkg, replacing the target layer with updated gdf
    if verbose:
        print("Writing layers to new gpkg:", out_gpkg)

    if dry_run:
        print("Dry-run: no files will be written. Exiting.")
        return 0

    # remove temp file if exist
    if os.path.exists(out_gpkg):
        os.remove(out_gpkg)

    # iterate through original layers, writing them to out_gpkg (replacing 'layer')
    first_written = False
    for lyr in layers:
        if lyr == layer:
            to_write = gdf
        else:
            to_write = gpd.read_file(gpkg_in, layer=lyr)

        # write layer to out_gpkg
        if not first_written:
            # first write creates file
            to_write.to_file(out_gpkg, layer=lyr, driver="GPKG")
            first_written = True
        else:
            # subsequent writes append layer
            # geopandas supports writing new layer to existing gpkg by specifying layer argument
            to_write.to_file(out_gpkg, layer=lyr, driver="GPKG")

        if verbose:
            print("Written layer:", lyr)

    # if we used a temp path equal to gpkg_in + '.tmp.gpkg', then replace original
    if os.path.abspath(out_gpkg) == os.path.abspath(gpkg_in) + ".tmp.gpkg":
        final_path = gpkg_in
        # atomic replace
        print("Replacing original gpkg with updated one:", final_path)
        shutil.move(out_gpkg, final_path)
        print("Update complete. Original backed up at:", backup_path)
    else:
        print("Updated gpkg written to:", out_gpkg)
        if os.path.exists(gpkg_in):
            print("Original remains at:", gpkg_in)

    return 0

if __name__ == "__main__":
    sys.exit(main())

