import pandas as pd
import yaml
from convertion_functions import *

def main():
    yaml_file_path = "parameters.yaml"
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Aqui usaremos as funções de convertion_functions.py para calcular as dimensões
    dimensions = config['dimensions']
    parametros = []

    functions_to_work = []
    for dimensao in dimensions:
        functions_to_work.extend(list_functions(dimensao))

    dados_calculados = pd.DataFrame()
    resultado = None # correção de chamada de variável local antes de atribuição
    i = 0
    # lista de funções estabelecidas no YAML de parâmetros
    for dimension in dimensions:
        dados_entregues = pd.read_csv(dimension['path'])
        for item in dimension['indicadores']:
            nome_funcao = item['name']
            if nome_funcao in globals() and callable(globals()[nome_funcao]):
                funcao = globals()[nome_funcao]
                dados_entregues[nome_funcao] = funcao(dados_entregues)
                i+= 1

            

    # resultado: ire_cs_hum - resolução provisória: formação da função geral em código dentro da main
    pesos = {}
    for item in config['result']:
        if item['name'] == 'ire_cs_hum':
            for dep in item['depends_on']:
                pesos[dep['name']] = dep['peso']

    peso_ire_hu_pop  = float(pesos['ire_hu_pop'])
    peso_ire_hu_cobred = float(pesos['ire_hu_cobred'])

    colunas_numericas = ['ire_hu_pop', 'ire_hu_cobred']
    for col in colunas_numericas:
        dados_calculados[col] = dados_calculados[col].astype(str).str.replace(',', '.')
        dados_calculados[col] = pd.to_numeric(dados_calculados[col], errors='coerce')
    
    dados_calculados['ire_cs_hum'] = dados_calculados.apply(
        lambda row: ire_cs_hum(
            row['ire_hu_pop'], peso_ire_hu_pop,
            row['ire_hu_cobred'], peso_ire_hu_cobred
        ), axis=1
    )
    # saída registrada em csv
    dados_calculados.to_csv(config['output']['path'])
    print(dados_calculados.head())

if __name__ == "__main__":
    main()