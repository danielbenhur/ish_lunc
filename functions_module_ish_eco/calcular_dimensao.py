import pandas as pd
import yaml
from convertion_functions import *

def main():
    yaml_file_path = "parameters.yaml"
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    dimensions = config['dimensions']
    dados_gerais = pd.read_csv('arquivo_intermediario.csv', dtype='str')

    # Processar cada arquivo e aplicar as funções
    for dimension in dimensions:
        df = pd.read_csv(dimension['path'], dtype='str')
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
            if(nome_funcao == '')
            if nome_funcao in globals() and callable(globals()[nome_funcao]):
                funcao = globals()[nome_funcao]
                # entregando a coluna aos dados finais
                dados_gerais[nome_funcao] = funcao(dados_gerais)

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