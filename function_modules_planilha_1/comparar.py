import pandas as pd
import numpy as np

import re

def converter_numero_br(valor):
    """Converte número no formato brasileiro para float"""
    if pd.isna(valor):
        return np.nan
    
    valor_str = str(valor)
    
    # Padrão brasileiro: 1.234.567,89
    # Remove pontos de milhar (seguidos por exatamente 3 dígitos)
    # Mas mantém o último ponto se for decimal
    
    # Se tem vírgula, é decimal
    if ',' in valor_str:
        # Remove pontos que estão antes da vírgula (milhar)
        partes = valor_str.split(',')
        inteiro = partes[0].replace('.', '')  # Remove todos os pontos da parte inteira
        decimal = partes[1]
        return float(f"{inteiro}.{decimal}")
    else:
        # Sem vírgula, pode ter ponto de milhar ou ser inteiro
        # Se o padrão for algo como "1.234" (ponto de milhar)
        if '.' in valor_str and len(valor_str.split('.')[-1]) == 3:
            return float(valor_str.replace('.', ''))
        else:
            return float(valor_str)

arquivo_1 = pd.read_csv('tabela_inicial.csv')
arquivo_2 = pd.read_csv('arquivo_br.csv')

lista_conversao = ['disp_q95','dem_ret_ano','dem_acm','bal_perc',
                    'disp/dem','fator_iminente','fator_pós_deficit',
                    'fator_de_risco_total','dmu_nu_poptotal','dmu_nu_popurbana',
                    'dmu_nu_poprural','ihu_pc_risco_inerente','ihu_pc_riscoposdeficit',
                    'ihu_pc_risco','ihu_nu_popriscoinerente','ihu_nu_popriscoposdeficit',
                    'ihu_nu_popriscototal','ihu_pc_cobrede','cs_risco','cs_cobred',
                	'ihu_cs_ish','area_setor','area_otto','area_scbc','pop','densidade',
                    'pop_urb_scbc','pop_urb_bacia','perc_scbc','ihu_rel','ire_cs_hum']


for i in lista_conversao:
    arquivo_1[i] = arquivo_1[i].apply(converter_numero_br)
    arquivo_2[i] = arquivo_2[i].apply(converter_numero_br)

coluna_referencia = 'cod_mun'
posicao = arquivo_2.columns.get_loc(coluna_referencia)
df_comparacoes = arquivo_2.iloc[:, :posicao]

for i in arquivo_2.columns:
    if i in lista_conversao:
        df_comparacoes[i] = np.where(
            abs(100*(arquivo_2[i] - arquivo_1[i])/arquivo_2[i]) > 2,
            100*(arquivo_2[i] - arquivo_1[i])/arquivo_2[i],
            0
        )

df_comparacoes.to_csv('comparacoes.csv')