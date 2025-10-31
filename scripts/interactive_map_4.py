#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/interactive_map.py

Gera um mapa interativo (Leaflet via folium) a partir de um GeoPackage (.gpkg).
Permite escolher múltiplas camadas e múltiplos campos por camada para cloropleth.
Suporta:
  --fields all              -> em todas as camadas selecionadas, usar todas as colunas que contenham "cs"
  --fields "layer:all"      -> para a camada especificada, usar todas as colunas que contenham "cs"
  --fields "layer:fld1,fld2;layer2:fldX"
Uso:
  python -m scripts.interactive_map
  python -m scripts.interactive_map --gpkg path/to.gpkg --layers layer1,layer2 --fields "layer1:fieldA,fieldB;layer2:all" --output map.html

Dependências:
  geopandas, folium, branca, fiona
  Recomendo instalar via conda: conda install -c conda-forge geopandas folium branca fiona
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

try:
    import geopandas as gpd
    import folium
    import branca
    import fiona
except Exception:
    print("Erro ao importar dependências. Instale geopandas, folium, branca e fiona.")
    print("Ex.: conda install -c conda-forge geopandas folium branca fiona")
    raise

# Cores e classes solicitadas
COLORS_ISH = ['#FF5500', '#FFAA00', '#FFFF71', '#169200', '#2986cc']
# cor para "sem-dados" (NULL / 0)
NO_DATA_COLOR = "#cccccc"
CLASS_THRESHOLDS = [1.5, 2.5, 3.5, 4.5, 5.0]  # limites superiores
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
    """Prompt enumerated choices. Returns list of selected items (or [] if cancelled)."""
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
    """
    Parse fields argument of format:
      layerA:field1,field2;layerB:field3
    Returns dict {layer: [field,...], ...}
    Note: values are strings; if user used 'all' as value will appear as ['all'].
    """
    if not fields_arg:
        return {}
    mapping = {}
    parts = [p.strip() for p in fields_arg.split(";") if p.strip()]
    for part in parts:
        if ":" not in part:
            # allow short "all" handled elsewhere
            continue
        layer, fields_str = part.split(":", 1)
        fields = [f.strip() for f in fields_str.split(",") if f.strip()]
        if fields:
            mapping[layer.strip()] = fields
    return mapping


def get_color_for_value(v):
    """Return color for ISH value.
    Observações:
      - valores None/NULL e o número 0.0 são tratados como 'sem dados' e recebem NO_DATA_COLOR.
      - valores < 1.0 (mas > 0) recebem uma cor cinza clara.
    """
    try:
        if v is None:
            return NO_DATA_COLOR
        vf = float(v)
    except Exception:
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
    legend_html = f"""
     <div style="position: fixed; 
                 bottom: 50px; left: 10px; width: 240px; height: auto; 
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


def style_function_for_field(field):
    def style_function(feature):
        props = feature.get("properties", {})
        val = props.get(field)
        color = get_color_for_value(val)
        return {
            "fillColor": color,
            "color": "#444444",
            "weight": 0.5,
            "fillOpacity": 0.8,
        }
    return style_function


def try_parse_float(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "":
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def run_interactive(gpkg_path=None, chosen_layers=None, fields_map=None, output_html=None, open_browser=True,
                    generate='both', static=False, static_out=None):
    """
    fields_map can be:
      - None (interactive prompt per layer)
      - a string produced by CLI (--fields argument), parsed by parse_fields_arg
      - the string 'all' meaning global 'all' (select cs-containing columns for every selected layer)
      - a dict {layer: [field,..], ...} where a value may be ['all'] or ['cs_ish', ...]
    """
    # 1) discover gpkg
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

    # 2) list layers
    layers = fiona.listlayers(gpkg_path)
    if not layers:
        print("Nenhuma camada encontrada:", gpkg_path)
        return None

    # 3) choose layers (interactive if not provided)
    if chosen_layers is None:
        chosen_layers = choose_from_list("Escolha uma ou mais camadas (por número):", layers)
        if not chosen_layers:
            print("Nenhum layer selecionado. Abortando.")
            return None
    else:
        for l in chosen_layers:
            if l not in layers:
                raise ValueError(f"Layer {l} não está no gpkg. Disponíveis: {layers}")

    # 4) interpret fields_map argument
    # if string provided, parse / handle global 'all'
    if isinstance(fields_map, str):
        fm_str = fields_map.strip()
        if fm_str.lower() == "all":
            fields_map = "ALL_GLOBAL"
        else:
            # parse mapping like "layer:fld1,fld2;layer2:fldA"
            fields_map = parse_fields_arg(fields_map)
    if fields_map is None:
        fields_map = {}

    # If global ALL_GLOBAL signal, convert to explicit mapping {layer: [cs-columns]}
    if fields_map == "ALL_GLOBAL":
        fm = {}
        for lyr in chosen_layers:
            try:
                gdf_head = gpd.read_file(gpkg_path, layer=lyr, rows=5)
            except Exception:
                # fallback to reading a small part without rows param
                gdf_head = gpd.read_file(gpkg_path, layer=lyr)
            cols = [c for c in gdf_head.columns if c != gdf_head.geometry.name]
            cs_cols = [c for c in cols if "cs" in c.lower()]
            fm[lyr] = cs_cols
        fields_map = fm

    # 5) For each chosen layer, build final selection of fields (respecting per-layer 'all')
    layer_field_selection = {}
    for lyr in chosen_layers:
        try:
            gdf_head = gpd.read_file(gpkg_path, layer=lyr, rows=5)
        except Exception:
            gdf_head = gpd.read_file(gpkg_path, layer=lyr)
        cols = [c for c in gdf_head.columns if c != gdf_head.geometry.name]

        if lyr in fields_map and fields_map[lyr]:
            requested = fields_map[lyr]
            # requested may be string, list; unify to list
            if isinstance(requested, str):
                if requested.strip().lower() == "all":
                    valid = [c for c in cols if "cs" in c.lower()]
                else:
                    # string but not 'all' — try exact column if exists
                    valid = [requested] if requested in cols else []
            else:
                # list: if contains 'all' keyword, expand
                if any(str(x).strip().lower() == "all" for x in requested):
                    valid = [c for c in cols if "cs" in c.lower()]
                else:
                    valid = [f for f in requested if f in cols]
            if not valid:
                print(f"Aviso: nenhuma das colunas solicitadas para '{lyr}' foi encontrada. Disponíveis: {cols}")
                # fallthrough to interactive prompt
            else:
                layer_field_selection[lyr] = valid
                continue  # go to next layer

        # If we reach here, either lyr not in fields_map or requested fields invalid -> prompt
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

    # 6) load selected layers into memory
    # Decidir quais saídas serão necessárias para economizar tempo/memória
    need_html = generate in ('html', 'both')
    need_png = (generate in ('png', 'both')) and static
    if not (need_html or need_png):
        print(f"Nenhuma saída requisitada (generate={generate}, static={static}). Abortando.")
        return None
 
    # Carregar GDFs apenas se necessário
    gdfs = []
    if need_html or need_png:
        for lyr in chosen_layers:
            gdf = gpd.read_file(gpkg_path, layer=lyr)
            gdfs.append((lyr, gdf))

    # 7) determine map centre from bounds
    all_bounds = [gdf.total_bounds for _, gdf in gdfs]
    minxs = [b[0] for b in all_bounds]
    minys = [b[1] for b in all_bounds]
    maxxs = [b[2] for b in all_bounds]
    maxys = [b[3] for b in all_bounds]
    if not all_bounds:
        print("Erro: sem bounds calculáveis.")
        return None
    center_x = (min(minxs) + max(maxxs)) / 2.0
    center_y = (min(minys) + max(maxys)) / 2.0

    # 8) build folium map (apenas se HTML foi pedido)
    if need_html:
        m = folium.Map(location=[center_y, center_x], zoom_start=8, tiles="CartoDB Positron")

    # For each layer and each selected field, add a sublayer named "layer__field"
    for lyr_name, gdf in gdfs:
        sel_fields = layer_field_selection.get(lyr_name, [])
        if not sel_fields:
            # add base layer (no styling) just to toggle visibility
            fg = folium.FeatureGroup(name=f"{lyr_name}", show=False)
            try:
                gdf_wgs = gdf.to_crs(epsg=4326)
            except Exception:
                gdf_wgs = gdf.copy()
            folium.GeoJson(
                json.loads(gdf_wgs.to_json()),
                name=lyr_name,
            ).add_to(fg)
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

    # 9) add legend and controls
    add_legend(m, title="Classes ISH")
    folium.LayerControl(collapsed=False).add_to(m)

    # 10) write output HTML
    if output_html is None:
        gpkg_parent = os.path.dirname(os.path.abspath(gpkg_path))
        output_dir = os.path.join(gpkg_parent, "interactive_maps")
        os.makedirs(output_dir, exist_ok=True)
        output_html = os.path.join(output_dir, f"interactive_map_{Path(gpkg_path).stem}.html")
    else:
        output_dir = os.path.dirname(os.path.abspath(output_html)) or "."

    m.save(output_html)
    print("Mapa salvo em:", output_html)
    if open_browser:
        try:
            webbrowser.open("file://" + os.path.abspath(output_html))
        except Exception:
            pass
    else:
        # garantir output_dir para o caso de só gerar PNG (default path)
        gpkg_parent = os.path.dirname(os.path.abspath(gpkg_path))
        output_dir = os.path.join(gpkg_parent, "interactive_maps")
        os.makedirs(output_dir, exist_ok=True)

    # Se PNG estático foi requisitado, gerar aqui (apenas se static True)
    if need_png:
        if static_out is None:
            img_path = os.path.join(output_dir, f"preview_{Path(gpkg_path).stem}.png")
        else:
            img_path = static_out
        save_static_maps_from_selection(gpkg_path, gdfs, layer_field_selection, output_path=img_path,
                                        title_prefix=f"Preview - {Path(gpkg_path).stem}")
        # se HTML não foi gerado, retornar o caminho do PNG; caso contrário, retornar HTML
        return output_html if need_html else img_path
    return output_html

def save_static_maps_from_selection(gpkg_path, gdfs, layer_field_selection, output_path=None,
                                    crs_epsg=4326, cmap=None, title_prefix=None, dpi=150,
                                    max_label_chars=40):
    """
    Gera uma imagem estática com subplots a partir das mesmas camadas/colunas usadas no mapa interativo.

    Parâmetros:
      - gpkg_path: caminho do gpkg (apenas para nomes/metadata, pode ser None)
      - gdfs: lista de tuplas (layer_name, gdf) carregadas (como em run_interactive)
      - layer_field_selection: dict {layer_name: [field1, field2, ...]} (pode conter listas vazias para layer sem field)
      - output_path: se fornecido, salva PNG em output_path; caso contrário mostra a figura na tela
      - crs_epsg: EPSG para projetar antes de desenhar (default 4326)
      - cmap: não usado (mantemos as cores discretas definidas por get_color_for_value para ISH)
      - title_prefix: string para colocar no título (ex.: nome do gpkg / cenário)
      - dpi: resolução do PNG salvo
      - max_label_chars: truncar labels longos para não poluir a legenda

    Retorna: caminho do arquivo salvo (ou None se apenas mostrar).
    """
    # 1) montar lista de "plots" a partir de gdfs e layer_field_selection
    items = []  # list of (label, gdf_for_plot, field_or_None)
    for lyr_name, gdf in gdfs:
        sel_fields = layer_field_selection.get(lyr_name, [])
        if not sel_fields:
            # adicionar a layer "sem campo", como base (uma única visualização)
            try:
                gdf_plot = gdf.to_crs(epsg=crs_epsg)
            except Exception:
                gdf_plot = gdf.copy()
            items.append((lyr_name, gdf_plot, None))
        else:
            for fld in sel_fields:
                if fld not in gdf.columns:
                    # pula se não existir
                    continue
                gdf_copy = gdf.copy()
                # normaliza valores numéricos e converte virgula -> ponto
                gdf_copy[fld] = gdf_copy[fld].apply(lambda x: try_parse_float(x))
                try:
                    gdf_plot = gdf_copy.to_crs(epsg=crs_epsg)
                except Exception:
                    gdf_plot = gdf_copy
                label = f"{lyr_name}__{fld}"
                items.append((label, gdf_plot, fld))

    n = len(items)
    if n == 0:
        raise ValueError("Nenhum item para plotar (verifique layer_field_selection e gdfs).")

    # 2) escolher arranjo: seguir a heurística pedida
    # - se n <= 3: 1 linha, n colunas
    # - se n == 4: 2x2
    # - caso geral: rows = ceil(n/3) (até 3 colunas por linha preferencialmente)
    if n <= 3:
        rows = 1
    elif n == 4:
        rows = 2
    else:
        rows = math.ceil(n / 3)  # produz rows=2 para n=5,6; rows=3 para n=7..9 etc.

    base = n // rows
    rem = n % rows
    # distribuir o resto para as últimas linhas (pra obter ex: n=5 -> [2,3])
    per_row = [base + (1 if i >= rows - rem else 0) for i in range(rows)]
    cols = max(per_row)

    # 3) preparar figura: tamanho automático
    # dimensões por subplot (em polegadas) - ajuste se quiser maior/menor
    w_per = 5.0
    h_per = 4.0
    figsize = (max(6, cols * w_per), max(4, rows * h_per))
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=figsize)
    # axes pode ser 1D se rows==1 or cols==1 -> forçar 2D array para indexação uniforme
    if rows == 1 and cols == 1:
        axes = [[axes]]
    elif rows == 1:
        axes = [axes]
    elif cols == 1:
        axes = [[ax] for ax in axes]

    # 4) iterar e desenhar, respeitando per_row (preencher esquerda->direita, topo->baixo,
    #    mas deixando colunas vazias à direita se uma linha tiver menos elementos)
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
                # dessiner
                try:
                    if field is None:
                        # sem campo: plot simples
                        gdf_plot.plot(ax=ax, color="lightgray", edgecolor="k", linewidth=0.2)
                    else:
                        # construir lista de cores por feição com get_color_for_value
                        vals = gdf_plot[field].tolist()
                        cols_list = [get_color_for_value(v) for v in vals]
                        # plot usando cores já computadas; para manter legendas discretas, plot sem cmap
                        gdf_plot.plot(ax=ax, color=cols_list, edgecolor="k", linewidth=0.2)
                    # título do subplot (truncado se longo)
                    short_label = label if len(label) <= max_label_chars else label[:max_label_chars-3] + "..."
                    ax.set_title(short_label, fontsize=10)
                except Exception as e:
                    ax.text(0.5, 0.5, f"Erro ao plotar:\n{e}", ha="center", va="center", fontsize=9)
                idx += 1
            else:
                # espaço vazio: deixar sem eixos
                ax.set_visible(False)

    # 5) legenda das classes ISH (discreta) - desenhar no canto inferior direito como caixas coloridas
    # criar patches
    patches = [mpatches.Patch(color=col, label=lbl) for col, lbl in zip(COLORS_ISH, CLASS_LABELS)]
    # posicionar legenda global
    # colocar fora do subplot principal: usar fig.legend
    fig.legend(handles=patches, loc="lower center", ncol=len(patches), frameon=True,
               bbox_to_anchor=(0.5, 0.02))
    # título principal
    if title_prefix:
        fig.suptitle(title_prefix, fontsize=14, y=0.98)

    plt.tight_layout(rect=[0, 0.04, 1, 0.96])  # deixar espaço para legenda/título

    # 6) salvar ou mostrar
    if output_path:
        outp = str(output_path)
        fig.savefig(outp, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        print(f"Imagem salva em: {outp}")
        return outp
    else:
        plt.show()
        return None


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
    parser.add_argument("--static-out", help="Caminho do PNG de saída para a imagem estática (opcional).")    
    args = parser.parse_args()

    gpkg = args.gpkg
    layers = None
    if args.layers:
        layers = [s.strip() for s in args.layers.split(",") if s.strip()]
    fields_map = args.fields if args.fields else None

    out = run_interactive(gpkg_path=gpkg, chosen_layers=layers, fields_map=fields_map,
                          output_html=args.output, open_browser=(not args.no_open),
                          generate=args.generate, static=args.static, static_out=args.static_out)
    if out is None:
        sys.exit(1)
    else:
        print("Concluído:", out)


if __name__ == "__main__":
    main()
