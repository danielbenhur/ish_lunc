import pandas as pd
import geopandas as gpd
import numpy as np

# campos: 
# A: fid (identificador único de registro)
# B: código de ottobacia (COBACIA)
# C: setor censitário
# D: tipo de setor
# E: código de município
# F: nome do município
# G: unidade da federação
# H: situação do setor censitário


# I: disponibilidade hídrica associada à vazão Q95
# J: demanda hídrica anual (dem_ret_ano),
# K: demanda acumulada (dem_acm)


# L: balanço hídrico percentual (bal_perc; demanda/disponibilidade); M, disponibilidade/demanda; 
# N, fator de risco iminente, (1/3)*(M3)^SE(M3>=1;-2;1); 
# O: Fator pós déficit: = SE(M3 >=1;0;1 - (M3))
# P: Fator de risco Total: = O3+N3

# Q: população total do município projetada para o ano de 2020
# R: população urbana do município, também projetada para 2020
# S: população rural do município

# T: percentual da população em risco inerente no município, sendo calculada a partir da razão entre o número de habitantes em risco inerente e a população urbana total
# U: o valor absoluto da população em risco inerente (coluna W) é obtido multiplicando-se a população urbana (coluna R) pelo fator de risco iminente previamente calculado
# V: esse valor é dividido pela população urbana, resultando no percentual correspondente
# W: o percentual da população em risco pós-déficit, utilizando-se o fator de risco pós-déficit aplicado sobre a população urbana
# X: o percentual da população em risco total, que considera a população urbana multiplicada pelo fator de risco total (derivado da soma entre o fator iminente e o fator pós-déficit)
# Y: Ver depois

# Z: percentual de cobertura de rede do município, correspondente a um valor percentual previamente definido e utilizado como parâmetro de saneamento.

# AE, AF e AG correspondem a variáveis espaciais tabeladas, sendo respectivamente a área total do setor censitário, a área total da ottobacia e a área da porção do setor censitário inserida na ottobacia, não sendo derivadas por cálculo direto na planilha. 

dados_string = ['fid', 'COBACIA', 'cod_setor', 'cod_mun']
dtype_dict = {col: str for col in dados_string}

tabela_central = pd.read_csv('dim_hum_cnr_fmea.csv', dtype=dtype_dict)
tabela_central.drop(0, inplace=True)
tabela_inicial = tabela_central[tabela_central['COBACIA'].notna() & (tabela_central['COBACIA'] != '')]

dados_entregues = tabela_inicial.copy()


for col in dados_entregues.columns:
    if col in dados_string:
        dados_entregues[col] = dados_entregues[col].astype(str)
    elif dados_entregues[col].dtype == 'object':
        # tenta converter para número
        try:
            dados_entregues[col] = (
                dados_entregues[col]
                .str.replace('.', '', regex=False)      # remove ponto de milhar
                .str.replace(',', '.', regex=False)     # troca vírgula decimal por ponto
                .astype(float)
            )
        except (AttributeError, ValueError, TypeError):
            # se falhar, mantém coluna original
            pass

dados_entregues['bal_perc'] = 100*dados_entregues['dem_acm']/dados_entregues['disp_q95'] # L; a documentação original está ambígua sobre qual demanda utilizar; pelo contexto, inferi ser a demanda acumulada
dados_entregues['disp/dem'] = 100/dados_entregues['bal_perc'] # M


dados_entregues['fator_iminente'] = (1/3) * np.where( # N = (1/3)*(M3)^SE(M3>=1;-2;1); 
    dados_entregues['disp/dem'] >= 1,  
    dados_entregues['disp/dem'] ** (-2),  
    dados_entregues['disp/dem'] ** 1 
)

dados_entregues['fator_pós_deficit'] = np.where( # O = SE(M3 >=1;0;1 - (M3))
    dados_entregues['disp/dem'] >= 1,
    0,
    1 - dados_entregues['disp/dem']
)

dados_entregues['fator_de_risco_total'] = dados_entregues['fator_iminente'] + dados_entregues['fator_pós_deficit'] # P = O3+N3

# Substituir NaN por 0 e infinitos por 0 antes de converter
dados_entregues['ihu_nu_popriscoinerente'] = ( # W: percentual da população em risco pós-déficit, utilizando-se o fator de risco pós-déficit aplicado sobre a população urbana; N*R
    dados_entregues['fator_iminente'] * dados_entregues['dmu_nu_popurbana']
).fillna(0).replace([float('inf'), -float('inf')], 0).astype(float) 


dados_entregues['ihu_pc_risco_inerente'] = dados_entregues['ihu_nu_popriscoinerente']/dados_entregues['dmu_nu_popurbana'] # T: razão entre o número de habitantes em risco inerente e a população urbana total


dados_entregues['ihu_nu_popriscoposdeficit'] =  (
    dados_entregues['fator_pós_deficit']*dados_entregues['dmu_nu_popurbana'] # X: o percentual da população em risco total; X = O*R
).fillna(0).replace([float('inf'), -float('inf')], 0).astype(float)

dados_entregues['ihu_pc_riscoposdeficit'] = (
    dados_entregues['ihu_nu_popriscoposdeficit']/dados_entregues['dmu_nu_popurbana'] # U = X/R
).fillna(0).replace([float('inf'), -float('inf')], 0).astype(float)

dados_entregues['ihu_nu_popriscototal'] = (
    dados_entregues['fator_de_risco_total']*dados_entregues['dmu_nu_popurbana']
).fillna(0).replace([float('inf'), -float('inf')], 0).astype(float)  # Y = P*R

dados_entregues['ihu_pc_risco'] = (
    dados_entregues['ihu_nu_popriscototal']/dados_entregues['dmu_nu_popurbana'] # V = Y/R
).fillna(0).replace([float('inf'), -float('inf')], 0).astype(float)

dados_entregues['densidade'] = (
    dados_entregues['pop']/dados_entregues['area_setor']
).fillna(0).replace([float('inf'), -float('inf')], 0).astype(float)

# cs_risco: busca de dados em matriz
matriz_risco = [
            #    0% 20% 40% 60% 80%
                [5, 5,	4,	4,	3], # 0
                [5,	4,	3,	3,	2], # 2000
                [4,	3,	3,	2,	2], # 5000
                [4,	3,	2,	2,	1], # 10000
                [3,	2,	2,	1,	1]  # 50000
]

dados_entregues['cs_risco'] = dados_entregues['cs_risco'] = np.array(matriz_risco)[
    pd.cut(dados_entregues['ihu_nu_popriscototal'], bins=[0,2000,5000,10000,50000,float('inf')], labels=[0,1,2,3,4], right=False).astype(int),
    pd.cut(dados_entregues['ihu_pc_risco'], bins=[0,0.2,0.4,0.6,0.8,1.0], labels=[0,1,2,3,4], right=False).astype(int)
]

# cs_cobred: busca de dados dentre os limites da Cobertura de Rede de Abastecimento (%)
dados_entregues['cs_cobred'] = (pd.cut(dados_entregues['ihu_pc_cobrede'], bins=[0, 0.8, 0.9, 0.95, 0.98, 1], labels=[1,2,3,4,5],include_lowest=True)
                                 .astype(float)  # Converte para float, NaN vira NaN
                                 .fillna(0)      # Agora fillna funciona
                                 .astype(int))

# perc_scbc: Percentual da população na porção do setor cencitário que está na ottobacia em relação à população total da ottobacia
dados_entregues['perc_scbc'] = dados_entregues['pop_urb_scbc']/dados_entregues['pop_urb_bacia']

# TODO: ihu_rel: multiplicação do percentual da população na porção do setor censitário e ihu_cs_ish (preciso de conceituação) 
dados_entregues['ihu_rel'] = dados_entregues['perc_scbc']*dados_entregues['ihu_cs_ish']
# ire_cs_hum: soma dos ihu_rel que pertencem à mesma cobacia
dados_entregues['ire_cs_hum'] = dados_entregues.groupby('COBACIA')['ihu_rel'].transform('sum')

# Criar uma cópia do DataFrame com os números formatados como string brasileira
df_export = dados_entregues.copy()

# Converter todas as colunas numéricas para formato brasileiro
for col in df_export.select_dtypes(include=['float64', 'int64']).columns:
    df_export[col] = df_export[col].apply(lambda x: f"{x}".replace('.', ','))

# Salvar como CSV
df_export.to_csv('arquivo_br.csv', index=False, encoding='utf-8-sig')

tabela_inicial.to_csv('tabela_inicial.csv')