import pandas as pd
import yaml
from convertion_functions import *

def functions_module_ish_hum():
    yaml_file_path = "/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_hum/parameters.yaml"
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
            for possible_key in ['COBACIA', 'cod_mun']:
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
    # 🔥 SEGUNDO: Verifica se as colunas existem antes de processar
    # print("\nColunas disponíveis após processamento:", dados_gerais.columns.tolist())
    
    # Processar pesos e calcular ire_cs_hum
    pesos = {}
    for item in config['result']:
        if item['name'] == 'ire_cs_hum':
            for dep in item['depends_on']:
                pesos[dep['name']] = dep['peso']
    
    # Verifica se as colunas necessárias existem
    colunas_necessarias = ['ire_hu_pop', 'ire_hu_cobred']
    colunas_faltando = [col for col in colunas_necessarias if col not in dados_gerais.columns]
    
    if colunas_faltando:
        # print(f"⚠️ Colunas faltando: {colunas_faltando}")
        # print(f"Colunas disponíveis: {dados_gerais.columns.tolist()}")
        # Pode optar por criar colunas com valores padrão ou interromper
        for col in colunas_faltando:
            # print(f"Criando coluna '{col}' com valores padrão (0)")
            dados_gerais[col] = 0
    
    # Agora processa as colunas numéricas
    for col in colunas_necessarias:
        if col in dados_gerais.columns:
            dados_gerais[col] = dados_gerais[col].astype(str).str.replace(',', '.')
            dados_gerais[col] = pd.to_numeric(dados_gerais[col], errors='coerce')
    
    # Verifica se os pesos existem
    if 'ire_hu_pop' not in pesos or 'ire_hu_cobred' not in pesos:
        print(f"⚠️ Pesos não encontrados! Pesos disponíveis: {pesos}")
        # Define pesos padrão se necessário
        peso_ire_hu_pop = float(pesos.get('ire_hu_pop', 0.5))
        peso_ire_hu_cobred = float(pesos.get('ire_hu_cobred', 0.5))
    else:
        peso_ire_hu_pop = float(pesos['ire_hu_pop'])
        peso_ire_hu_cobred = float(pesos['ire_hu_cobred'])
    
    # Calcula ire_cs_hum
    dados_gerais['ire_cs_hum'] = dados_gerais.apply(
        lambda row: ire_cs_hum(
            row['ire_hu_pop'], peso_ire_hu_pop,
            row['ire_hu_cobred'], peso_ire_hu_cobred
        ), axis=1
    )
    
    dados_resultado = dados_gerais[['COBACIA', 'ire_cs_hum']]
    dados_resultado.to_csv(config['output']['path'], index=False)
    dados_gerais.to_csv(config['intermediario'])
    print(f"✅ Resultado salvo em: {config['output']['path']}")
    # print(dados_resultado.head)

if __name__ == "__main__":
    functions_module_ish_hum()