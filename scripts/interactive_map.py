#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interactive_map.py (final)

- Opções:
  --generate {html,png,both}  : qual saída gerar (padrão both)
  --static                    : habilita geração de PNG estático (subplots)
  --static-out                : caminho do PNG de saída
  --static-max-features       : amostrar feições para PNG estático
  --static-no-edges           : camadas para desenhar sem linhas no PNG
  --fields                    : mapeamento layer:fields (ex.: "mun:cs_ish;reg:all")
  --layers                    : camadas a utilizar (vírgula separado)

Colorização: cores do ISH e NO_DATA_COLOR para Null/0.
"""
import os
import sys
import argparse
import json
import webbrowser
import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import geopandas as gpd
import folium
import branca
import fiona

# Paleta e classes
COLORS_ISH = ['#FF5500', '#FFAA00', '#FFFF71', '#169200', '#2986cc']
NO_DATA_COLOR = "#cccccc"
CLASS_THRESHOLDS = [1.5, 2.5, 3.5, 4.5]
CLASS_LABELS = [
    "1.00 - 1.50 (Mínimo)",
    "1.51 - 2.50 (Baixo)",
    "2.51 - 3.50 (Médio)",
    "3.51 - 4.50 (Alto)",
    "4.51 - 5.00 (Máximo)",
]


def find_gpkg_files(root="."):
    root = Path(root)
    return [str(f) for f in root.rglob("*.gpkg")]


def choose_from_list(prompt, options, allow_multiple=True):
    print(prompt)
    for i, opt in enumerate(options, start=1):
        print(f"{i}) {opt}")
    while True:
        choice = input("Escolha número(s) separados por vírgula (ENTER para cancelar): ").strip()
        if choice == "":
            return []
        parts = [p.strip() for p in choice.split(",") if p.strip()]
        try:
            idxs = [int(p) - 1 for p in parts]
            if any(i < 0 or i >= len(options) for i in idxs):
                raise ValueError
            selected = [options[i] for i in idxs]
            return selected if allow_multiple else selected[:1]
        except Exception:
            print("Entrada inválida. Use números separados por vírgula.")


def parse_fields_arg(fields_arg):
    if not fields_arg:
        return {}
    mapping = {}
    parts = [p.strip() for p in fields_arg.split(";") if p.strip()]
    for part in parts:
        if ":" not in part:
            continue
        layer, fields_str = part.split(":", 1)
        fields = [f.strip() for f in fields_str.split(",") if f.strip()]
        if fields:
            mapping[layer.strip()] = fields
    return mapping


def try_parse_float(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        try:
            return float(x)
        except Exception:
            return None
    s = str(x).strip()
    if s == "":
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def get_color_for_value(v):
    """
    Retorna cor para valor ISH.
    NULL/None e zero (0.0) são tratados como sem-dados -> NO_DATA_COLOR.
    Valores < 1.0 (mas > 0) recebem cor cinza claro.
    """
    if v is None:
        return NO_DATA_COLOR
    try:
        vf = float(v)
    except Exception:
        # strings não-numéricas etc.
        return NO_DATA_COLOR
    # tratar NaN / inf como sem-dados
    import math as _math
    if (not _math.isfinite(vf)) or _math.isnan(vf):
        return NO_DATA_COLOR
    # tratar zero como sem-dados
    if vf == 0.0:
        return NO_DATA_COLOR
    if vf < 1.0:
        return "#eeeeee"
    for thresh, color in zip(CLASS_THRESHOLDS, COLORS_ISH):
        if vf <= thresh:
            return color
    return COLORS_ISH[-1]


def add_legend(map_obj, title="Classes ISH"):
    labels_html = ""
    for lbl, col in zip(CLASS_LABELS, COLORS_ISH):
        labels_html += (
            f'<div style="display:flex;align-items:center;margin-bottom:4px;">'
            f'<div style="width:18px;height:14px;background:{col};margin-right:8px;border:1px solid #444;"></div>'
            f'<div style="font-size:12px">{lbl}</div></div>'
        )
    labels_html += (
        f'<div style="display:flex;align-items:center;margin-bottom:4px;">'
        f'<div style="width:18px;height:14px;background:{NO_DATA_COLOR};margin-right:8px;border:1px solid #444;"></div>'
        f'<div style="font-size:12px">Sem dados / zero</div></div>'
    )
    legend_html = f"""
     <div style="position: fixed; 
                 bottom: 50px; left: 10px; width: 260px; height: auto; 
                 z-index:9999; font-size:12px;">
       <div style="background:white;padding:8px;border:1px solid #999;box-shadow:2px 2px 5px rgba(0,0,0,0.3)">
         <div style="font-weight:bold;margin-bottom:6px">{title}</div>
         {labels_html}
       </div>
     </div>
    """
    from branca.element import Element
    el = Element(legend_html)
    map_obj.get_root().html.add_child(el)


def style_function_for_field(field, edgecolor="#444444", weight=0.5, fillOpacity=0.8):
    def style_function(feature):
        props = feature.get("properties", {})
        val = props.get(field)
        color = get_color_for_value(val)
        return {
            "fillColor": color,
            "color": edgecolor,
            "weight": weight,
            "fillOpacity": fillOpacity,
        }
    return style_function


def save_static_maps_from_selection(gpkg_path, gdfs, layer_field_selection, output_path=None,
                                    crs_epsg=4326, dpi=300, max_label_chars=40, no_edge_layers=None):
    if no_edge_layers is None:
        no_edge_layers = []

    items = []
    for lyr_name, gdf in gdfs:
        sel_fields = layer_field_selection.get(lyr_name, [])
        if not sel_fields:
            try:
                gdf_plot = gdf.to_crs(epsg=crs_epsg)
            except Exception:
                gdf_plot = gdf.copy()
            items.append((lyr_name, gdf_plot, None))
        else:
            for fld in sel_fields:
                if fld not in gdf.columns:
                    continue
                gdf_copy = gdf.copy()
                gdf_copy[fld] = gdf_copy[fld].apply(lambda x: try_parse_float(x))
                try:
                    gdf_plot = gdf_copy.to_crs(epsg=crs_epsg)
                except Exception:
                    gdf_plot = gdf_copy
                items.append((f"{lyr_name}__{fld}", gdf_plot, fld))

    n = len(items)
    if n == 0:
        raise ValueError("Nenhum item para plotar.")

    if n <= 3:
        rows = 1
    elif n == 4:
        rows = 2
    else:
        rows = math.ceil(n / 3)

    base = n // rows
    rem = n % rows
    per_row = [base + (1 if i >= rows - rem else 0) for i in range(rows)]
    cols = max(per_row)

    w_per = 5.0
    h_per = 4.0
    figsize = (max(6, cols * w_per), max(4, rows * h_per))
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=figsize)
    if rows == 1 and cols == 1:
        axes = [[axes]]
    elif rows == 1:
        axes = [axes]
    elif cols == 1:
        axes = [[ax] for ax in axes]

    idx = 0
    for r in range(rows):
        ncols_this_row = per_row[r]
        for c in range(cols):
            ax = axes[r][c]
            ax.set_axis_off()
            if c < ncols_this_row:
                if idx >= n:
                    continue
                label, gdf_plot, field = items[idx]
                base_layer = label.split("__")[0]
                if base_layer in no_edge_layers:
                    edgecolor = None
                    linewidth = 0
                else:
                    edgecolor = "k"
                    linewidth = 0.2
                try:
                    if field is None:
                        gdf_plot.plot(ax=ax, color="lightgray", edgecolor=edgecolor, linewidth=linewidth)
                    else:
                        vals = gdf_plot[field].tolist()
                        cols_list = [get_color_for_value(v) for v in vals]
                        gdf_plot.plot(ax=ax, color=cols_list, edgecolor=edgecolor, linewidth=linewidth)
                    short_label = label if len(label) <= max_label_chars else label[:max_label_chars-3] + "..."
                    ax.set_title(short_label, fontsize=10)
                except Exception as e:
                    ax.text(0.5, 0.5, f"Erro ao plotar:\n{e}", ha="center", va="center", fontsize=9)
                idx += 1
            else:
                ax.set_visible(False)

    patches = [mpatches.Patch(color=col, label=lbl) for col, lbl in zip(COLORS_ISH, CLASS_LABELS)]
    patches.append(mpatches.Patch(color=NO_DATA_COLOR, label="Sem dados / zero"))
    fig.legend(handles=patches, loc="lower center", ncol=len(patches), frameon=True, bbox_to_anchor=(0.5, 0.02))
    plt.tight_layout(rect=[0, 0.04, 1, 0.96])

    if output_path:
        outp = str(output_path)
        fig.savefig(outp, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        print(f"Imagem salva em: {outp}")
        return outp
    else:
        plt.show()
        return None


def run_interactive(gpkg_path=None, chosen_layers=None, fields_map=None, output_html=None, open_browser=True,
                    generate='both', static=False, static_out=None, static_dpi=300, static_max_features=None, static_no_edges=None):
    """
    generate: 'html','png','both' — controla quais saídas gerar.
    Se 'html' não for solicitado, não gera HTML (economiza memória).
    Se 'png' não for solicitado, não gera PNG.
    """
    if gpkg_path is None:
        files = find_gpkg_files(".")
        if not files:
            print("Nenhum .gpkg encontrado no diretório atual/subdiretórios.")
            return None
        chosen = choose_from_list("Escolha o arquivo GeoPackage (.gpkg) a usar:", files, allow_multiple=False)
        if not chosen:
            print("Cancelado.")
            return None
        gpkg_path = chosen[0]

    if not os.path.exists(gpkg_path):
        print("Arquivo não encontrado:", gpkg_path)
        return None

    layers = fiona.listlayers(gpkg_path)
    if not layers:
        print("Nenhuma camada encontrada:", gpkg_path)
        return None

    if chosen_layers is None:
        chosen_layers = choose_from_list("Escolha uma ou mais camadas (por número):", layers)
        if not chosen_layers:
            print("Nenhum layer selecionado. Abortando.")
            return None
    else:
        for l in chosen_layers:
            if l not in layers:
                raise ValueError(f"Layer {l} não está no gpkg. Disponíveis: {layers}")

    if isinstance(fields_map, str):
        fm_str = fields_map.strip()
        if fm_str.lower() == "all":
            fields_map = "ALL_GLOBAL"
        else:
            fields_map = parse_fields_arg(fields_map)
    if fields_map is None:
        fields_map = {}

    if fields_map == "ALL_GLOBAL":
        fm = {}
        for lyr in chosen_layers:
            try:
                gdf_head = gpd.read_file(gpkg_path, layer=lyr, rows=5)
            except Exception:
                gdf_head = gpd.read_file(gpkg_path, layer=lyr)
            cols = [c for c in gdf_head.columns if c != gdf_head.geometry.name]
            cs_cols = [c for c in cols if "cs" in c.lower()]
            fm[lyr] = cs_cols
        fields_map = fm

    layer_field_selection = {}
    for lyr in chosen_layers:
        try:
            gdf_head = gpd.read_file(gpkg_path, layer=lyr, rows=5)
        except Exception:
            gdf_head = gpd.read_file(gpkg_path, layer=lyr)
        cols = [c for c in gdf_head.columns if c != gdf_head.geometry.name]

        if lyr in fields_map and fields_map[lyr]:
            requested = fields_map[lyr]
            if isinstance(requested, str):
                if requested.strip().lower() == "all":
                    valid = [c for c in cols if "cs" in c.lower()]
                else:
                    valid = [requested] if requested in cols else []
            else:
                if any(str(x).strip().lower() == "all" for x in requested):
                    valid = [c for c in cols if "cs" in c.lower()]
                else:
                    valid = [f for f in requested if f in cols]
            if not valid:
                print(f"Aviso: nenhuma das colunas solicitadas para '{lyr}' foi encontrada. Disponíveis: {cols}")
            else:
                layer_field_selection[lyr] = valid
                continue

        print(f"\nColunas disponíveis na camada '{lyr}':")
        for i, c in enumerate(cols, start=1):
            print(f"  {i}) {c}")
        choice = input("Escolha número(s) de colunas separados por vírgula (ENTER para pular esta camada): ").strip()
        if choice == "":
            layer_field_selection[lyr] = []
            continue
        parts = [p.strip() for p in choice.split(",") if p.strip()]
        try:
            idxs = [int(p) - 1 for p in parts]
            sel = []
            for i in idxs:
                if i < 0 or i >= len(cols):
                    raise ValueError
                sel.append(cols[i])
            layer_field_selection[lyr] = sel
        except Exception:
            print("Entrada inválida — ignorando seleção para esta camada.")
            layer_field_selection[lyr] = []

    need_html = generate in ('html', 'both')
    need_png = generate in ('png', 'both') and static
    if not (need_html or need_png):
        print(f"Nenhuma saída solicitada (generate={generate}, static={static}). Abortando.")
        return None

    gdfs = []
    if need_html or need_png:
        for lyr in chosen_layers:
            gdf = gpd.read_file(gpkg_path, layer=lyr)
            gdfs.append((lyr, gdf))

    # bounds
    all_bounds = [gdf.total_bounds for _, gdf in gdfs]
    minxs = [b[0] for b in all_bounds]
    minys = [b[1] for b in all_bounds]
    maxxs = [b[2] for b in all_bounds]
    maxys = [b[3] for b in all_bounds]
    center_x = (min(minxs) + max(maxxs)) / 2.0
    center_y = (min(minys) + max(maxys)) / 2.0

    if need_html:
        m = folium.Map(location=[center_y, center_x], zoom_start=8, tiles="CartoDB Positron")
        for lyr_name, gdf in gdfs:
            sel_fields = layer_field_selection.get(lyr_name, [])
            if not sel_fields:
                fg = folium.FeatureGroup(name=f"{lyr_name}", show=False)
                try:
                    gdf_wgs = gdf.to_crs(epsg=4326)
                except Exception:
                    gdf_wgs = gdf.copy()
                folium.GeoJson(json.loads(gdf_wgs.to_json()), name=lyr_name).add_to(fg)
                fg.add_to(m)
                continue
            for field in sel_fields:
                if field not in gdf.columns:
                    print(f"Aviso: campo '{field}' não existe em '{lyr_name}'; pulando.")
                    continue
                gdf_copy = gdf.copy()
                gdf_copy[field] = gdf_copy[field].apply(lambda x: try_parse_float(x))
                try:
                    gdf_wgs = gdf_copy.to_crs(epsg=4326)
                except Exception:
                    gdf_wgs = gdf_copy.copy()
                geojson = json.loads(gdf_wgs.to_json())
                layer_label = f"{lyr_name}__{field}"
                fg = folium.FeatureGroup(name=layer_label, show=False)
                gj = folium.GeoJson(
                    geojson,
                    name=layer_label,
                    style_function=style_function_for_field(field),
                    tooltip=folium.GeoJsonTooltip(fields=[field], aliases=[field], localize=True),
                )
                gj.add_to(fg)
                fg.add_to(m)

        add_legend(m, title="Classes ISH")
        folium.LayerControl(collapsed=False).add_to(m)

        if output_html is None:
            gpkg_parent = os.path.dirname(os.path.abspath(gpkg_path))
            output_dir = os.path.join(gpkg_parent, "interactive_maps")
            os.makedirs(output_dir, exist_ok=True)
            output_html = os.path.join(output_dir, f"interactive_map_{Path(gpkg_path).stem}.html")
        else:
            output_dir = os.path.dirname(os.path.abspath(output_html)) or "."

        m.save(output_html)
        print("Mapa HTML salvo em:", output_html)
        if open_browser:
            try:
                webbrowser.open("file://" + os.path.abspath(output_html))
            except Exception:
                pass
    else:
        gpkg_parent = os.path.dirname(os.path.abspath(gpkg_path))
        output_dir = os.path.join(gpkg_parent, "interactive_maps")
        os.makedirs(output_dir, exist_ok=True)

    if need_png:
        gdfs_static = []
        for lyr, gdf in gdfs:
            gdf_small = gdf
            if static_max_features and len(gdf) > static_max_features:
                step = max(1, len(gdf) // static_max_features)
                idxs = list(range(0, len(gdf), step))[:static_max_features]
                gdf_small = gdf.iloc[idxs].reset_index(drop=True)
            gdfs_static.append((lyr, gdf_small))
        if static_out is None:
            img_path = os.path.join(output_dir, f"preview_{Path(gpkg_path).stem}.png")
        else:
            img_path = static_out
        if isinstance(static_no_edges, str):
            static_no_edges_list = [s.strip() for s in static_no_edges.split(",") if s.strip()]
        elif isinstance(static_no_edges, (list, tuple)):
            static_no_edges_list = list(static_no_edges)
        else:
            static_no_edges_list = []
        save_static_maps_from_selection(gpkg_path, gdfs_static, layer_field_selection,
                                        output_path=img_path, dpi=static_dpi, no_edge_layers=static_no_edges_list)
    return output_html if need_html else (img_path if need_png else None)


def main():
    parser = argparse.ArgumentParser(description="Criar mapa interativo (leaflet) a partir de um GeoPackage.")
    parser.add_argument("--gpkg", help="Caminho para o GeoPackage (.gpkg). Se omitido, será listado para escolha.")
    parser.add_argument("--layers", help="Nome(s) da(s) camada(s) dentro do gpkg, separados por vírgula. Se omitido, será solicitado interativamente.")
    parser.add_argument("--fields", help="Mapeamento layer:fields ex: 'layer1:field1,field2;layer2:field3' ou 'all' (opcional).")
    parser.add_argument("--output", help="Arquivo HTML de saída (opcional).")
    parser.add_argument("--no-open", action="store_true", help="Não abrir o HTML no navegador após criar.")
    parser.add_argument("--generate", choices=["html", "png", "both"], default="both",
                        help="O que gerar: 'html' (apenas HTML), 'png' (apenas PNG estático), 'both' (padrão).")
    parser.add_argument("--static", action="store_true", help="Gerar imagem estática (subplots) com as camadas/fields selecionados.")
    parser.add_argument("--static-out", help="Caminho do PNG de saída para a imagem estática (se omitido, salvo em interactive_maps/).")
    parser.add_argument("--static-dpi", type=int, default=300, help="DPI ao salvar a imagem estática (padrão 300).")
    parser.add_argument("--static-max-features", type=int, default=None, help="Se definido, amostra até esse número de feições por layer para o static plot.")
    parser.add_argument("--static-no-edges", help="Lista separada por vírgula de nomes de layers (base) para desenhar sem linhas (fills only) no static plot.")
    args = parser.parse_args()

    gpkg = args.gpkg
    layers = None
    if args.layers:
        layers = [s.strip() for s in args.layers.split(",") if s.strip()]
    fields_map = args.fields if args.fields else None

    out = run_interactive(gpkg_path=gpkg, chosen_layers=layers, fields_map=fields_map, output_html=args.output,
                         open_browser=(not args.no_open), generate=args.generate, static=args.static,
                         static_out=args.static_out, static_dpi=args.static_dpi, static_max_features=args.static_max_features,
                         static_no_edges=args.static_no_edges)
    if out is None:
        sys.exit(1)
    else:
        print("Concluído:", out)


if __name__ == "__main__":
    main()
