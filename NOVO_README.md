# ISH_LUNC - README

Este repositório contém scripts com finalidade principal de calcular o **Índice de Segurança Hídrica LabGest-UFES/Neades-CPID (ISH_LUNC)** por ottobacias e agregar/visualizar esses resultados em unidades de apresentação (municípios, estados, regiões etc.). O projeto engloba como padrão as funções na dimensão humana, presentes na pasta functions_module_ish_hum; depois dos cálculos puxados pelo motorCalculo.py, usa-se o joinISH.py para gerar um gpkg para formar os mapas verificáveis em GIS.

![Fluxograma do ISH-LUNC](./ISH-LUNC_fluxograma.svg)

## **Veja o modelo aplicado:** [AdaptaES](https://adaptaes.incaper.es.gov.br/ish)

## **Arquitetura**
```
ISH_LUNC/
├─ joinISH.py                   # script que junta csv's calculados em um arquivo .gpkg para funcionalidade de mapa em GIS
├─ motorCalculo.py              # script que roda os códigos internos das pastas de dimensões para calcular os componentes de ISH
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
O arquivo central para operação das contas como um todo é o "motorCalculo.py", que será o arquivo utilizado para gerar os dados coerentemente com o que precisa ser calculado em cada dimensão; utilizando a estrutura correta, em que cada dimensão tem sua própria pasta, esse arquivo irá executar os arquivos próprios internamente para gerar os dados necessários; ele lerá a lista de dimensões a serem calculadas de acordo com o arquivo de configuração "parameters.yaml" na mesma pasta que ele.

As subpastas (neste exemplo ainda são functions_module_ish_hum e functions_module_ish_eco), referentes a cada dimensão do modelo terão duas subpastas próprias: input e output; input é onde estão os arquivos csv que serão usados para calcular os dados e output onde está o resultado final da execução do arquivo "calcular_dimensao.py", que usa o arquivo de configuração próprio da mesma subpasta chamado "parameters.yaml". A biblioteca de funções para esse arquivo executado é "convertion_functions.py", onde está a lógica central de cada função que anteriormente era calculada em Excel. A elaboração dessas funções deve ter o nome especificado e igual tanto na biblioteca como no arquivo de configuração. A adequação de pesos ocorre no arquivo de configuração, cabendo ao usuário decidir como os pesos serão utilizados. A escolha de valores de pesos deve ter a mesma ordem das colunas que estão sendo trabalhadas em cada função.

Considerando a similaridade e uso comum de diferentes colunas na mesma execução entre dimensões diferentes, tem uma pasta específica chamada "dados_gerais", que irá ter um arquivo em csv nomeado "arquivo_intermediario.csv", que conterá todas as colunas; a ordem como as dimensões são chamadas é importante, sendo necessário sempre começar pela humana já que os dados dessa dimensão vão ser usadas pelas outras e para os cálculos gerais

Por fim, o "joinISH.py" tem o papel de extrair os dados presentes em cada subpasta output, unir tudo em um único DataFrame e fazer uma junção com a tabela GPKG em "BHO_area.gpkg", sendo responsável por extrair os dados gerais de cada dimensão e tirar uma média de todas elas, tendo seu resultado presente na subpasta escolhida no "parameters.yaml" geral e possível averiguação do mapa no QGIS.

Execução (na pasta principal): 
python3 motorCalculo.py
python3 joinISH.py

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