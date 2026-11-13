# ISH_LUNC - README

Este repositório contém scripts com finalidade principal de calcular o **Índice de Segurança Hídrica LabGest-UFES/Neades-CPID (ISH_LUNC)** por ottobacias e agregar/visualizar esses resultados em unidades de apresentação (municípios, estados, regiões etc.). O projeto engloba como padrão as funções na dimensão humana, presentes na pasta functions_module_ish_hum; depois da aplicação das funções nos dados de entrada, usa-se um código para unificar os dados apresentáveis: o joinISH; com isso, o código junta os arquivos em um geopackage (.gpkg) e é possível visualizar o mapa final com as dimensões presentes. O script motorCalculo.py roda o código em cada pasta de dimensão e o joinISH ao final.

![Fluxograma do ISH-LUNC](./ISH-LUNC_fluxograma.svg)

## **Veja o modelo aplicado:** [AdaptaES](https://adaptaes.incaper.es.gov.br/ish)

## **Arquitetura**
```
ISH_LUNC/
├─ joinISH.py                   # script que junta csv's calculados em um arquivo .gpkg para funcionalidade de mapa em GIS
├─ motorCalculo.py              # script que faz as contas em cada dimensão específica e depois roda o joinISH.py
├─ requirements.txt             # pacotes requeridos no projeto
├─ dados_gerais/                # pasta com dados comuns a todas as dimensões (dataframe completo gerado pela função humana armazenado em arquivo .csv)
├─ output/                      # pasta onde ficam os resultados de joinISH.py
├─ functions_module_ish_*/      # padrão de pasta para cálculos de cada dimensão (a dimensão humana é o padrão; o padrão é functions_module_ish_hum)
|   ├─ input/                   # pasta com dados para serem base para o motor de Cálculo
|   ├─ output/                  # pasta da saída do valor final da dimensão feito pelo motor de Cálculo 
|   ├─ calcular_dimensao.py     # motor de Cálculo propriamente dito na pasta
|   ├─ convertion_functions.py  # biblioteca de funções utilizadas
|   ├─ comparar.py              # arquivo para comparar valores calculados e valores padronizados calculados anteriormente
├─ Metodologia_ISH_ANA.pdf      # origem teórica de medidas tomadas pela ANA
├─ Metodologia_ISH-LUNC.md      # origem teórica de medidas tomadas no projeto
├─ ISH-LUNC_fluxograma.svg      # imagem do fluxograma de funcionamento previsto para o projeto - TODO
└─ apresentacao/                # Pasta com geodataframes utilizados para gerar valores agregados por regiões
   └─ *.gpkg                    # Importante ser do tipo gpkg
```

---
## **Guia de Uso**
1. Estrutura de Pastas para funcionamento

├─  dados_gerais
|   ├─ arquivo_intermediario.csv
|
├─  functions_module_ish_eco
|   ├─ output
|   |   ├─ ish_eco.csv
|   ├─ input
|   |   ├─ PAM - ES - demanda.csv
|   |   ├─ PPM - ES - demanda.csv
|   |   ├─ Indicador Industria - Bernardo - demanda.csv
|   |   ├─ PAM - ES - Producao irrigada .csv
|   |   ├─ PPM - ES - PPM.csv
|   |   ├─ Indicador Industria - Bernardo - Ind_sc_otto.csv
|   ├─  calcular_dimensao.py
|   ├─  convertion_functions.py
|   ├─  parameters.yaml
|
├─  functions_module_ish_hum
|   ├─ output
|   |   ├─ ish_hum.csv
|   ├─ input
|   |   ├─ dimensao_humana.csv
|   ├─  calcular_dimensao.py
|   ├─  convertion_functions.py
|   ├─  parameters.yaml
|
├─  motorCalculo.py
├─  joinISH.py
├─  parameters.yaml
├─  BHO_area.gpkg
|
├─  output
|   ├─ resultado.csv
|   ├─ resultado.gpkg

2. Explicação de cada arquivo programado
O arquivo central para operação das contas como um todo estão em cada pasta de dimensão; cada subpasta que começa em "functions_module_ish_" deve ter as entradas definitivas de como a dimensão deve ser trabalhada; a partir de uma planilha formatada, o usuário consegue fazer as contas com o script "calcular_dimensao.py", que vai usar as funções da biblioteca de funções específicas de cada dimensão para chegar em alguma conclusão. Para escolher as funções que serão usadas, tem um arquivo "parameters.yaml", que tem detalhado como cada coluna de uma tabela será trabalhada (seja com pesos específicos, valores setados e os parâmetros de cada função utilizada na biblioteca; as colunas originais que eram feitas em Excel agora são funções próprias do código).

No momento, apenas a dimensão humana está pronta nesse propósito, mas o formato pode ser usado para as outras dimensões também.

O joinISH junta os resultados de todas as "calcular_dimensao.py" das subpastas anteriores; isso é uma convenção: o dado visto no script joinISH pode estar em qualquer lugar do computador, desde que selecionado na formatação devida e em alguma pasta indicada pelo "parameters.yaml" da pasta geral. Cada dimensão tem um campo específico nesse arquivo de configuração e a partir disso o usuário decide de onde vai ser extraída a coluna de cada dimensão para a conta final do mapa. Isso, no entanto, não significa que a padronização não é relevante: às vezes a escolha do lugar da pasta pode não ser um ponto de atenção do usuário e mesmo refazendo as contas ele pode esquecer do local onde seus resultados estão indo. Por isso, é bom colocar a padronização em cada dimensão do arquivo resultado das contas (mesmo que ele seja entrada do joinISH).

Por fim, o script motorCalculo.py roda cada dimensão e junta com a execução do joinISH; tudo pode ser rodado sozinho (as dimensões individualmente e o joinISH separadamente), mas o motorCalculo.py junta as duas coisas para melhorar o fluxo de simulações.

Execução (na pasta principal): 
python3 motorCalculo.py

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

1. [Pré-requisitos](#pré-requisitos)  
- Arquivo de mapa .gpkg (serve para bho)
- Pastas com os dados necessários para cada dimensão analisada
- pandas, numpy, geopandas e fiona instalados na máquina


2. [Formatos de entrada](#formatos-de-entrada)  
- Entradas de arquivos e dados feitas nos arquivos parameters.yaml
- Arquivos .gpkg e .csv indicados pela localização a ser procurada pelo usuário

3. [Formatos de saída](#formatos-de-saída) 
- Pastas output em cada pasta de domínio
- Saída de arquivo intermediário (com todos os dados) na pasta dados_gerais
- Pasta getal de output para recebimento do mapa com as colunas especificadas no respectivo parameters.yaml

4. [Como rodar os scripts (Exemplos)](#como-rodar-os-scripts-exemplos)  
- Para configurações gerais:
python3 motorCalculo.py

- Para configurações dimensionais específicas:
python3 ./functions_module_ish_hum/calcular_dimensao.py

5. [Interpretação da camada de saída do joinISH](#interpretação-da-camada-de-saída-do-joinish)
- Arquivo com o mapa completo e o conjunto de colunas de diferentes fontes

6. [Exemplo prático (numérico)](#exemplo-prático-numérico)
7. [Logs e interpretação rápida](#logs-e-interpretação-rápida)  

8. [Validação rápida (scripts úteis)](#validação-rápida-scripts-úteis)
- Uso do script "comparar.py", presente em cada subpasta, para verificação se o padrão sugerido existe

9. [Boas práticas e recomendações](#boas-práticas-e-recomendações)  
- Deixar as dimensões todas no mesmo formato e alterando apenas o nome de alguns arquivo
- Colocar as fontes de dados em um lugar que o usuário pode se lembrar depois
- Não criar colunas novas nos arquivos de fonte 
- Formate as tabelas para se adequarem ao formato exigido com os devidos nomes das fontes colocadas no arquivo .yaml de parâmetros

10. [Exemplos de estrutura da pasta final](#exemplos-de-estrutura-da-pasta-final)  
# interpretação geral (faz sentido estarem na mesma pasta)
- motorCalculo.py
- parameters.yaml
- input/
   - mapa_padrao.gpkg
- output/
   - mapa_gerado.csv
   - mapa_gerado.gpkg

# pastas das dimensões (são inputs do resultado final, mas precisam de inputs próprios)
- functions_module_ish_hum/*
- functions_module_ish_eco/*
