import pandas as pd
import yaml
from convertion_functions import *

def main():
    yaml_file_path = "parameters.yaml"
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    dimensions = config['dimensions']
    dados_entregues = pd.read_csv('arquivo_intermediario.csv', dtype='str')

    # Processar cada arquivo e aplicar as funções
    for dimension in dimensions:
        df = pd.read_csv(dimension['path'], dtype='str')
        
        # Aplicar as funções específicas para cada dimensão
        for item in dimension['indicadores']:
            nome_funcao = item['name']
            if nome_funcao in globals() and callable(globals()[nome_funcao]):
                funcao = globals()[nome_funcao]
                # entregando a coluna aos dados finais
                coluna_resultado = funcao(df)
                if 'COBACIA' in df.columns:
                    chave = 'COBACIA'
                    resultado_temp = pd.DataFrame({
                        chave: df[chave],
                        nome_funcao: coluna_resultado
                    })
                else:
                    chave = 'cod_mun'
                    resultado_temp = pd.DataFrame({
                        chave: df[chave],
                        nome_funcao: coluna_resultado
                    })
                resultado_temp = resultado_temp.drop_duplicates(subset=[chave])

                if chave in dados_entregues.columns:
                    dados_entregues = pd.merge(dados_entregues, 
                                            resultado_temp, 
                                            on=chave, 
                                            how='left')
                #  Verificar se não houve duplicação indesejada
                if dados_entregues.duplicated().any():
                    print(f"Aviso: Duplicatas detectadas após merge de {nome_funcao}")
                    dados_entregues = dados_entregues.drop_duplicates()
                
                if nome_funcao == 'deman_irri':
                    print(dados_entregues.head())
                    exit(1) 
    
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