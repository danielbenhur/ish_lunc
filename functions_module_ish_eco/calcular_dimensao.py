import pandas as pd
import yaml
from convertion_functions import *

def functions_module_ish_eco():
    yaml_file_path = "/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_eco/parameters.yaml"
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    dimensions = config['dimensions']
    dados_gerais = pd.read_csv(config['intermediario'], dtype='str')
    
    # Processar cada arquivo e aplicar as funções
    for dimension in dimensions:
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
        
        # Aplicar as funções específicas para cada dimensão
        for item in dimension['indicadores']:
            nome_funcao = item['name']
            # Verifica se a função existe
            if nome_funcao in globals() and callable(globals()[nome_funcao]):
                funcao = globals()[nome_funcao]
                try:
                    # Executa a função aplicando pesos se necessário
                    if 'pesos' in item:
                        pesos = item['pesos']
                        resultado = funcao(dados_gerais, pesos=pesos)
                    else:
                        resultado = funcao(dados_gerais)
                    
                    # Verifica se retornou algo
                    if resultado is not None:
                        dados_gerais[nome_funcao] = resultado
                    else:
                        print(f"    ⚠️ Função '{nome_funcao}' retornou None!")
                        
                except Exception as e:
                    print(f"    ❌ Erro ao executar '{nome_funcao}': {e}")
            else:
                print(f"    ❌ Função '{nome_funcao}' não encontrada no escopo global!")
                print(f"    Funções disponíveis: {[f for f in dir() if callable(globals().get(f)) and not f.startswith('_')]}")
    
    colunas_necessarias = ['ire_cs_ind_eco', 'ire_cs_irri_eco', 'ire_cs_pec_eco']
    colunas_faltando = [col for col in colunas_necessarias if col not in dados_gerais.columns]
    
    if colunas_faltando:
        print(f"ERRO: Colunas faltando: {colunas_faltando}")
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
        dados_gerais[col] = dados_gerais[col].astype(str).str.replace(',', '.')
        dados_gerais[col] = pd.to_numeric(dados_gerais[col], errors='coerce')
    
    # Aplicar função de cálculo do resultado final
    dados_gerais['ire_cs_eco'] = dados_gerais.apply(
        lambda row: ire_cs_eco(
            row['ire_cs_ind_eco'], peso_ind,
            row['ire_cs_irri_eco'], peso_irri,
            row['ire_cs_pec_eco'], peso_pec
        ), axis=1
    )
    
    dados_resultado = dados_gerais[['COBACIA','ire_cs_ind_eco', 'ire_cs_irri_eco', 'ire_cs_pec_eco', 'ire_cs_eco']]

    # Salvar resultado
    dados_resultado.to_csv(config['output']['path'], index=False)
    dados_gerais.to_csv(config['intermediario'])
    print(f"✅Resultado salvo em: {config['output']['path']}")
    print(dados_resultado.head)

if __name__ == "__main__":
    functions_module_ish_eco()