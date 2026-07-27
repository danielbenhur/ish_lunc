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
        df = pd.read_csv(dimension['path'])
        
        # Aplicar as funções específicas para cada dimensão
        for item in dimension['indicadores']:
            nome_funcao = item['name']
            if nome_funcao in globals() and callable(globals()[nome_funcao]):
                funcao = globals()[nome_funcao]
                df[nome_funcao] = funcao(df)
        
        dataframes.append(df)
        print(f"Arquivo {dimension['path']} processado. Colunas: {df.columns.tolist()}")
    
    # Fazer merge de todos os DataFrames
    # Assumindo que todos têm uma coluna de identificação comum (ex: 'id', 'municipio', etc.)
    # Você precisa identificar qual é a chave comum entre os arquivos
    
    # Exemplo 1: Se todos têm a mesma coluna 'id' como chave
    dados_entregues = dataframes[0]
    for df in dataframes[1:]:
        # Encontre colunas comuns para fazer o merge
        # Ajuste a coluna de merge conforme seus dados
        coluna_chave = 'COBACIA'  # ALTERE PARA A COLUNA QUE É COMUM ENTRE SEUS ARQUIVOS
        dados_entregues = pd.merge(dados_entregues, df, on=coluna_chave, how='outer')
    
    # Exemplo 2: Se não há uma chave comum e os DataFrames têm a mesma estrutura
    # (mesmas linhas na mesma ordem)
    # dados_entregues = pd.concat(dataframes, axis=1)
    
    print(f"\nDataFrame final - Colunas: {dados_entregues.columns.tolist()}")
    print(f"DataFrame final - Shape: {dados_entregues.shape}")
    
    # Verificar se as colunas necessárias existem
    colunas_necessarias = ['ire_cs_ind_eco', 'ire_cs_irri_eco', 'ire_cs_pec_eco']
    colunas_faltando = [col for col in colunas_necessarias if col not in dados_entregues.columns]
    
    if colunas_faltando:
        print(f"ERRO: Colunas faltando: {colunas_faltando}")
        print("Colunas disponíveis:", dados_entregues.columns.tolist())
        return
    
    # Continuar com o processamento...
    pesos = {}
    for item in config['result']:
        if item['name'] == 'ire_cs_eco':
            for dep in item['depends_on']:
                pesos[dep['name']] = dep['peso']
    
    print(f"Pesos carregados: {pesos}")
    
    peso_ind = float(pesos['ire_cs_ind_eco'])
    peso_irri = float(pesos['ire_cs_irri_eco'])
    peso_pec = float(pesos['ire_cs_pec_eco'])
    
    # Converter colunas para numérico
    colunas_numericas = ['ire_cs_ind_eco', 'ire_cs_irri_eco', 'ire_cs_pec_eco']
    for col in colunas_numericas:
        dados_entregues[col] = dados_entregues[col].astype(str).str.replace(',', '.')
        dados_entregues[col] = pd.to_numeric(dados_entregues[col], errors='coerce')
    
    # Aplicar função de cálculo do resultado final
    dados_entregues['ire_cs_eco'] = dados_entregues.apply(
        lambda row: ire_cs_eco(
            row['ire_cs_ind_eco'], peso_ind,
            row['ire_cs_irri_eco'], peso_irri,
            row['ire_cs_pec_eco'], peso_pec
        ), axis=1
    )
    
    # Salvar resultado
    dados_entregues.to_csv(config['output']['path'], index=False)
    print(f"\nResultado salvo em: {config['output']['path']}")
    print(dados_entregues.head())
    
if __name__ == "__main__":
    main()