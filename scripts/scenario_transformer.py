#!/usr/bin/env python3
"""
scripts/scenario_transformer.py

MVP engine para aplicar transformações declarativas em CSVs de dimensão:
- actions suportadas: add, multiply, set
- conditions suportadas: between, gt, lt, equals, any
- suporta target via 'path' ou 'target_glob' na regra
- dry_run: quando True, não grava arquivos; retorna manifesto
- gera manifest dict que contém mapping original -> modified (absolute paths)
"""

from pathlib import Path
import os
import glob
import hashlib
import json
import time
import subprocess
from datetime import datetime

import pandas as pd
import numpy as np
import yaml


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _to_numeric_series(ser: pd.Series) -> pd.Series:
    # preserve original formatting but convert comma decimal separators
    s = ser.astype(str).str.replace(",", ".").replace("None", np.nan)
    return pd.to_numeric(s, errors="coerce")


def get_mask(df: pd.DataFrame, condition: dict) -> pd.Series:
    """
    Returns boolean mask for df rows according to condition dict.
    condition types supported:
      - between: {"type":"between","min":x,"max":y}
      - gt: {"type":"gt","value":x}
      - lt: {"type":"lt","value":x}
      - equals: {"type":"equals","value":x}
      - any: {"type":"any"}  -> True for all rows (non-NaN or even NaN? we'll treat as True for non-NaN)
    """
    if not condition or condition.get("type") == "any":
        # apply to all rows
        return pd.Series([True] * len(df), index=df.index)

    typ = condition.get("type")
    # the caller should ensure column conversion; we pass column value series into this function
    # But we will accept condition with either numeric or string.
    # We will expect the caller to pass the relevant series through conversion before using mask.
    # To keep API simple, condition just uses numeric comparisons applied to df (should be numeric column)
    # For generality, return mask False if column missing - handled upstream
    raise ValueError("get_mask should be called with a pre-bound column series in this implementation.")


def _build_mask_from_series(series: pd.Series, condition: dict) -> pd.Series:
    """
    Generate boolean mask for a numeric series based on the condition.
    """
    if condition is None or condition.get("type") == "any":
        return pd.Series([True] * len(series), index=series.index)

    typ = condition.get("type")
    if typ == "between":
        lo = float(condition.get("min", -np.inf))
        hi = float(condition.get("max", np.inf))
        return (series >= lo) & (series <= hi)
    if typ == "gt":
        v = float(condition["value"])
        return series > v
    if typ == "lt":
        v = float(condition["value"])
        return series < v
    if typ == "equals":
        v = float(condition["value"])
        return series == v
    # unknown -> none matched
    return pd.Series([False] * len(series), index=series.index)


def apply_action_to_series(series: pd.Series, action: dict, mask: pd.Series) -> (pd.Series, int):
    """
    Apply action (add/multiply/set) to the numeric series (pd.Series) under mask (boolean Series).
    Returns (new_series, modified_count)
    """
    a_type = action.get("type")
    before = series.copy().astype(float)
    new = series.copy().astype(float)

    if a_type == "add":
        val = float(action.get("value", 0.0))
        new.loc[mask] = new.loc[mask] + val
    elif a_type == "multiply":
        factor = float(action.get("factor", 1.0))
        new.loc[mask] = new.loc[mask] * factor
    elif a_type == "set":
        val = action.get("value")
        # support numeric set
        new.loc[mask] = float(val) if val is not None else np.nan
    else:
        raise ValueError(f"Unsupported action type: {a_type}")

    # count modified: use numpy isclose with equal_nan=True
    try:
        before_vals = before.values
        after_vals = new.values
        # both are float arrays now
        changed = ~np.isclose(before_vals, after_vals, equal_nan=True)
        modified_count = int(np.sum(changed))
    except Exception:
        # fallback to simple not-equal counting
        modified_count = int((before != new).sum())

    return pd.Series(new, index=series.index), modified_count


def _resolve_targets_from_rule(rule: dict, yaml_dir: str) -> list:
    """
    Given a rule dict, return a list of matching file paths (absolute).
    rule may include:
      - 'path' (single file)
      - 'target' (alternative for path)
      - 'target_glob' (glob pattern)
      - 'file_glob' (alias)
    yaml_dir is used to resolve relative paths.
    """
    res = []
    def abs_path(p):
        p = str(p)
        pth = Path(p)
        if not pth.is_absolute():
            pth = Path(yaml_dir) / pth
        return str(pth.resolve())

    if rule.get("path"):
        t = abs_path(rule["path"])
        if os.path.exists(t):
            res.append(t)
    if rule.get("target"):
        t = abs_path(rule["target"])
        if os.path.exists(t):
            res.append(t)
    if rule.get("target_glob"):
        pat = str(Path(yaml_dir) / rule["target_glob"]) if not Path(rule["target_glob"]).is_absolute() else rule["target_glob"]
        matches = glob.glob(pat)
        res.extend([str(Path(x).resolve()) for x in matches])
    if rule.get("file_glob"):
        pat = str(Path(yaml_dir) / rule["file_glob"]) if not Path(rule["file_glob"]).is_absolute() else rule["file_glob"]
        matches = glob.glob(pat)
        res.extend([str(Path(x).resolve()) for x in matches])
    # dedupe
    return sorted(list(dict.fromkeys(res)))


def apply_declarative_rule_to_file(file_path: str, rule: dict, out_folder: str, dry_run: bool = False) -> dict:
    """
    Apply a single declarative rule to a single CSV file.
    Returns dict: { "file": original_abs, "out": out_abs (intended), "modified": int, "orig_sha256": str }
    """
    file_path = str(Path(file_path).resolve())
    out_folder = str(Path(out_folder).resolve())
    Path(out_folder).mkdir(parents=True, exist_ok=True)

    # read CSV robustly
    try:
        df = pd.read_csv(file_path, sep=None, engine="python", dtype=str)
    except Exception:
        # fallback simpler read
        df = pd.read_csv(file_path, sep=",", dtype=str)

    # target column
    col = rule.get("column")
    if col not in df.columns:
        # no such column -> nothing to do (report 0)
        return {"file": file_path, "out": None, "modified": 0, "orig_sha256": sha256_file(file_path), "note": f"column {col} not found"}

    # convert column to numeric
    series_orig = _to_numeric_series(df[col])
    # build mask
    cond = rule.get("condition", None)
    mask = _build_mask_from_series(series_orig, cond)

    # apply action
    action = rule.get("action", {})
    new_series, modified_count = apply_action_to_series(series_orig.fillna(np.nan), action, mask)

    # assign back (preserve original formatting of other columns)
    df_out = df.copy()
    # write numeric with same decimal separator '.'; we won't try to preserve comma format
    df_out[col] = new_series

    out_filename = Path(file_path).name
    out_path = os.path.join(out_folder, out_filename)

    if not dry_run:
        # write out CSV
        df_out.to_csv(out_path, index=False)
    else:
        # create parent folder if not exists but do not write file
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    return {
        "file": file_path,
        "out": str(Path(out_path).resolve()),
        "modified": int(modified_count),
        "orig_sha256": sha256_file(file_path)
    }


def apply_transformations(scenario_yaml_path: str, out_folder: str = None, dry_run: bool = False) -> dict:
    """
    Main entry.
    - scenario_yaml_path: path to YAML file (used to resolve relative targets)
    - out_folder: where modified CSVs are stored (default: same directory + middle/modified_csvs)
    - dry_run: if True, do not write files (but manifest will describe intended outputs)
    Returns manifest dict with keys:
      - scenario_id, timestamp, git_commit, rules_applied (list), file_map {orig_abs: modified_abs}
    """
    yaml_path = Path(scenario_yaml_path).resolve()
    yaml_dir = str(yaml_path.parent)
    with open(yaml_path, "r", encoding="utf-8") as f:
        scenario = yaml.safe_load(f)

    if out_folder is None:
        # default to scenario parent / middle / modified_csvs
        out_folder = os.path.join(yaml_dir, "middle", "modified_csvs")
    Path(out_folder).mkdir(parents=True, exist_ok=True)

    manifest = {
        "scenario_file": str(yaml_path),
        "scenario_id": scenario.get("id"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "git_commit": None,
        "rules_applied": [],
        "file_map": {}
    }

    # try to capture git commit
    try:
        git_out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=str(Path.cwd()))
        if git_out.returncode == 0:
            manifest["git_commit"] = git_out.stdout.strip()
    except Exception:
        manifest["git_commit"] = None

    rules = scenario.get("transformations", []) or scenario.get("rules", [])
    for r in rules:
        rid = r.get("id", None)
        # declarative rules only in MVP
        if "sql" in r:
            # skip SQL-like in MVP
            manifest["rules_applied"].append({"id": rid, "note": "sql rules not supported in MVP", "skipped": True})
            continue

        # resolve targets
        targets = _resolve_targets_from_rule(r, yaml_dir)
        if not targets:
            manifest["rules_applied"].append({"id": rid, "note": "no target files matched", "skipped": True})
            continue

        for t in targets:
            res = apply_declarative_rule_to_file(t, r, out_folder, dry_run=dry_run)
            manifest["rules_applied"].append({"id": rid, "file": res.get("file"), "out": res.get("out"), "modified": res.get("modified"), "note": res.get("note", "")})
            # populate file_map
            manifest["file_map"][str(Path(res.get("file")).resolve())] = str(Path(res.get("out")).resolve())

    # write manifest to out_folder
    manifest_path = os.path.join(out_folder, "manifest.json")
    try:
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # print summary
    total_mods = sum([r.get("modified", 0) for r in manifest["rules_applied"] if isinstance(r.get("modified", None), (int, float))])
    print(f"[scenario_transformer] rules: {len(rules)} -> files modified (total rows changed): {total_mods}  (dry_run={dry_run})")
    return manifest
