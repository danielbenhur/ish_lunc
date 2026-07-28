import pandas as pd
import yaml
from convertion_functions import *

def main():
    yaml_file_path = "parameters.yaml"
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    dimensions = config['dimensions']
    dataframes = []  # Lista para armazenar todos os DataFrames
    
    # Processar cada arquivo e aplicar as funções
    for dimension in dimensions:
        df = pd.read_csv(dimension['path'], dtype='str')
        # Aplicar as funções específicas para cada dimensão
        for item in dimension['indicadores']:
            nome_funcao = item['name']
            if nome_funcao in globals() and callable(globals()[nome_funcao]):
                funcao = globals()[nome_funcao]
                df[nome_funcao] = funcao(df)
                if(nome_funcao == "fator_de_risco_total"):
                    df.to_csv('arquivo_intermediario.csv')
        
        dataframes.append(df)
        # print(f"Arquivo {dimension['path']} processado. Colunas: {df.columns.tolist()}")
    
    # Fazer merge de todos os DataFrames
    # Assumindo que todos têm uma coluna de identificação comum (ex: 'id', 'municipio', etc.)
    # Você precisa identificar qual é a chave comum entre os arquivos
    
    dados_entregues = dataframes[0]
    for df in dataframes[1:]:
        # Encontre colunas comuns para fazer o merge
        # Ajuste a coluna de merge conforme seus dados
        coluna_chave = 'COBACIA'  # ALTERE PARA A COLUNA QUE É COMUM ENTRE SEUS ARQUIVOS
        dados_entregues = pd.merge(dados_entregues, df, on=coluna_chave, how='outer')

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
        dados_entregues[col] = dados_entregues[col].astype(str).str.replace(',', '.')
        dados_entregues[col] = pd.to_numeric(dados_entregues[col], errors='coerce')
    
    dados_entregues['ire_cs_hum'] = dados_entregues.apply(
        lambda row: ire_cs_hum(
            row['ire_hu_pop'], peso_ire_hu_pop,
            row['ire_hu_cobred'], peso_ire_hu_cobred
        ), axis=1
    )
    # saída registrada em csv
    dados_entregues.to_csv(config['output']['path'])

if __name__ == "__main__":
    main()