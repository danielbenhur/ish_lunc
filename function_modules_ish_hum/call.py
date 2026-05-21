from convertion_functions import *
import sys

dados_string = ['fid', 'COBACIA', 'cod_setor', 'cod_mun']
dtype_dict = {col: str for col in dados_string}

yaml_file_path = 'scenario.yaml'
with open(yaml_file_path, 'r') as file:
    config = yaml.safe_load(file)
dimensions = config['dimensions']

functions_to_work = []
for dimensao in dimensions:
    functions_to_work.extend(list_functions(dimensao))
print(functions_to_work)


tabela_central = pd.read_csv(f'dim_hum_cnr_fmea.csv', dtype=dtype_dict)
tabela_central.drop(0, inplace=True)
tabela_inicial = tabela_central[tabela_central['COBACIA'].notna() & (tabela_central['COBACIA'] != '')]

dados_entregues = tabela_inicial.copy()
dados_entregues = dados_entregues.loc[:, :'bal_perc']

for col in dados_entregues.columns:
    if col not in dados_string and dados_entregues[col].dtype == 'object':
        # tenta converter para número
        try:
            dados_entregues[col] = (
                dados_entregues[col]
                .str.replace('.', '', regex=False)      # remove ponto de milhar
                .str.replace(',', '.', regex=False)     # troca vírgula decimal por ponto
                .astype(float)
            )
            dados_entregues[col] = pd.to_numeric(dados_entregues[col], errors='coerce').fillna(0)
        except (AttributeError, ValueError, TypeError):
            # se falhar, mantém coluna original
            pass

for item in functions_to_work:
    funcao = globals()[item['indicador']]
    parametros_colunas = []
    print(item['indicador'])
    for dependencia in item['depends_on']:
        # quando não estiver no dataframe, será número
        # não está bom, muito menos robusto
        if dependencia in dados_entregues:
            parametros_colunas.append(dados_entregues[dependencia])
        else:
            coluna_constante = pd.Series([dependencia] * len(df), index=df.index)
            parametros_colunas.append()
    
    if('column' in item):
        print(f"{item['indicador']} {item['depends_on']}")
        dados_entregues[item['column']] = funcao(parametros_colunas)
    else:
        dados_entregues[item['indicador']] = funcao(parametros_colunas)

# Criar uma cópia do DataFrame com os números formatados como string brasileira
df_export = dados_entregues.copy()

# Converter todas as colunas numéricas para formato brasileiro
for col in df_export.select_dtypes(include=['float64', 'int64']).columns:
    df_export[col] = df_export[col].apply(lambda x: f"{x}".replace('.', ','))

# Salvar como CSV
df_export.to_csv('arquivo_br.csv', index=False, encoding='utf-8-sig')

tabela_inicial.to_csv('tabela_inicial.csv')
