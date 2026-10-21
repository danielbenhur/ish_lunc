import pandas as pd
import yaml
from convertion_functions import *

def functions_module_ish_hum(yaml_file_path):
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    dimensions = config['dimensions']
    dados_gerais = pd.DataFrame()
    
    # Processar cada arquivo e aplicar as funções
    for dimension in dimensions:
        # print(dimension)
        df = pd.read_csv(dimension['path'], dtype='str')
        if dados_gerais.empty:
            dados_gerais = df
        
        else:
            # verifica como juntar com um DataFrame geral
            chave = None
            for possible_key in ['cobacia', 'cod_mun']:
                if possible_key in df.columns:
                    chave = possible_key
                    break

            if chave is None:
                print(f"  ⚠️ Sem chave! Pulando...")
                continue
            df = df.dropna(subset=[chave])
        
            # CRIA UM DICIONÁRIO DE MAPPING (chave -> primeiro valor)
            mapping = {}
            for col in df.columns:
                if col != chave:
                    mapping[col] = df.drop_duplicates(subset=[chave], keep='first').set_index(chave)[col].to_dict()
        
            # Aplica o mapping à base (sem multiplicar!)
            for col in mapping:
                if col not in dados_gerais.columns:
                    dados_gerais[col] = dados_gerais[chave].map(mapping[col])
                    # print(f"  Adicionada coluna: {col}")
        
        # 🔥 PRIMEIRO: Aplicar as funções específicas para cada dimensão
        for item in dimension['indicadores']:
            nome_funcao = item['name']
            # print(f"Aplicando função: {nome_funcao}")
            if nome_funcao in globals() and callable(globals()[nome_funcao]):
                funcao = globals()[nome_funcao]
                # entregando a coluna aos dados finais
                # aplicando peso diferentes do padrão já pré-estabelecido na função
                if 'pesos' in item:
                    pesos = item['pesos']
                    dados_gerais[nome_funcao] = funcao(dados_gerais, pesos=pesos)
                else:
                    dados_gerais[nome_funcao] = funcao(dados_gerais)
                # print(f"  ✅ Coluna criada: {nome_funcao}")
            else:
                print(f"  ⚠️ Função '{nome_funcao}' não encontrada!")

    dados_gerais.to_csv(config['intermediario'], index=False)    
    
    dados_resultado = dados_gerais[['cobacia', 'ire_cs_hum']]
    dados_resultado.to_csv(config['output']['path'], index=False)
    dados_gerais.to_csv(config['intermediario'])
    print(f"✅ Resultado salvo em: {config['output']['path']}")
    # print(dados_resultado.head)

if __name__ == "__main__":
    functions_module_ish_hum("/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_hum/parameters.yaml")