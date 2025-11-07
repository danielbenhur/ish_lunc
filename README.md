
# ISH_LUNC - README

Este repositório contém scripts com finalidade principal de calcular o **Índice de Segurança Hídrica LabGest-UFES/Neades-CPID (ISH_LUNC)** por ottobacias e agregar/visualizar esses resultados em unidades de apresentação (municípios, estados, regiões etc.). O projeto ainda está em fase inicial de desenvolvimento.

**Arquitetura de exemplo**
```
ISH/
├─ joinISH.py     # Script principal que calcula o ISH a partir de um cenário determinado
├─ environment.yml     # ambiente, caso use conda
├─ requirements.txt     # pacotes requeridos, caso use venv
├─ planilhas/     # Um exemplo de pasta onde planilhas de cálculos manuais possam ser armazenadas e reutilizadas
├─ scripts/     # Alguns scripts auxiliares
│  ├─ aggregate_presentation.py     # Agrega os dados do ISH para uma outra base de representação de informações (como municípios, bacias hidrográficas...) 
│  ├─ aplica_recortes.py     # Script que realiza recortes da área com dados (para diminuir área total de estudo)
│  ├─ plot_bho.py     # Script simples para plotar uma bho
│  └─ interactive_map.py     # Gera mapas conforme as classes do ISH, em html ou png
│  └─ update_dimension.py     # Altera uma ou mais dimensões de um arquivo gpkg já criado (útil quando se quer modificar uma dimensão apenas, sem ter que possuir os arquivos das demais dimensões)
│  └─ gdf_to_csv.py      # Transforma qualquer geoddataframe em um csv (útil para criar csv do arquivo gpkg do cenário)
│  └─ gdfhead.py     # Visualizador de cabeçalho de geodataframe (útil para verificar colunas e exemplos de dados do arquivo)
├─ cnr_<cenario>/    # Padronizado, para facilitar organização dos cenários
│  ├─ input/     # Pasta onde serão buscados os arquivos de entrada do joinISH
│  │  ├─ BHO_area.gpkg     # Base hidrográfica ottocodificada de referência para a área de estudo (o ideal é que contenha uma área um pouco além da borda da área de estudo de interesse real)
│  │  └─ dim_<sigla_da_dimensão>.csv     # Todas as dimensões precisam estar com esse padrão de nomeclatura
│  └─ output/     # Pasta onde estará as daídas dos cenários
│     └─ ish_cnr_<cenario>.gpkg     # Arquivo principal de saída padrão dos scripts que calculam cenários. Nele estarão 
│     └─ interactive_maps/
│        └─ interactive_map_ish_<cenário>.html     # Arquivo com o mapa interativo em html (saída padrão interactive_map.py)
│        └─ preview_ish_<cenário>.png     # Arquivo com o mapa interativo estático em png (saída padrão interactive_map.py)
├─ recortes/     # Pasta com geodataframes para gerar recorte de área
│  └─ *.gpkg     # Importante ser do tipo gpkg
└─ apresentacao/     # Pasta com geodataframes utilizados para gerar valores agregados por regiões
   └─ *.gpkg     # Importante ser do tipo gpkg
```

---

## Índice

1. [Pré-requisitos](#pré-requisitos)  
2. [Formatos de entrada](#formatos-de-entrada)  
3. [Formatos de saída](#formatos-de-saída)  
4. [Como rodar os scripts (Exemplos)](#como-rodar-os-scripts-exemplos)  
5. [Interpretação da camada de saída do joinISH](#interpretação-da-camada-de-saída-do-joinish)
6. [Exemplo prático (numérico)](#exemplo-prático-numérico)  
7. [Logs e interpretação rápida](#logs-e-interpretação-rápida)  
8. [Validação rápida (scripts úteis)](#validação-rápida-scripts-úteis)  
9. [Boas práticas e recomendações](#boas-práticas-e-recomendações)  
10. [Exemplos de estrutura da pasta final](#exemplos-de-estrutura-da-pasta-final)  

---

## Pré-requisitos

1. Recomenda-se utilizar **conda** (canal `conda-forge`) para instalar dependências geoespaciais:

```bash
conda env create -f environment.yml
conda activate ish_lunc
```


2. Em ambiente que houver restrição de espaço, prefira o uso de ambiente virtual (é o que pessoalmente uso em meu Puppy Linux), no qual você pode instalar os pacotes sem interferir na instalação global do Python e ao mesmo tempo ter facilidade de apagar os arquivos quando precisar. Para isso, siga os seguintes passos:

```bash
# Crie um novo ambiente virtual (você pode escolher o nome, aqui usamos "ish_lunc_venv")
python3 -m venv ish_lunc_venv

# Ative o ambiente virtual
source ish_lunc_venv/bin/activate

# Agora, dentro deste ambiente, instale os pacotes desejados (presentes no arquivo requirements.txt)
pip install -r requirements.txt
```

- Se tiver atualizado os scripts e quiser refazer o arquivo requeriments.txt, pode usar o comando:
`pip freeze > requirements.txt`

- Após ativar o ambiente virtual, você pode executar seu script Python normalmente. Quando terminar, para sair do ambiente virtual, basta usar o comando:
`deactivate`

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
  - `cobacia` deve ser numérico inteiro (ex.: `7913`). Se houver formatos distintos (p.ex. `7796133.0`, `7.796.133`) o script pode não funcionar; prefira enviar limpo.
  - `ire_cs_<sigla>` deve ser float (p.ex. `1.234`).

**Exemplo `dim_amb_cnr_2035.csv`:**
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

## Como rodar os scripts (Exemplos)

### 1) Rodar `joinISH.py` (gerar `ish_cnr`, ou seja, o ISH para algum cenário)
Após criar uma pasta denominada `cnr_<nome_do_cenário>`, e dentro dela a pasta input contendo o arquivo base `BHO_area.gpkg`, bem como os arquivos das dimensões, nomeados com o padrão ``dim_<nome_da_dimensão>_<nome_do_cenário>.csv``
Na raiz do projeto (`ISH/`, isto é, fora da pasta do cenário específico):

Executar joinISH para gerar o gpkg base (caso ainda não esteja criado):
```bash
python3 joinISH.py 2035
```
### 2) Agregar para uma área de apresentação (ex.: municípios)
Usando o output gerado acima:

1. Agregar por municípios (média apenas — comportamento padrão):
```bash
python3 -m scripts.aggregate_presentation 2035 ./apresentacao/mun_es.gpkg --id-field cod_ibge
```
Isso criará (ou substituirá) a camada `agg_mun_es` dentro de:
`./cnr_2035/output/ish_cnr_2035.gpkg` contendo a coluna `cs_ish_mean`.

2. Agregar por municípios pedindo várias agregações (as possíveis são média ponderada, mediana ponderada, máximo e mínimo):
```bash
python3 -m scripts.aggregate_presentation 2035 ./apresentacao/mun_es.gpkg --id-field cod_ibge --agg mean median max
```
Resultado: camada `agg_mun_es` com colunas `cs_ish_mean`, `cs_ish_median`, `cs_ish_max`.

3. Pedir todas as agregações:
```bash
python3 -m scripts.aggregate_presentation 2035 ./apresentacao/mun_es.gpkg --id-field cod_ibge --agg all
```

4. Use --targets para especificar alvos a agregar.

Exemplo: --targets cs_ish ire_cs_amb ire_cs_eco

Exemplo: --targets all para agregar cs_ish e todas as colunas do input que começam com ire_cs_.

As colunas geradas no layer de saída terão o nome: <target>_<agg> (ex.: ire_cs_amb_mean, cs_ish_median).

```bash
python3 -m scripts.aggregate_presentation 2035 ./apresentacao/mun_es.gpkg --id-field fid --agg mean --targets all
# -> cria agg_mun_es com cs_ish_mean, ire_cs_amb_mean, ire_cs_eco_mean, ...
```

### 3) Plotar mapas

Podemos plotar a BHO para visualizar área de estudo rapidamente. Nesse caso, o script `plot_bho.py` criará um png para visualização:

```bash
python3 -m scripts.plot_bho ./cnr_2035/input/BHO_area.gpkg --layer bho_area --area --output ./cnr_2035/output/bho_plot.png
```

**Também podemos plotar interativamente mapas do ISH_LUNC** usando o script `interactive_map.py`:
#### O que o script interactive_maps.py faz

- Lista (recursivamente) arquivos .gpkg no diretório atual, caso você não passe --gpkg.
- Lista camadas do .gpkg e permite escolher uma ou mais camadas.
- Seleciona automaticamente o campo cs_ish (se presente) ou um ire_cs_* disponível; também permite que você escolha outro campo.
- Você pode escolher salvar um mapa estático em png ou um mapa interativo html (Leaflet via folium) com cloropleta usando as cores ISH padrões e as faixas definidas.
- Use a flag --help para entender os parâmetros de entrada permitidos

#### Como rodar o interactive_maps.py

1) Modo interativo (prompt):

```bash
python3 -m scripts.interactive_map
```

2) Gerar apenas o HTML (interativo):
```bash
python3 -m scripts.interactive_map --gpkg /caminho/ish_cenario.gpkg --layers regiao_completa,agg_mun_es --fields "regiao_completa:cs_ish;agg_mun_es:cs_ish"
```

3) Gerar HTML e imagem estática (salva em interactive_maps/preview_<gpkg>.png):
```bash
python3 -m scripts.interactive_map --gpkg /caminho/ish_cenario.gpkg --layers regiao_completa --fields "regiao_completa:cs_ish" --static
```

4) Gerar imagem estática e remover linhas (edge) apenas para a layer regiao_completa:
```bash
python3 -m scripts.interactive_map --gpkg /caminho/ish_cenario.gpkg --layers regiao_completa,agg_mun_es --fields "regiao_completa:all;agg_mun_es:cs_ish" --static --static-no-edges regiao_completa --static-out /tmp/preview.png
```

### 4) Gerar CSVs para análise

Para análises dos valores calculados a geração de CSV pode se útil.
utilize o script `gdf_to_csv.py` que converte um arquivo vetorial (gpkg/shp/geojson/...) para CSV e salva no mesmo diretório.
Uso:
```bash
  python3 scripts/gdf_to_csv.py /caminho/para/arquivo.gpkg
```

Opções:
  --layer LAYER        : nome da layer dentro do GPKG (se aplicável)
  --geom {wkt,centroid,x_y,none} : como incluir geometria no CSV (default: wkt)
  --to-wgs84           : reprojetar para EPSG:4326 antes de extrair centroid/coords
  --overwrite          : sobrescrever CSV de saída se existir
  --encoding ENCODING  : encoding do CSV (default utf-8)

---

## Interpretação da camada de saída do joinISH

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

Se pedir `--agg mean max`, a camada `agg_mun_es` conterá as colunas:
- `cs_ish_mean` = 0.975
- `cs_ish_max` = 2.0

---


## Logs e interpretação rápida

Recomenda-se redirecionar saída e erros para arquivos de log:

```bash
mkdir -p logs
python3 joinISH.py 2035 > logs/joinISH_2035.log 2>&1
python3 -m scripts.aggregate_presentation 2035 ./apresentacao/mun_es.gpkg --id-field fid > logs/aggregate_mun.log 2>&1
```

**O que procurar nos logs**
- `Camadas disponíveis:` — confirma leitura do GPKG de entrada.
- `Preview (head)` — confirma formato e nomes das colunas.
- `Reprojecting presentation layer to input CRS:` — indica reprojeção automática.
- `Computing intersections (this may take time)...` — overlay em andamento.
- `Writing aggregated layer mean_mun_es to ...` — gravação concluída.

**Erros comuns**
- `ModuleNotFoundError: No module named 'geopandas'` → instale o pacote (no caso do exemplo, o geopandas).
- `ValueError: Input layer does not contain 'cs_ish'` → verifique se `joinISH.py` produziu `cs_ish`.

---

## Validação rápida (scripts úteis)

### Verificar CSVs e duplicatas
```python
import pandas as pd
df = pd.read_csv("cnr_2035/input/dim_res_cnr_2035.csv", sep=None, engine="python")
print("total rows:", len(df))
print("unique cobacia:", df['cobacia'].nunique())
print(df['cobacia'].value_counts().head())
```

### Verificar GPKG e camadas
```python
import fiona
print(fiona.listlayers("cnr_2035/output/ish_cnr_2035.gpkg"))
```

---

## Boas práticas e recomendações

- Garanta CSVs limpos (sem duplicatas em `cobacia`) — embora os scripts incluam rotinas de limpeza, é melhor corrigir na origem.
- Se sua maquina tiver espaço, use `conda` para evitar problemas com dependências nativas.
- Faça backup do GPKG antes de rodar operações que sobrescrevem camadas.
- Para conjuntos grandes, execute a interseção em um servidor/VM com memória adequada.
- Trazer os scripts para um ambiente como o Google Colab pode ajudar a compartilhar com outros usuários.

---

## Exemplos de pasta
- Input:
  - `cnr_2035/input/BHO_area.gpkg`
  - `cnr_2035/input/dim_amb_cnr_2035.csv`
  - `cnr_2035/input/dim_hum_cnr_2035.csv`
  - `apresentacao/mun_es.gpkg`
- Output esperados:
  - `cnr_2035/output/ish_cnr_2035.gpkg` (layer `regiao_completa`, `agg_mun_es`, etc.)
  - `cnr_2035/output/interactive_maps/preview_ish_cnr_2035.png` (opcional)

---
