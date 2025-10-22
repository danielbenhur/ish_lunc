<<<<<<< HEAD
# Retry: write the interactive_map.py script to /mnt/data/scripts/interactive_map.py
#!/usr/bin/env python3
=======
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
"""
scripts/interactive_map.py

Gera um mapa interativo (Leaflet via folium) a partir de um GeoPackage (.gpkg).
<<<<<<< HEAD
Opções:
 - escolher interativamente (via prompt) o arquivo .gpkg entre os encontrados no diretório atual/subdiretórios
 - escolher uma ou várias camadas do gpkg
 - escolher o campo a ser usado para choropleth (padrão: cs_ish)
 - gera um HTML interativo com controles de camadas e legenda

Como usar (CLI):
  python -m scripts.interactive_map                       # modo interativo (prompt)
  python -m scripts.interactive_map --gpkg path/to.gpkg --layers layer1,layer2 --field cs_ish --output map.html --open

Dependências:
  pip install geopandas folium branca
  (recomendo usar conda: conda install -c conda-forge geopandas folium branca)

Cores e classes de ISH usadas (conforme solicitado):
  colors_ish = ['#FF5500','#FFAA00', '#FFFF71','#169200','#2986cc']
  classes (intervalos, inclusive aproximado):
    1.00 - 1.50  (Mínimo)   -> '#FF5500'
    1.51 - 2.50  (Baixo)    -> '#FFAA00'
    2.51 - 3.50  (Médio)    -> '#FFFF71'
    3.51 - 4.50  (Alto)     -> '#169200'
    4.51 - 5.00  (Máximo)   -> '#2986cc'

O script foi pensado para rodar localmente e abrir um arquivo HTML com Leaflet.
=======
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
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
"""
import os
import sys
import argparse
import json
import webbrowser
from pathlib import Path

try:
    import geopandas as gpd
    import folium
    import branca
<<<<<<< HEAD
except Exception as e:
    print("Erro ao importar dependências. Instale geopandas, folium e branca.")
    print("Ex.: conda install -c conda-forge geopandas folium branca")
    raise

COLORS_ISH = ['#FF5500', '#FFAA00', '#FFFF71', '#169200', '#2986cc']
# class breaks (upper bounds): we'll use these thresholds for mapping inclusive ranges
CLASS_THRESHOLDS = [1.5, 2.5, 3.5, 4.5, 5.0]
CLASS_LABELS = [
    "1.00 - 1.50 (mínimo)",
=======
    import fiona
except Exception:
    print("Erro ao importar dependências. Instale geopandas, folium, branca e fiona.")
    print("Ex.: conda install -c conda-forge geopandas folium branca fiona")
    raise

# Cores e classes solicitadas
COLORS_ISH = ['#FF5500', '#FFAA00', '#FFFF71', '#169200', '#2986cc']
CLASS_THRESHOLDS = [1.5, 2.5, 3.5, 4.5, 5.0]  # limites superiores
CLASS_LABELS = [
    "1.00 - 1.50 (Mínimo)",
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
    "1.51 - 2.50 (Baixo)",
    "2.51 - 3.50 (Médio)",
    "3.51 - 4.50 (Alto)",
    "4.51 - 5.00 (Máximo)",
]

<<<<<<< HEAD
def find_gpkg_files(root="."):
    """Procura recursivamente por arquivos .gpkg a partir da raiz indicada."""
    root = Path(root)
    files = list(root.rglob("*.gpkg"))
    return [str(f) for f in files]

def choose_from_list(prompt, options):
    """Mostra opções enumeradas e retorna o item escolhido (index)."""
=======

def find_gpkg_files(root="."):
    root = Path(root)
    return [str(f) for f in root.rglob("*.gpkg")]


def choose_from_list(prompt, options, allow_multiple=True):
    """Prompt enumerated choices. Returns list of selected items (or [] if cancelled)."""
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
    print(prompt)
    for i, opt in enumerate(options, start=1):
        print(f"{i}) {opt}")
    while True:
<<<<<<< HEAD
        choice = input("Escolha um número (ou múltiplos separados por vírgula): ").strip()
        if not choice:
            print("Escolha inválida. Tente novamente.")
            continue
=======
        choice = input("Escolha número(s) separados por vírgula (ENTER para cancelar): ").strip()
        if choice == "":
            return []
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
        parts = [p.strip() for p in choice.split(",") if p.strip()]
        try:
            idxs = [int(p) - 1 for p in parts]
            if any(i < 0 or i >= len(options) for i in idxs):
                raise ValueError
<<<<<<< HEAD
            return [options[i] for i in idxs]
        except Exception:
            print("Entrada inválida — forneça números das opções separados por vírgula.")

def get_color_for_value(v):
    """Retorna a cor correspondente ao valor v (float). None/NaN => gray."""
    try:
        if v is None or (isinstance(v, float) and (v != v)):  # NaN check
=======
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
    """Return color for ISH value; NaN/None => light grey."""
    try:
        if v is None:
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
            return "#cccccc"
        v = float(v)
    except Exception:
        return "#cccccc"
<<<<<<< HEAD
=======
    if v < 1.0:
        return "#eeeeee"
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
    for thresh, color in zip(CLASS_THRESHOLDS, COLORS_ISH):
        if v <= thresh:
            return color
    return COLORS_ISH[-1]

<<<<<<< HEAD
def add_legend(map_obj, title="Classes ISH"):
    """Adiciona uma legenda simples ao mapa (usando branca MacroElement)."""
    labels_html = ""
    for lbl, col in zip(CLASS_LABELS, COLORS_ISH):
        labels_html += f'<div style="display:flex;align-items:center;margin-bottom:4px;"><div style="width:18px;height:14px;background:{col};margin-right:8px;border:1px solid #444;"></div><div style="font-size:12px">{lbl}</div></div>'
    legend_html = f"""
     <div style="position: fixed; 
                 bottom: 50px; left: 10px; width: 220px; height: auto; 
=======

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
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
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

<<<<<<< HEAD
def style_function_factory(field):
    def style_function(feature):
        props = feature["properties"]
=======

def style_function_for_field(field):
    def style_function(feature):
        props = feature.get("properties", {})
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
        val = props.get(field)
        color = get_color_for_value(val)
        return {
            "fillColor": color,
            "color": "#444444",
            "weight": 0.5,
            "fillOpacity": 0.8,
        }
    return style_function

<<<<<<< HEAD
def try_parse_float(x):
    """Tenta converter strings com vírgula para float, etc."""
=======

def try_parse_float(x):
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "":
        return None
<<<<<<< HEAD
    # replace comma decimal by dot
=======
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None

<<<<<<< HEAD
def run_interactive(gpkg_path=None, chosen_layers=None, field=None, output_html=None, open_browser=True):
    """Fluxo principal — se parâmetros não fornecidos, faz prompts interativos."""
    # 1) discover gpkg files if not provided
    if gpkg_path is None:
        files = find_gpkg_files(".")
        if not files:
            print("Nenhum arquivo .gpkg encontrado no diretório atual/subdiretórios.")
            return None
        chosen = choose_from_list("Escolha o arquivo GeoPackage (.gpkg) a usar:", files)
=======

def run_interactive(gpkg_path=None, chosen_layers=None, fields_map=None, output_html=None, open_browser=True):
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
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
        gpkg_path = chosen[0]

    if not os.path.exists(gpkg_path):
        print("Arquivo não encontrado:", gpkg_path)
        return None

<<<<<<< HEAD
    # list layers
    import fiona
    layers = fiona.listlayers(gpkg_path)
    if not layers:
        print("Nenhuma camada encontrada no gpkg:", gpkg_path)
        return None

    if chosen_layers is None:
        chosen_layers = choose_from_list("Escolha uma ou mais camadas (por número):", layers)
    else:
        # validate provided chosen_layers list
        for l in chosen_layers:
            if l not in layers:
                raise ValueError(f"Layer {l} not in gpkg. Available: {layers}")

    # load chosen layers as GeoDataFrames into list
=======
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
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
    gdfs = []
    for lyr in chosen_layers:
        gdf = gpd.read_file(gpkg_path, layer=lyr)
        gdfs.append((lyr, gdf))

<<<<<<< HEAD
    # Determine default field: prefer cs_ish if present, else first ire_cs_*
    if field is None:
        candidate = None
        for _, gdf in gdfs:
            if "cs_ish" in gdf.columns:
                candidate = "cs_ish"
                break
        if candidate is None:
            # look for any ire_cs_*
            for _, gdf in gdfs:
                for c in gdf.columns:
                    if c.startswith("ire_cs_"):
                        candidate = c
                        break
                if candidate:
                    break
        field = candidate
    # If still None, prompt user to choose a field from union of columns
    if field is None:
        all_cols = set()
        for _, gdf in gdfs:
            all_cols.update(gdf.columns.tolist())
        cols = sorted(list(all_cols))
        print("Nenhum campo padrão (cs_ish/ire_cs_) encontrado. Escolha um campo para usar na cloropleta:")
        for i, c in enumerate(cols, start=1):
            print(f"{i}) {c}")
        sel = input("Escolha número (ou ENTER para cancelar): ").strip()
        if sel == "":
            print("Operação cancelada.")
            return None
        try:
            idx = int(sel) - 1
            field = cols[idx]
        except Exception:
            print("Entrada inválida. Abortando.")
            return None

    print("Usando campo:", field)

    # Create base folium map centered on combined centroid
    all_bounds = []
    for _, gdf in gdfs:
        all_bounds.append(gdf.total_bounds)  # [minx, miny, maxx, maxy]
    # compute average centre
=======
    # 7) determine map centre from bounds
    all_bounds = [gdf.total_bounds for _, gdf in gdfs]
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
    minxs = [b[0] for b in all_bounds]
    minys = [b[1] for b in all_bounds]
    maxxs = [b[2] for b in all_bounds]
    maxys = [b[3] for b in all_bounds]
<<<<<<< HEAD
    center_x = (min(minxs) + max(maxxs)) / 2.0
    center_y = (min(minys) + max(maxys)) / 2.0

    m = folium.Map(location=[center_y, center_x], zoom_start=8, tiles="CartoDB Positron")

    # add each chosen layer as a FeatureGroup with the choropleth styling
    for lyr_name, gdf in gdfs:
        # ensure field present in this gdf; if not, create NaNs
        if field not in gdf.columns:
            gdf[field] = None
        # add layer
        fg = folium.FeatureGroup(name=lyr_name, show=True)
        # convert geometries to WGS84 for folium (leaflet expects lat/lon)
        try:
            gdf_wgs = gdf.to_crs(epsg=4326)
        except Exception:
            gdf_wgs = gdf.copy()
        geojson = json.loads(gdf_wgs.to_json())
        gj = folium.GeoJson(
            geojson,
            name=lyr_name,
            style_function=style_function_factory(field),
            tooltip=folium.GeoJsonTooltip(fields=[field], aliases=[field], localize=True),
        )
        gj.add_to(fg)
        fg.add_to(m)

    add_legend(m, title="Classes ISH")

    folium.LayerControl(collapsed=False).add_to(m)

    # default output path
    if output_html is None:
        # try to place into same folder as gpkg under output/interactive_map.html
=======
    if not all_bounds:
        print("Erro: sem bounds calculáveis.")
        return None
    center_x = (min(minxs) + max(maxxs)) / 2.0
    center_y = (min(minys) + max(maxys)) / 2.0

    # 8) build folium map
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
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
        gpkg_parent = os.path.dirname(os.path.abspath(gpkg_path))
        output_dir = os.path.join(gpkg_parent, "interactive_maps")
        os.makedirs(output_dir, exist_ok=True)
        output_html = os.path.join(output_dir, f"interactive_map_{Path(gpkg_path).stem}.html")

    m.save(output_html)
    print("Mapa salvo em:", output_html)
    if open_browser:
<<<<<<< HEAD
        webbrowser.open("file://" + os.path.abspath(output_html))
    return output_html

=======
        try:
            webbrowser.open("file://" + os.path.abspath(output_html))
        except Exception:
            pass
    return output_html


>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
def main():
    parser = argparse.ArgumentParser(description="Criar mapa interativo (leaflet) a partir de um GeoPackage.")
    parser.add_argument("--gpkg", help="Caminho para o GeoPackage (.gpkg). Se omitido, será listado para escolha.")
    parser.add_argument("--layers", help="Nome(s) da(s) camada(s) dentro do gpkg, separados por vírgula. Se omitido, será solicitado interativamente.")
<<<<<<< HEAD
    parser.add_argument("--field", help="Campo a ser usado para cloropleta (default: cs_ish ou primeiro ire_cs_*).")
=======
    parser.add_argument("--fields", help="Mapeamento layer:fields ex: 'layer1:field1,field2;layer2:field3' ou 'all' (opcional).")
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
    parser.add_argument("--output", help="Arquivo HTML de saída (opcional).")
    parser.add_argument("--no-open", action="store_true", help="Não abrir o HTML no navegador após criar.")
    args = parser.parse_args()

    gpkg = args.gpkg
    layers = None
    if args.layers:
        layers = [s.strip() for s in args.layers.split(",") if s.strip()]
<<<<<<< HEAD
    out = run_interactive(gpkg_path=gpkg, chosen_layers=layers, field=args.field, output_html=args.output, open_browser=(not args.no_open))
=======
    fields_map = args.fields if args.fields else None

    out = run_interactive(gpkg_path=gpkg, chosen_layers=layers, fields_map=fields_map, output_html=args.output, open_browser=(not args.no_open))
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
    if out is None:
        sys.exit(1)
    else:
        print("Concluído:", out)

<<<<<<< HEAD
if __name__ == "__main__":
    main()

# ensure directory exists and write file
import os
os.makedirs("/mnt/data/scripts", exist_ok=True)
with open("/mnt/data/scripts/interactive_map.py", "w", encoding="utf-8") as f:
    f.write(script)

"/mnt/data/scripts/interactive_map.py"
=======

if __name__ == "__main__":
    main()
>>>>>>> c408c7f (Atualizações no interactive_map e criação de environment.yml)
