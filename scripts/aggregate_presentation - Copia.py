#!/usr/bin/env python3
"""
Updated aggregate_presentation.py

Now supports requesting multiple aggregation types in one run (e.g. --agg mean median),
or using "--agg all" to compute all supported aggregations.

Instead of writing one layer per aggregation, this version writes a single layer named
agg_<presentation_basename> (e.g. agg_mun_es) containing one column per aggregation:
 - cs_ish_mean
 - cs_ish_median
 - cs_ish_max
 - cs_ish_min

The script still defaults to writing into the same output GPKG produced by joinISH
(e.g. ./cnr_<cenario>/output/ish_cnr_<cenario>.gpkg).

Usage examples:
  python -m scripts.aggregate_presentation atlas_2035 ./apresentacao/mun_es.gpkg --id-field fid --agg mean median
  python -m scripts.aggregate_presentation atlas_2035 ./apresentacao/mun_es.gpkg --agg all
"""
import os
import argparse
import geopandas as gpd
import numpy as np
import fiona
from shapely.ops import unary_union

SUPPORTED_AGGS = ("mean", "median", "max", "min")

def _get_local_utm_crs(gdf):
    if gdf.crs is None:
        raise ValueError("Input GeoDataFrame has no CRS.")
    gdf4326 = gdf.to_crs(epsg=4326)
    centroid = gdf4326.unary_union.centroid
    lon = centroid.x
    lat = centroid.y
    zone = int((lon + 180) / 6) + 1
    south = lat < 0
    proj4 = f"+proj=utm +zone={zone} +datum=WGS84 +units=m +no_defs"
    if south:
        proj4 += " +south"
    return proj4

def _weighted_median(values, weights):
    if len(values) == 0:
        return np.nan
    mask = ~np.isnan(values)
    values = values[mask]
    weights = weights[mask]
    if len(values) == 0:
        return np.nan
    weights = np.array(weights, dtype=float)
    if weights.sum() == 0:
        return float(np.nanmedian(values))
    sorter = np.argsort(values)
    values_sorted = values[sorter]
    weights_sorted = weights[sorter]
    cumsum = np.cumsum(weights_sorted)
    cutoff = weights_sorted.sum() / 2.0
    idx = np.searchsorted(cumsum, cutoff)
    return float(values_sorted[min(idx, len(values_sorted)-1)])

def _safe_write_layer_to_gpkg(gpkg_path, layer_name, gdf_to_write):
    gpkg_path = os.path.abspath(gpkg_path)
    if not os.path.exists(gpkg_path):
        gdf_to_write.to_file(gpkg_path, layer=layer_name, driver="GPKG")
        return

    layers = fiona.listlayers(gpkg_path)
    if layer_name not in layers:
        gdf_to_write.to_file(gpkg_path, layer=layer_name, driver="GPKG")
        return

    temp_path = gpkg_path + ".tmp.gpkg"
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass

    for lyr in layers:
        if lyr == layer_name:
            continue
        gdf = gpd.read_file(gpkg_path, layer=lyr)
        if not os.path.exists(temp_path):
            gdf.to_file(temp_path, layer=lyr, driver="GPKG")
        else:
            gdf.to_file(temp_path, layer=lyr, driver="GPKG", mode="a")

    if not os.path.exists(temp_path):
        gdf_to_write.to_file(temp_path, layer=layer_name, driver="GPKG")
    else:
        gdf_to_write.to_file(temp_path, layer=layer_name, driver="GPKG", mode="a")

    os.replace(temp_path, gpkg_path)

def aggregate_presentation_gpkg(input_gpkg,
                                input_layer="regiao_completa",
                                presentation_gpkg=None,
                                presentation_layer=None,
                                id_field="id_apresent",
                                aggs=("mean",),
                                output_gpkg=None,
                                verbose=True):
    """
    aggs: iterable of aggregation names (subset of SUPPORTED_AGGS) or ('mean',) by default.
    """
    if presentation_gpkg is None:
        raise ValueError("presentation_gpkg must be provided.")
    # normalize aggs
    if isinstance(aggs, str):
        aggs = (aggs,)
    aggs = list(aggs)
    if "all" in aggs:
        aggs = list(SUPPORTED_AGGS)
    # validate
    for a in aggs:
        if a not in SUPPORTED_AGGS:
            raise ValueError(f"Unsupported aggregation '{a}'. Supported: {SUPPORTED_AGGS} or 'all'.")

    if output_gpkg is None:
        output_gpkg = input_gpkg

    if verbose:
        print("Loading input GPKG:", input_gpkg, "layer:", input_layer)
    gdf_input = gpd.read_file(input_gpkg, layer=input_layer)
    if "cs_ish" not in gdf_input.columns:
        raise ValueError("Input layer does not contain 'cs_ish' column.")

    # load presentation
    if presentation_layer is None:
        layers = fiona.listlayers(presentation_gpkg)
        if not layers:
            raise ValueError("No layers found in presentation_gpkg: " + str(presentation_gpkg))
        presentation_layer = layers[0]
    if verbose:
        print("Loading presentation:", presentation_gpkg, "layer:", presentation_layer)
    gdf_pres = gpd.read_file(presentation_gpkg, layer=presentation_layer)

    if id_field not in gdf_pres.columns:
        raise ValueError(f"id_field '{id_field}' not found in presentation layer columns: {gdf_pres.columns.tolist()}")

    # reproject presentation to input CRS if needed
    if gdf_input.crs != gdf_pres.crs:
        if verbose:
            print("Reprojecting presentation layer to input CRS:", gdf_input.crs)
        gdf_pres = gdf_pres.to_crs(gdf_input.crs)

    # choose projected CRS for area calc
    try:
        project_crs = _get_local_utm_crs(gdf_pres)
        if verbose:
            print("Using local projected CRS for area calculations:", project_crs)
    except Exception:
        if gdf_input.crs.is_projected:
            project_crs = gdf_input.crs
            if verbose:
                print("Fallback: using input CRS for area calc:", project_crs)
        else:
            project_crs = "EPSG:3857"
            if verbose:
                print("Fallback: using EPSG:3857 for area calc")

    gdf_input_p = gdf_input.to_crs(project_crs)
    gdf_pres_p = gdf_pres.to_crs(project_crs)

    # compute presentation area
    gdf_pres_p["area_apresent_km2"] = gdf_pres_p.geometry.area / 1e6

    if verbose:
        print("Computing intersections (this may take time)...")
    inter = gpd.overlay(gdf_pres_p, gdf_input_p[["cobacia", "cs_ish", "geometry"]], how="intersection")

    layer_basename = os.path.splitext(os.path.basename(presentation_gpkg))[0]
    out_layer_name = f"agg_{layer_basename}"

    # create result frame (copy of presentation projected)
    result_pres = gdf_pres_p.copy()

    # initialize columns for requested aggs
    for a in aggs:
        colname = f"cs_ish_{a}"
        result_pres[colname] = np.nan

    if inter.empty:
        if verbose:
            print("No intersections found. Writing empty result layer with requested aggregation columns.")
        result_pres_out = result_pres.to_crs(gdf_pres.crs)
        _safe_write_layer_to_gpkg(output_gpkg, out_layer_name, result_pres_out)
        if verbose:
            print("Written layer", out_layer_name, "to", output_gpkg)
        return output_gpkg

    inter["area_inter_km2"] = inter.geometry.area / 1e6

    # ensure area_apresent_km2 present
    if "area_apresent_km2" not in inter.columns:
        inter = inter.merge(gdf_pres_p[[id_field, "area_apresent_km2"]], on=id_field, how="left")

    # Prepare aggregations
    if "mean" in aggs:
        inter["weighted"] = inter["cs_ish"].fillna(0) * (inter["area_inter_km2"] / inter["area_apresent_km2"])
        agg_mean = inter.groupby(id_field, as_index=False).agg({"weighted": "sum"})
        agg_mean = agg_mean.rename(columns={"weighted": "cs_ish_mean"})
        result_pres = result_pres.merge(agg_mean, on=id_field, how="left")

    if "median" in aggs:
        records = []
        for key, grp in inter.groupby(id_field):
            vals = grp["cs_ish"].to_numpy(dtype=float)
            w = grp["area_inter_km2"].to_numpy(dtype=float)
            med = _weighted_median(vals, w)
            records.append({id_field: key, "cs_ish_median": med})
        if records:
            agg_med = gpd.GeoDataFrame(records)
            result_pres = result_pres.merge(agg_med, on=id_field, how="left")
        else:
            result_pres["cs_ish_median"] = np.nan

    if "max" in aggs:
        agg_max = inter.groupby(id_field, as_index=False).agg({"cs_ish": "max"})
        agg_max = agg_max.rename(columns={"cs_ish": "cs_ish_max"})
        result_pres = result_pres.merge(agg_max, on=id_field, how="left")

    if "min" in aggs:
        agg_min = inter.groupby(id_field, as_index=False).agg({"cs_ish": "min"})
        agg_min = agg_min.rename(columns={"cs_ish": "cs_ish_min"})
        result_pres = result_pres.merge(agg_min, on=id_field, how="left")

    # ensure all columns exist in result_pres (fill missing with NaN)
    for a in aggs:
        colname = f"cs_ish_{a}"
        if colname not in result_pres.columns:
            result_pres[colname] = np.nan

    # result_pres currently in projected CRS -> back to original presentation CRS
    result_pres_out = result_pres.to_crs(gdf_pres.crs)

    if verbose:
        print("Writing aggregated layer", out_layer_name, "to", output_gpkg)
    _safe_write_layer_to_gpkg(output_gpkg, out_layer_name, result_pres_out)

    if verbose:
        print("Aggregation complete. Output GPKG:", output_gpkg, "layer:", out_layer_name)
    return output_gpkg

def cli():
    parser = argparse.ArgumentParser(description="Aggregate cs_ish from ottobacias to a presentation layer.")
    parser.add_argument("cenario", help="Cenário (nome) — the script will look for ./cnr_<cenario>/output/ish_cnr_<cenario>.gpkg by default")
    parser.add_argument("presentation_gpkg", help="Path to presentation gpkg (e.g. apresent_municipios.gpkg)")
    parser.add_argument("--presentation-layer", default=None, help="Layer name inside presentation gpkg (defaults to first layer)")
    parser.add_argument("--id-field", default="id_apresent", help="Identifier field in presentation layer (default: id_apresent)")
    parser.add_argument("--input-gpkg", default=None, help="Input gpkg path (default: ./cnr_<cenario>/output/ish_cnr_<cenario>.gpkg)")
    parser.add_argument("--input-layer", default="regiao_completa", help="Input layer (default: regiao_completa)")
    parser.add_argument("--agg", nargs="+", default=["mean"], help="Aggregation types: mean median max min OR 'all' to compute all. Example: --agg mean median")
    args = parser.parse_args()

    if args.input_gpkg is None:
        root = os.getcwd()
        args.input_gpkg = os.path.join(root, f"cnr_{args.cenario}", "output", f"ish_cnr_{args.cenario}.gpkg")

    # normalize agg argument: allow comma-separated single string as well
    if len(args.agg) == 1 and "," in args.agg[0]:
        args.agg = [s.strip() for s in args.agg[0].split(",") if s.strip()]

    # output_gpkg default is same as input_gpkg
    output_folder = os.path.join(os.getcwd(), f"cnr_{args.cenario}", "output")
    os.makedirs(output_folder, exist_ok=True)
    output_gpkg = args.input_gpkg

    aggregate_presentation_gpkg(
        input_gpkg=args.input_gpkg,
        input_layer=args.input_layer,
        presentation_gpkg=args.presentation_gpkg,
        presentation_layer=args.presentation_layer,
        id_field=args.id_field,
        aggs=args.agg,
        output_gpkg=output_gpkg,
        verbose=True
    )

if __name__ == "__main__":
    cli()
