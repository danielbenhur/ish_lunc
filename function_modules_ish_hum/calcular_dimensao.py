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
    print(functions_to_work)

    dados_calculados = pd.DataFrame()
    
    # lista de funções estabelecidas no YAML de parâmetros
    for dimension in dimensions:
        dados_entregues = pd.read_csv(dimension['path'])
        for item in dimension['indicadores']:
            nome_funcao = item['indicador']
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


# tabela_central = pd.read_csv(f'dim_hum_cnr_fmea.csv', dtype=dtype_dict)
# tabela_central.drop(0, inplace=True)
# tabela_inicial = tabela_central[tabela_central['COBACIA'].notna() & (tabela_central['COBACIA'] != '')]
# 
# dados_entregues = tabela_inicial.copy()
# dados_entregues = dados_entregues.loc[:, :'bal_perc']
# 
# for col in dados_entregues.columns:
    # if col not in dados_string and dados_entregues[col].dtype == 'object':
        # tenta converter para número
        # try:
            # dados_entregues[col] = (
                # dados_entregues[col]
                # .str.replace('.', '', regex=False)      # remove ponto de milhar
                # .str.replace(',', '.', regex=False)     # troca vírgula decimal por ponto
                # .astype(float)
            # )
            # dados_entregues[col] = pd.to_numeric(dados_entregues[col], errors='coerce').fillna(0)
        # except (AttributeError, ValueError, TypeError):
            # se falhar, mantém coluna original
            # pass
# 
# for item in functions_to_work:
    # funcao = globals()[item['indicador']]
    # parametros_colunas = []
    # print(item['indicador'])
    # for dependencia in item['depends_on']:
        # quando não estiver no dataframe, será número
        # não está bom, muito menos robusto
        # if dependencia in dados_entregues:
            # parametros_colunas.append(dados_entregues[dependencia])
        # else:
            # coluna_constante = pd.Series([dependencia] * len(df), index=df.index)
            # parametros_colunas.append(coluna_constante)
    # 
    # if('column' in item):
        # print(f"{item['indicador']} {item['depends_on']}")
        # dados_entregues[item['column']] = funcao(parametros_colunas)
    # else:
        # dados_entregues[item['indicador']] = funcao(parametros_colunas)
# 
# Criar uma cópia do DataFrame com os números formatados como string brasileira
# df_export = dados_entregues.copy()
# 
# Converter todas as colunas numéricas para formato brasileiro
# for col in df_export.select_dtypes(include=['float64', 'int64']).columns:
    # df_export[col] = df_export[col].apply(lambda x: f"{x}".replace('.', ','))
# 
# Salvar como CSV
# df_export.to_csv('arquivo_br.csv', index=False, encoding='utf-8-sig')
# 
# tabela_inicial.to_csv('tabela_inicial.csv')
# 