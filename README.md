
# ISH Automation README

Este repositório contém scripts para calcular e processar o **Índice de Segurança Hídrica LabGest-UFES/Neades-CPID (ISH_LUNC)** por ottobacias e para agregar/visualizar esses resultados em unidades de apresentação (municípios, estados, regiões etc.).

**Arquitetura de exemplo**
```
ISH/
├─ joinISH.py
├─ planilhas/
├─ scripts/
│  ├─ aggregate_presentation.py
│  ├─ aplica_recortes.py
│  ├─ plot_bho.py
│  └─ interactive_map.py
├─ cnr_<cenario>/
│  ├─ input/
│  │  ├─ BHO_area.gpkg
│  │  └─ dim_*.csv
│  └─ output/
│     └─ ish_cnr_<cenario>.gpkg
├─ recortes/
│  └─ *.gpkg
└─ apresentacao/
   └─ *.gpkg
```

---

## Índice

1. [Pré-requisitos](#pré-requisitos)  
2. [Formato dos arquivos de entrada — exemplos concretos](#formatos-de-entrada)  
3. [Saídas esperadas — exemplos concretos](#formatos-de-saída)  
4. [Como rodar os scripts (exemplos)](#como-rodar)  
5. [Interpretação dos logs](#logs)  
6. [Validação rápida e dicas](#validacao)  
7. [Exemplo numérico da agregação ponderada](#exemplo-numerico)  
8. [Como abrir/inspecionar resultados](#inspecionar)  

---

## Pré-requisitos

1. Recomenda-se utilizar **conda** (canal `conda-forge`) para instalar dependências geoespaciais:

```bash
conda create -n ishgeo python=3.10 -c conda-forge geopandas pandas fiona shapely pyproj rtree matplotlib
conda activate ishgeo
```

Verifique instalação:
```bash
python -c "import geopandas as gpd, pandas as pd, fiona; print('ok')"
```

2. Em ambiente Linux, pessoalmente recomendo uso de ambiente virtual, no qual você pode instalar os pacotes sem interferir na instalação global do Python. Para isso, siga os seguintes passos:

```bash
# Crie um novo ambiente virtual (você pode escolher o nome, aqui usamos "meu_ambiente")
python3 -m venv meu_ambiente

# Ative o ambiente virtual
source meu_ambiente/bin/activate

# Agora, dentro deste ambiente, instale os pacotes desejados
pip install geopandas pandas

#Após ativar o ambiente virtual, você pode executar seu script Python normalmente. Quando terminar, para sair do ambiente virtual, basta usar o comando:
bash
deactivate
```

3. Utilizar o pipx para Aplicações Globalmente Isoladas
Se você deseja instalar um aplicativo Python globalmente sem afetar o ambiente do sistema, use o pipx, que administra ambientes virtuais automaticamente:

```bash
# Instale o pipx (se ainda não estiver instalado)
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Instale o aplicativo desejado com pipx
pipx install nome_do_app
```
> Atenção: > Evite utilizar a flag --break-system-packages para forçar a instalação global, pois isso pode comprometer a integridade do ambiente Python do seu sistema, causando problemas futuros.

Essas abordagens garantem que as instalações de pacotes sejam gerenciadas de forma isolada, mantendo o sistema operacional estável e evitando conflitos entre versões.

---

## Formatos de entrada

A seguir, exemplos concretos de como **devem** ser os arquivos de entrada.

### 1) `BHO_area.gpkg` — ottobacias (entrada principal)
- **Local:** `./cnr_<cenario>/input/BHO_area.gpkg`
- **Layer:** `bho_area` (ou outro nome; ajuste `joinISH.py` se necessário)
- **CRS:** `EPSG:31984` (SIRGAS 2000 / UTM zone 24S) — ideal manter consistente.
- **Colunas esperadas:**
  - `cobacia` — identificador único (inteiro)
  - `geometry` — `MultiPolygon`

**Preview (exemplo):**

| cobacia | geometry |
|--------:|---------|
| 7913    | MULTIPOLYGON(...) |
| 77975   | MULTIPOLYGON(...) |
| 77976   | MULTIPOLYGON(...) |

---

### 2) `dim_*.csv` — dimensões utilizadas no cálculo do ISH
- **Local:** `./cnr_<cenario>/input/dim_<sigla>_cnr_<cenario>.csv`
- **Formato:** CSV com 2 colunas: `cobacia` e `ire_cs_<sigla>`
- **Regras:**
  - `cobacia` deve ser numérico inteiro (ex.: `7913`). Se houver formatos distintos (p.ex. `7796133.0`, `7.796.133`) o script contém rotinas de limpeza; porém prefira enviar limpo.
  - `ire_cs_<sigla>` deve ser float (p.ex. `1.234`).

**Exemplo `dim_amb_cnr_atlas2035.csv`:**
```
cobacia,ire_cs_amb
7913,4.0
77975,1.0
77976,0.0
77977,0.5
77979,1.2
```

**Observação:** se o CSV contiver linhas duplicadas por `cobacia`, corrigi-las evita resultados duplicados no `merge`. O script pode aplicar `drop_duplicates()` ou `groupby(...).mean()` conforme sua configuração.

---

## Formatos de saída

### 1) Saída do `joinISH.py`
**Arquivo:** `./cnr_<cenario>/output/ish_cnr_<cenario>.gpkg`  
**Layer principal:** `regiao_completa`

**Schema (exemplo):**
- `cobacia` (int)
- `ire_cs_amb` (float)
- `ire_cs_eco` (float)
- `ire_cs_hum` (float)
- `ire_cs_inu` (float)
- `ire_cs_res` (float)
- `cs_ish` (float) — valor combinado do índice por ottobacia
- `geometry` (MultiPolygon)
- CRS: `EPSG:31984`

**Preview (exemplo):**

| cobacia | ire_cs_amb | ire_cs_eco | ire_cs_hum | ire_cs_inu | ire_cs_res | cs_ish |
|-------:|-----------:|-----------:|----------:|----------:|----------:|-------:|
| 7913   | NaN        | NaN        | 4.0       | NaN       | NaN       | 4.0000 |
| 77975  | 1.0        | 1.02       | 0.0       | NaN       | 2.0       | 1.3399 |

---

### 2) Saída do `aggregate_presentation.py`
- A agregação (por padrão `mean`, área-ponderada) **escreve uma nova camada no mesmo GPKG de saída do joinISH** (padrão), com nome composto por `agg_<presentation_basename>` (ex.: `agg_mun_es`).
- Campo resultado: `cs_ish_<tipo_agg>` (float)
- Preserva demais atributos da camada de apresentação (p.ex. `fid`, `name`, ...)

**Preview (exemplo, camada `agg_mun_es`):**

| fid | name         | area_apresent_km2 | cs_ish_mean |
|----:|--------------|-------------------:|-----------:|
| 1001| Município A  | 150.0             | 1.234      |
| 1002| Município B  | 72.5              | 0.456      |
| 1003| Município C  | 10.0              | NaN        |

`NaN` indica ausência de interseção entre ottobacias e a unidade de apresentação.

---

## Como rodar (comandos concretos)

### 1) Rodar `joinISH.py` (gerar `ish_cnr`)
Na raiz do projeto (`ISH/`):

Executar joinISH para gerar o gpkg base (caso ainda não esteja criado):
```bash
python3 joinISH.py atlas_2035
```
### 2) Agregar para apresentação (municípios)
Usando o output gerado acima:

1. Agregar por municípios (média apenas — comportamento padrão):
```bash
python -m scripts.aggregate_presentation atlas_2035 ./apresentacao/mun_es.gpkg --id-field fid
```
Isso criará (ou substituirá) a camada `agg_mun_es` dentro de:
`./cnr_atlas_2035/output/ish_cnr_atlas_2035.gpkg` contendo a coluna `cs_ish_mean`.

2. Agregar por municípios pedindo várias agregações:
```bash
python -m scripts.aggregate_presentation atlas_2035 ./apresentacao/mun_es.gpkg --id-field fid --agg mean median max
```
Resultado: camada `agg_mun_es` com colunas `cs_ish_mean`, `cs_ish_median`, `cs_ish_max`.

3. Pedir todas as agregações:
```bash
python -m scripts.aggregate_presentation atlas_2035 ./apresentacao/mun_es.gpkg --id-field fid --agg all
```

4. Use --targets para especificar alvos a agregar.

Exemplo: --targets cs_ish ire_cs_amb ire_cs_eco

Exemplo: --targets all para agregar cs_ish e todas as colunas do input que começam com ire_cs_.

As colunas geradas no layer de saída terão o nome: <target>_<agg> (ex.: ire_cs_amb_mean, cs_ish_median).

```bash
python -m scripts.aggregate_presentation atlas_2035 ./apresentacao/mun_es.gpkg --id-field fid --agg mean --targets all
# -> cria agg_mun_es com cs_ish_mean, ire_cs_amb_mean, ire_cs_eco_mean, ...
```
---

## Interpretação da camada de saída

- **Nome da camada:** `agg_<presentation_basename>` (por ex. `agg_mun_es`)
- **Colunas:** todas as colunas originais da camada de apresentação são preservadas,
  e as colunas `cs_ish_<agg>` são adicionadas (por ex. `cs_ish_mean`).
- **Valores `NaN`:** se uma unidade de apresentação não possui interseção com as ottobacias,
  as colunas de agregação terão `NaN`.

---

## Exemplo prático (numérico)

Suponha Município X (fid=1001), área = 100 km²; interseções:
- peça1: cs_ish = 2.0, area_inter = 25 km²
- peça2: cs_ish = 1.5, area_inter = 10 km²
- peça3: cs_ish = 0.5, area_inter = 65 km²

Cálculo média ponderada (cs_ish_mean):
- 2.0*(25/100) + 1.5*(10/100) + 0.5*(65/100) = 0.975

Se pedir `--agg mean median`, a camada `agg_mun_es` conterá as colunas:
- `cs_ish_mean` = 0.975
- `cs_ish_median` = (weighted median computed as described)

---

## 3) Plotar BHO
```bash
python -m scripts.plot_bho ./cnr_atlas_2035/input/BHO_area.gpkg --layer bho_area --area --output ./cnr_atlas_2035/output/bho_plot.png
```

Também podemos plotar interativamente:
### O que o script faz

- Lista (recursivamente) arquivos .gpkg no diretório atual, caso você não passe --gpkg.
- Lista camadas do .gpkg e permite escolher uma ou mais camadas.
- Seleciona automaticamente o campo cs_ish (se presente) ou um ire_cs_* disponível; também permite que você escolha outro campo.
- Gera um mapa interativo (Leaflet via folium) com cloropleta usando as cores ISH que você especificou e as faixas definidas.
- Salva o HTML em interactive_maps/interactive_map_<gpkg_stem>.html ao lado do gpkg por padrão e abre no navegador.

### Como rodar

Modo interativo (prompt):

```bash
python -m scripts.interactive_map
```

Modo com argumentos:

```bash
python -m scripts.interactive_map --gpkg ./cnr_atlas_2035/input/BHO_area.gpkg --layers bho_area --field cs_ish --output /tmp/map.html
```

Dependências

```bash
#geopandas, folium, branca. Recomendo instalar via conda-forge:
conda install -c conda-forge geopandas folium branca
```

ou pip:

```bash
pip install geopandas folium branca
```

(Geopandas funciona melhor via conda por dependências binárias.)

### Como integrar ao joinISH.py

Após gerar o ish_cnr_<cenario>.gpkg você pode chamar o script diretamente (subprocess) ou importá-lo. Exemplo (dentro do joinISH.py):

```bash
# após salvar output_file (caminho do gpkg)
import subprocess, sys
subprocess.run([sys.executable, "-m", "scripts.interactive_map", "--gpkg", output_file, "--layers", "regiao_completa", "--field", "cs_ish"])
```

Ou chamar programaticamente:

```bash
from scripts.interactive_map import run_interactive
run_interactive(gpkg_path=output_file, chosen_layers=["regiao_completa"], field="cs_ish")
```
---

## Logs e interpretação rápida

Recomenda-se redirecionar saída e erros para arquivos de log:

```bash
mkdir -p logs
python3 joinISH.py atlas_2035 > logs/joinISH_atlas2035.log 2>&1
python -m scripts.aggregate_presentation atlas_2035 ./apresentacao/mun_es.gpkg --id-field fid > logs/aggregate_mun.log 2>&1
```

**O que procurar nos logs**
- `Camadas disponíveis:` — confirma leitura do GPKG de entrada.
- `Preview (head)` — confirma formato e nomes das colunas.
- `Reprojecting presentation layer to input CRS:` — indica reprojeção automática.
- `Computing intersections (this may take time)...` — overlay em andamento.
- `Writing aggregated layer mean_mun_es to ...` — gravação concluída.

**Erros comuns**
- `ModuleNotFoundError: No module named 'geopandas'` → instale geopandas (preferível via conda).
- `ValueError: Input layer does not contain 'cs_ish'` → verifique se `joinISH.py` produziu `cs_ish`.
- `fiona.listlayers(...)` falha → verifique instalação do `fiona`.

---

## Validação rápida (scripts úteis)

### Verificar CSVs e duplicatas
```python
import pandas as pd
df = pd.read_csv("cnr_atlas_2035/input/dim_res_cnr_atlas2035.csv", sep=None, engine="python")
print("total rows:", len(df))
print("unique cobacia:", df['cobacia'].nunique())
print(df['cobacia'].value_counts().head())
```

### Verificar GPKG e camadas
```python
import fiona
print(fiona.listlayers("cnr_atlas_2035/output/ish_cnr_atlas_2035.gpkg"))
```

---

## Boas práticas e recomendações

- Garanta CSVs limpos (sem duplicatas em `cobacia`) — embora os scripts incluam rotinas de limpeza, é melhor corrigir na origem.
- Use `conda` para evitar problemas com dependências nativas.
- Faça backup do GPKG antes de rodar operações que sobrescrevem camadas.
- Para conjuntos grandes, execute a interseção em um servidor/VM com memória adequada.

---

## Exemplos concretos
- Input:
  - `cnr_atlas_2035/input/BHO_area.gpkg`
  - `cnr_atlas_2035/input/dim_amb_cnr_atlas2035.csv`
  - `cnr_atlas_2035/input/dim_hum_cnr_atlas2035.csv`
  - `apresentacao/mun_es.gpkg`
- Output esperados:
  - `cnr_atlas_2035/output/ish_cnr_atlas_2035.gpkg` (layer `regiao_completa`, `agg_mun_es`, etc.)
  - `cnr_atlas_2035/output/bho_plot.png` (opcional)

---
