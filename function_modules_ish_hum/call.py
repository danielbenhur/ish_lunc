from convertion_functions import *
import sys

dados_string = ['fid', 'COBACIA', 'cod_setor', 'cod_mun']
dtype_dict = {col: str for col in dados_string}

localizacao = './'
tabela_central = pd.read_csv(f'{localizacao}/dim_hum_cnr_fmea.csv', dtype=dtype_dict)
tabela_central.drop(0, inplace=True)
tabela_inicial = tabela_central[tabela_central['COBACIA'].notna() & (tabela_central['COBACIA'] != '')]

dados_entregues = tabela_inicial.copy()

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

functions_to_work = list_functions('scenario.yaml')

for item in functions_to_work:
    funcao = getattr(sys.modules['convertion_functions'], item['indicador']) # chama a função de acordo com o solicitado no yaml
    parametros_colunas = []
    print(item['indicador'])
    for dependencia in item['depends_on']:
        parametros_colunas.append(dados_entregues[dependencia])
    if('column' in item):
        print(f"{item['indicador']} {item['depends_on']}")
        dados_entregues[item['column']] = funcao(parametros_colunas)
        print(dados_entregues[item['column']].head())
    # else:
        # dados_entregues[item['indicador']] = funcao(dependencias)
