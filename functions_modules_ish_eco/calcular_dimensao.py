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
    dados_calculados = pd.DataFrame()

    # lista de funções estabelecidas no YAML de parâmetros
    for dimension in dimensions:
        dados_entregues = pd.read_csv(dimension['path'])
        for item in dimension['indicadores']:
            nome_funcao = item['name']
            if nome_funcao in globals() and callable(globals()[nome_funcao]):
                funcao = globals()[indicador]
                if item['depends_on'] == True:
                    parametros = item['depends_on']
                    resultado = funcao(parametros)
            else:
                resultado = dados_entregues[nome_funcao]
            dados_entregues[nome_funcao] = resultado
        if dados_calculados.empty == True:
            dados_calculados = dados_entregues
        else:
            dados_calculados = pd.merge(
                dados_calculados,
                dados_entregues,
                how='inner',
                on='COBACIA'
            )

    # resultado: ire_cs_eco - resolução provisória: formação da função geral em código dentro da main
    pesos = {}
    for item in config['result']:
        if item['name'] == 'ire_cs_eco':
            for dep in item['depends_on']:
                pesos[dep['name']] = dep['peso']

    print(pesos)
    peso_ind  = float(pesos['ire_cs_ind_eco'])
    peso_irri = float(pesos['ire_cs_irri_eco'])
    peso_pec  = float(pesos['ire_cs_pec_eco'])
    # Antes de aplicar a função, converta as colunas
    print(dados_calculados.head())
    colunas_numericas = ['ire_cs_ind_eco', 'ire_cs_irri_eco', 'ire_cs_pec_eco']
    for col in colunas_numericas:
        dados_calculados[col] = dados_calculados[col].astype(str).str.replace(',', '.')
        dados_calculados[col] = pd.to_numeric(dados_calculados[col], errors='coerce')
    
    dados_calculados['ire_cs_eco'] = dados_calculados.apply(
        lambda row: ire_cs_eco(
            row['ire_cs_ind_eco'], peso_ind,
            row['ire_cs_irri_eco'], peso_irri,
            row['ire_cs_pec_eco'], peso_pec
        ), axis=1
    )

    # saída registrada em csv
    dados_calculados.to_csv(config['output']['path'])
    print(dados_calculados.head())
    
if __name__ == "__main__":
    main()
