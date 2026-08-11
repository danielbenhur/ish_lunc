import pandas as pd
import yaml
from convertion_functions import *

def main():
    yaml_file_path = "/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_hum/parameters.yaml"
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    dimensions = config['dimensions']
    dados_gerais = pd.DataFrame()
    # Processar cada arquivo e aplicar as funções
    for dimension in dimensions:
        print(dimension['name'])
        df = pd.read_csv(dimension['path'], dtype='str')
        if dados_gerais.empty:
            dados_gerais = df
            continue
        # verifica como juntar com um DataFrame geral
        chave = None
        for possible_key in ['COBACIA', 'cod_mun']:
            if possible_key in df.columns:
                chave = possible_key
                break
        
        if chave is None:
            print(f"  ⚠️ Sem chave! Pulando...")
            continue
        df = df.dropna(subset=[chave])
        # 🔥 CRIA UM DICIONÁRIO DE MAPPING (chave -> primeiro valor)
        # Isso garante que cada chave tenha APENAS UM valor
        mapping = {}
        for col in df.columns:
            if col != chave:
                # Pega o primeiro valor para cada chave
                mapping[col] = df.drop_duplicates(subset=[chave], keep='first').set_index(chave)[col].to_dict()
        
        # Aplica o mapping à base (sem multiplicar!)
        for col in mapping:
            if col not in dados_gerais.columns:
                dados_gerais[col] = dados_gerais[chave].map(mapping[col])
                print(f"  Adicionada coluna: {col}")
        
        # Aplicar as funções específicas para cada dimensão
        for item in dimension['indicadores']:
            nome_funcao = item['name']
            print(nome_funcao)
            if nome_funcao in globals() and callable(globals()[nome_funcao]):
                funcao = globals()[nome_funcao]
                # entregando a coluna aos dados finais
                dados_gerais[nome_funcao] = funcao(dados_gerais)

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
        dados_gerais[col] = dados_gerais[col].astype(str).str.replace(',', '.')
        dados_gerais[col] = pd.to_numeric(dados_gerais[col], errors='coerce')
    
    dados_gerais['ire_cs_hum'] = dados_gerais.apply(
        lambda row: ire_cs_hum(
            row['ire_hu_pop'], peso_ire_hu_pop,
            row['ire_hu_cobred'], peso_ire_hu_cobred
        ), axis=1
    )

    dados_resultado = dados_gerais[['ire_cs_hum']]
    # saída registrada em csv
    dados_resultado.to_csv(config['output']['path'])

if __name__ == "__main__":
    main()