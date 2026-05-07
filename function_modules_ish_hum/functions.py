import pandas as pd
import geopandas as gpd
import numpy as np
from convertion_functions import *
import yaml

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

with open('scenario.yaml', 'r') as file:
    config = yaml.safe_load(file)

dimensions = config['dimensions']

# Encontra dimensão e já extrai os pesos
dimensao = next((d for d in dimensions if d['name'] == 'ire_cs_hum'), None)

if dimensao:
    indicadores = dimensao['indicadores']
    pesos = {item['indicador']: item['weight'] for item in indicadores}
    
    peso_cs_risco = pesos.get('cs_risco')
    peso_cs_cobred = pesos.get('cs_cobred')

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

dados_entregues['disp/dem'] = dados_entregues['bal_perc'].apply(disp_dem) # M

dados_entregues['fator_iminente'] = dados_entregues['disp/dem'].apply(fator_iminente)

dados_entregues['fator_pós_deficit'] = dados_entregues['disp/dem'].apply(fator_pos_deficit)

dados_entregues['fator_de_risco_total'] = dados_entregues['fator_iminente'] + dados_entregues['fator_pós_deficit'] # P = O3+N3

# Substituir NaN por 0 e infinitos por 0 antes de converter
dados_entregues['ihu_nu_popriscoinerente'] = dados_entregues.apply(ihu_nu_popriscoinerente, axis=1)

dados_entregues['ihu_pc_risco_inerente'] = dados_entregues.apply(ihu_pc_risco_inerente, axis=1) # T: razão entre o número de habitantes em risco inerente e a população urbana total

dados_entregues['ihu_nu_popriscoposdeficit'] =  dados_entregues.apply(ihu_nu_popriscoposdeficit,axis=1)

dados_entregues['ihu_pc_riscoposdeficit'] = dados_entregues.apply(ihu_pc_riscoposdeficit, axis=1)

dados_entregues['ihu_nu_popriscototal'] = dados_entregues.apply(ihu_nu_popriscototal, axis=1)

dados_entregues['ihu_pc_risco'] = dados_entregues.apply(ihu_pc_risco, axis=1)

dados_entregues['densidade'] = dados_entregues.apply(densidade, axis=1)

dados_entregues['cs_risco'] = dados_entregues.apply(cs_risco, axis=1)

# cs_cobred: busca de dados dentre os limites da Cobertura de Rede de Abastecimento (%)
dados_entregues['cs_cobred'] = dados_entregues['ihu_pc_cobrede'].apply(cs_cobred)

# perc_scbc: Percentual da população na porção do setor cencitário que está na ottobacia em relação à população total da ottobacia
dados_entregues['perc_scbc'] = dados_entregues.apply(perc_scbc, axis=1)

dados_entregues['ihu_cs_ish'] = dados_entregues.apply(
    lambda row: ihu_cs_ish(row, peso_cs_risco=peso_cs_risco, peso_cs_cobred=peso_cs_cobred), 
    axis=1
)

dados_entregues['ihu_rel_pop'] = dados_entregues['perc_scbc']*dados_entregues['cs_risco']
dados_entregues['ihu_rel_cobred'] = dados_entregues['perc_scbc']*dados_entregues['cs_cobred']

# dados_entregues['ihu_rel'] = dados_entregues['perc_scbc']*dados_entregues['ihu_cs_ish']   # Não preciso mais disso

#TODO: Precisa das colunas AP e AQ
dados_entregues['ire_hu_pop'] = round(dados_entregues.groupby('COBACIA')['ihu_rel_pop'].transform('sum'),2) # AP
dados_entregues['ire_hu_cobred'] = round(dados_entregues.groupby('COBACIA')['ihu_rel_cobred'].transform('sum'),2) # AQ # =SOMASE($B:$B;$B3;AN:AN)
dados_entregues['ire_cs_hum'] = dados_entregues.apply( # TODO:  =IF(AQ3<AP3;0,7*AP3+0,3*AQ3;AP3), 0,7 e 0,3 são weigths https://docs.google.com/spreadsheets/d/1BwZSjrKUrVmr8iAYrL86RvPQF2Lbkg4v/edit?usp=sharing&ouid=115797524688437743844&rtpof=true&sd=true
    lambda row: ire_cs_hum(row, peso_cs_risco=peso_cs_risco, peso_cs_cobred=peso_cs_cobred),
    axis=1
) 

# ind_rel: sempre que comece com esse valor, ele faz uma multiplicação baseado neles
# dados_entregues['ind_rel'] =
# Criar uma cópia do DataFrame com os números formatados como string brasileira
df_export = dados_entregues.copy()

# Converter todas as colunas numéricas para formato brasileiro
for col in df_export.select_dtypes(include=['float64', 'int64']).columns:
    df_export[col] = df_export[col].apply(lambda x: f"{x}".replace('.', ','))

# Salvar como CSV
df_export.to_csv('arquivo_br.csv', index=False, encoding='utf-8-sig')

tabela_inicial.to_csv('tabela_inicial.csv')
