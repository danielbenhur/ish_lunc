# ISH_LUNC - COMO USAR O MODELO MULTI-DIMENSIONAL DE GERAÇÃO DE MAPAS A PARTIR DE DADOS

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