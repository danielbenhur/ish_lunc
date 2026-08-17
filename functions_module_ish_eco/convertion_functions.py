import pandas as pd
import numpy as np
import yaml
import sys

# irri_eco
# funcoes dependem de tabela PAM (extra)
# =ÍNDICE('Producao irrigada '!$AC$3:$AC$1442;CORRESP($E2;'Producao irrigada '!$A$3:$A$1442;0);)
def irri_arroz(df, parametros=['area_arroz', 'taxa_arroz'], pesos=[1,1]):
    # E - código do município
    area_potencial = pd.to_numeric(df['area_arroz'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    taxa_media     = pd.to_numeric(df['taxa_arroz'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    area_potencial = area_potencial*pesos[0]
    taxa_media = taxa_media*pesos[1]
    return area_potencial*taxa_media
def irri_cafe(df, parametros=['Area potencial de ser colhida irrigada por municipio por cultura  (Café)', 'Taxa regional media de produção de Café (1000R$/ha) '], pesos=[1, 1]):
    area_potencial = pd.to_numeric(df['Area potencial de ser colhida irrigada por municipio por cultura  (Café)'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    taxa_media     = pd.to_numeric(df['Taxa regional media de produção de Café (1000R$/ha) '].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    area_potencial = area_potencial*pesos[0]
    taxa_media = taxa_media*pesos[1]
    return area_potencial*taxa_media
def irri_cana(df, parametros=['Area potencial de ser colhida irrigada por municipio por cultura (Cana)', 'Taxa regional media de produção de Cana (1000R$/ha) '], pesos=[1, 1]):
    area_potencial = pd.to_numeric(df['Area potencial de ser colhida irrigada por municipio por cultura (Cana)'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    taxa_media     = pd.to_numeric(df['Taxa regional media de produção de Cana (1000R$/ha) '].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    area_potencial = area_potencial*pesos[0]
    taxa_media = taxa_media*pesos[1]
    return area_potencial*taxa_media
def irri_oc(df, parametros=['Area potencial de ser colhida irrigada por municipio por cultura (Outras Culturas)', 'Taxa regional media de produção de Demais culturas (1000R$/ha) '], pesos=[1, 1]):
    area_potencial = pd.to_numeric(df['Area potencial de ser colhida irrigada por municipio por cultura (Outras Culturas)'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    taxa_media     = pd.to_numeric(df['Taxa regional media de produção de Demais culturas (1000R$/ha) '].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    area_potencial = area_potencial*pesos[0]
    taxa_media = taxa_media*pesos[1]
    return area_potencial*taxa_media

# função nos parâmetros jogada para outra parte no yaml de configuração 
def irri_total(df, parametros=['irri_arroz', 'irri_cafe', 'irri_cana', 'irri_oc'], pesos=[1, 1, 1, 1]):
    irri_arroz = df['irri_arroz']*pesos[0]
    irri_cafe = df['irri_cafe']*pesos[1]
    irri_cana = df['irri_cana']*pesos[2]
    irri_oc   = df['irri_oc']*pesos[3]
    resultado = irri_arroz + irri_cafe + irri_cana + irri_oc
    return resultado

# derivados das dependentes de PAM
def irri_arroz_risco_iminente(df, parametros=['irri_arroz', 'fator_iminente'], pesos=[1, 1]):
    irri_arroz = pd.to_numeric(df['irri_arroz'], errors='coerce')*pesos[0]
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')*pesos[1]
    return irri_arroz*fator_iminente

def irri_arroz_risco_pos_deficit(df, parametros=['irri_arroz', 'fator_pos_deficit'], pesos=[1, 1]):
    irri_arroz = pd.to_numeric(df['irri_arroz'], errors='coerce')*pesos[0]
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')*pesos[1]
    return irri_arroz*fator_pos_deficit

def irri_arroz_risco_total(df, parametros=['irri_arroz', 'fator_de_risco_total'], pesos=[1, 1]):
    irri_arroz = pd.to_numeric(df['irri_arroz'], errors='coerce')*pesos[0]
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')*pesos[1]
    return irri_arroz*fator_de_risco_total

def irri_cafe_risco_iminente(df, parametros=['irri_cafe', 'fator_iminente'], pesos=[1, 1]):
    irri_cafe = pd.to_numeric(df['irri_cafe'], errors='coerce')*pesos[0]
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')*pesos[1]
    return irri_cafe*fator_iminente

def irri_cafe_risco_pos_deficit(df, parametros=['irri_cafe', 'fator_pos_deficit'], pesos=[1, 1]):
    irri_cafe = pd.to_numeric(df['irri_cafe'], errors='coerce')*pesos[0]
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')*pesos[1]
    return irri_cafe*fator_pos_deficit

def irri_cafe_risco_total(df, parametros=['irri_cafe', 'fator_de_risco_total'], pesos=[1, 1]):
    irri_cafe = pd.to_numeric(df['irri_cafe'], errors='coerce')*pesos[0]
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')*pesos[1]
    return irri_cafe*fator_de_risco_total

def irri_cana_risco_iminente(df, parametros=['irri_cana', 'fator_iminente'], pesos=[1, 1]):
    irri_cana = pd.to_numeric(df['irri_cana'], errors='coerce')*pesos[0]
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')*pesos[1]
    return irri_cana*fator_iminente

def irri_cana_risco_pos_deficit(df, parametros=['irri_cana', 'fator_pos_deficit'], pesos=[1, 1]):
    irri_cana = pd.to_numeric(df['irri_cana'], errors='coerce')*pesos[0]
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')*pesos[1]
    return irri_cana*fator_pos_deficit

def irri_cana_risco_total(df, parametros=['irri_cana', 'fator_de_risco_total'], pesos=[1, 1]):
    irri_cana = pd.to_numeric(df['irri_cana'], errors='coerce')*pesos[0]
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')*pesos[1]
    return irri_cana*fator_de_risco_total

def irri_oc_risco_iminente(df, parametros=['irri_oc', 'fator_iminente'], pesos=[1, 1]):
    irri_oc = pd.to_numeric(df['irri_oc'], errors='coerce')*pesos[0]
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')*pesos[1]
    return irri_oc*fator_iminente

def irri_oc_risco_pos_deficit(df, parametros=['irri_oc', 'fator_pos_deficit'], pesos=[1, 1]):
    irri_oc = pd.to_numeric(df['irri_oc'], errors='coerce')*pesos[0]
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')*pesos[1]
    return irri_oc*fator_pos_deficit

def irri_oc_risco_total(df, parametros=['irri_oc', 'fator_de_risco_total'], pesos=[1, 1]):
    irri_oc = pd.to_numeric(df['irri_oc'], errors='coerce')*pesos[0]
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')*pesos[1]
    return irri_oc*fator_de_risco_total

def irri_total_risco_iminente(df, parametros=['irri_total', 'fator_iminente'], pesos=[1, 1]):
    irri_total = pd.to_numeric(df['irri_total'], errors='coerce')*pesos[0]
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')*pesos[1]
    return irri_total*fator_iminente

def irri_total_risco_pos_deficit(df, parametros=['irri_total', 'fator_pos_deficit'], pesos=[1, 1]):
    irri_total = pd.to_numeric(df['irri_total'], errors='coerce')*pesos[0]
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')*pesos[1]
    return irri_total*fator_pos_deficit

def irri_total_risco_total(df, parametros=['irri_total', 'fator_de_risco_total'], pesos=[1, 1]):
    irri_total = pd.to_numeric(df['irri_total'], errors='coerce')*pesos[0]
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')*pesos[1]
    return irri_total*fator_de_risco_total

# =ARRAY_CONSTRAIN(ARRAYFORMULA(ÍNDICE(classificacao!$B$3:$F$7;CORRESP($AJ2;classificacao!$A$3:$A$7;1);CORRESP($P2;classificacao!$B$2:$F$2;1))); 1; 1)
# AJ - irri_total
# P - fator_de_risco_total
def cs_ish_irri(df, parametros=['irri_total_risco_total', 'fator_de_risco_total'], pesos=[1, 1]):
    irri_total_risco_total = pd.to_numeric(df['irri_total_risco_total'].fillna(-float('inf')), errors='coerce')*pesos[0]
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'].fillna(-float('inf')), errors='coerce')*pesos[1]
    
    # Valores de referência
    irri_referencia = np.array([0, 1, 5, 10, 50])
    risco_referencia = np.array([0, 0.1, 0.2, 0.3, 0.4])
    
    # Matriz de risco
    matriz_risco = np.array([
        [5, 5, 4, 3, 3],
        [5, 4, 3, 3, 2],
        [4, 3, 3, 2, 2],
        [3, 3, 2, 2, 1],
        [3, 2, 2, 1, 1]
    ])
    
    # Encontra índices usando busca binária (mais eficiente)
    idx_irri = np.searchsorted(irri_referencia, irri_total_risco_total, side='right') - 1
    idx_risco = np.searchsorted(risco_referencia, fator_de_risco_total, side='right') - 1
    
    # Garante que os índices estão dentro dos limites
    idx_irri = np.clip(idx_irri, 0, matriz_risco.shape[0] - 1)
    idx_risco = np.clip(idx_risco, 0, matriz_risco.shape[1] - 1)
    
    # Mapeia os valores
    resultado = matriz_risco[idx_irri, idx_risco]
    
    return pd.Series(resultado)

# depende da tabela demanda (extra)
# precisa de outro arquivo csv ainda
# =SEERRO(ÍNDICE(demanda!$D:$D;CORRESP($B2;VALOR(ESQUERDA(demanda!$A:$A;15));0));0)
# TODO: corrigir lógica, está entregando dados errado
# A ideia aqui é extrair uma coluna e colocar ao final para fazer os cálculos
def deman_irri(df, parametros=['Valor que eu quero '], pesos=[1]):
    # demanda!D - Valor que eu quero
    # demanda!A - COBACIA
    # B - COBACIA
    demanda_df = pd.read_csv('/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_eco/input/PAM - ES - demanda.csv')
    coluna_D = 'Valor que eu quero '
    demanda_df['COBACIA'] = demanda_df['COBACIA'].astype('object')
    demanda_df[coluna_D] = pd.to_numeric(demanda_df[coluna_D].str.replace(',', '.'), errors='coerce')*pesos[0]

    return demanda_df[coluna_D]

def densidade_irri(df, parametros=['area_otto', 'deman_irri'], pesos=[1, 1]):
    area_otto = pd.to_numeric(df['area_otto'].str.replace(',', '.'), errors='coerce')*pesos[0]
    deman_irri = pd.to_numeric(df['deman_irri'], errors='coerce')*pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            (area_otto == 0) | pd.isna(area_otto),  # condição
            0,                                     # valor se for zero ou NaN
            deman_irri/area_otto                   # valor caso contrário
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)

# =SE($H2<=10;$AP2*$AN2;0)
def deman_agri_scbc(df, parametros=['situacao_setor', 'densidade_irri', 'area_setor'], pesos=[1, 1]):
    # H2 - situacao_setor - não faz sentido ter peso
    # AP2 - densidade
    # AN2 - area_setor
    situacao_setor = pd.to_numeric(df['situacao_setor'], errors='coerce')
    densidade = pd.to_numeric(df['densidade_irri'], errors='coerce')*pesos[0]
    area_setor = pd.to_numeric(df['area_setor'].str.replace(',', '.'), errors='coerce')*pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            (situacao_setor <= 10),  # condição
            densidade*area_setor,                                     
            0                 # valor caso contrário
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)

# =SOMASE($B:$B;$B2;AQ:AQ)
def deman_agri_otto(df, parametros=['COBACIA', 'deman_agri_scbc'], pesos=[1]):
    # B - COBACIA
    # AQ - deman_agri_scbc
    cobacia = df['COBACIA']
    deman_agri_scbc = df['deman_agri_scbc']*pesos[0]
    return deman_agri_scbc.groupby(cobacia).transform('sum') 

# TODO: análise se faz sentido usar a demanda da Ottobacia para verificar porcentagem
# =SEERRO(AQ2/AO2;0)
def perc_scbc_irri(df, parametros=['deman_agri_scbc', 'deman_irri'], pesos=[1, 1]):
    # AQ - deman_agri_scbc
    # AO - deman_agri
    deman_agri_scbc = df['deman_agri_scbc']*pesos[0]
    deman_irri = df['deman_agri_otto']*pesos[1]
    # print(df[['deman_agri_scbc', 'deman_irri']])
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            (deman_irri == 0),  # condição
            0,                                     
            deman_agri_scbc/deman_irri # valor caso contrário
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)

def irri_risco_scbc(df, parametros=['perc_scbc_irri', 'irri_total_risco_total'], pesos=[1, 1]):
    perc_scbc = df['perc_scbc_irri']*pesos[0]
    irri_total_risco_total = df['irri_total_risco_total']*pesos[1]
    return perc_scbc*irri_total_risco_total

# =SEERRO(AS2*$AK2;0)
def cs_ish_scbc_irri(df, parametros=['cs_ish_irri', 'perc_scbc_irri'], pesos=[1, 1]):
    cs_ish_irri = df['cs_ish_irri']*pesos[0]
    perc_scbc = df['perc_scbc_irri']*pesos[1]
    return cs_ish_irri*perc_scbc


# =SOMASE($B:$B;$B2;AU:AU)
def ire_cs_irri_eco(df, parametros=['COBACIA', 'cs_ish_scbc_irri'], pesos=[1]):
    cobacia = df['COBACIA']
    cs_ish_scbc_irri = df['cs_ish_scbc_irri']*pesos[0]
    return cs_ish_scbc_irri.groupby(cobacia).transform('sum')


# pec_eco
# dependem da tabela PPM
# =ÍNDICE(PPM!$N$4:$N$1442;CORRESP($E2;PPM!$B$4:$B$1442;0))
def pec_bov(df, parametros=['Valor por rebanho (Bovino)'], pesos=[1]):
    return df['Valor por rebanho (Bovino)']*pesos[0]
def pec_bub(df, parametros=['Valor por rebanho (Bufalo)'], pesos=[1]):
    return df['Valor por rebanho (Bufalo)']*pesos[0]
def pec_sui(df, parametros=['Valor por rebanho (Suino)'], pesos=[1]):
    return df['Valor por rebanho (Suino)']*pesos[0]
def pec_cap(df, parametros=['Valor por rebanho (Caprino)'], pesos=[1]):
    return df['Valor por rebanho (Caprino)']*pesos[0]
def pec_ovi(df, parametros=['Valor por rebanho (Ovino)'], pesos=[1]):
    return df['Valor por rebanho (Ovino)']*pesos[0]
def pec_gal(df, parametros=['Valor por rebanho (Galinaceos)'], pesos=[1]):
    return df['Valor por rebanho (Galinaceos)']*pesos[0]
# =SOMA(Q2:V2)
def pec_total(df, parametros=['pec_bov', 'pec_bub', 'pec_sui', 'pec_cap', 'pec_ovi', 'pec_gal'], pesos=[1, 1, 1, 1, 1, 1]):
    pec_bov = pd.to_numeric(df['pec_bov'], errors='coerce')*pesos[0]
    pec_bub = pd.to_numeric(df['pec_bub'], errors='coerce')*pesos[1]
    pec_sui = pd.to_numeric(df['pec_sui'], errors='coerce')*pesos[2]
    pec_cap = pd.to_numeric(df['pec_cap'], errors='coerce')*pesos[3]
    pec_ovi = pd.to_numeric(df['pec_ovi'], errors='coerce')*pesos[4]
    pec_gal = pd.to_numeric(df['pec_gal'], errors='coerce')*pesos[5]

    resultado = pec_bov+pec_bub+pec_sui+pec_cap+pec_ovi+pec_gal
    return resultado

def pec_risco_iminente(df, parametros=['pec_total', 'fator_iminente'], pesos=[1, 1]):
    pec_total = pd.to_numeric(df['pec_total'], errors='coerce')*pesos[0]
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')*pesos[1]
    return pec_total*fator_iminente

def pec_risco_pos_deficit(df, parametros=['pec_total', 'fator_pos_deficit'], pesos=[1, 1]):
    pec_total = pd.to_numeric(df['pec_total'], errors='coerce')*pesos[0]
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')*pesos[1]
    return pec_total*fator_pos_deficit

def pec_risco_total(df, parametros=['pec_total', 'fator_de_risco_total'], pesos=[1, 1]):
    pec_total = pd.to_numeric(df['pec_total'], errors='coerce')*pesos[0]
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')*pesos[1]
    return pec_total*fator_de_risco_total

# depende da tabela classificação
# =ARRAY_CONSTRAIN(ARRAYFORMULA(ÍNDICE(classificacao!$B$3:$F$7;CORRESP($Z2;classificacao!$A$3:$A$7;1);CORRESP($P2;classificacao!$B$2:$F$2;1))); 1; 1)
def cs_ish_pec(df, parametros=['pec_risco_total', 'fator_de_risco_total'], pesos=[1, 1]):
    pec_risco_total = pd.to_numeric(df['pec_risco_total'].fillna(-float('inf')), errors='coerce')*pesos[0]
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'].fillna(-float('inf')), errors='coerce')*pesos[1]
    
    # Valores de referência
    pec_referencia = np.array([0, 1000, 5000, 15000, 35000])
    risco_referencia = np.array([0, 0.1, 0.2, 0.3, 0.4])
    
    # Matriz de risco
    matriz_risco = np.array([
        [5,	5,	4,	3, 3],
        [5,	4,	3,	3, 2],
        [4,	3,	3,	2, 2],
        [3,	3,	2,	2, 1],
        [3,	2,	2,	1, 1]
    ])
    
    # Encontra índices usando busca binária (mais eficiente)
    idx_pec = np.searchsorted(pec_referencia, pec_risco_total, side='right') - 1
    idx_risco = np.searchsorted(risco_referencia, fator_de_risco_total, side='right') - 1
    
    # Garante que os índices estão dentro dos limites
    idx_pec = np.clip(idx_pec, 0, matriz_risco.shape[0] - 1)
    idx_risco = np.clip(idx_risco, 0, matriz_risco.shape[1] - 1)
    
    # Mapeia os valores
    resultado = matriz_risco[idx_pec, idx_risco]
    
    return pd.Series(resultado)

# depende da tabela demanda
# =SEERRO(ÍNDICE(demanda!$D:$D;CORRESP($B2;VALOR(ESQUERDA(demanda!$A:$A;15));0));0)
# TODO: corrigir lógica, está entregando dados errado
# A ideia aqui é extrair uma coluna e colocar ao final para fazer os cálculos
def deman_pecuaria(df, parametros=[], pesos=[1]):
    # demanda!D - Valor que eu quero
    # demanda!A - COBACIA
    # B - COBACIA
    demanda_df = pd.read_csv('/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_eco/input/PPM - ES - demanda.csv')
    coluna_D = 'Valor que eu quero '
    demanda_df['COBACIA'] = demanda_df['COBACIA'].astype('object')
    demanda_df[coluna_D] = pd.to_numeric(demanda_df[coluna_D].str.replace(',', '.'), errors='coerce')

    return demanda_df[coluna_D]*pesos[0]

# dúvida entre area_setor e area_otto
def densidade_pec(df, parametros=['area_otto', 'deman_pecuaria'], pesos=[1, 1]):
    area_otto = pd.to_numeric(df['area_otto'].str.replace(',', '.'), errors='coerce')*pesos[0]
    deman_pecuaria = pd.to_numeric(df['deman_pecuaria'], errors='coerce')*pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            (area_otto == 0) | pd.isna(area_otto),  # condição
            0,                                     # valor se for zero ou NaN
            deman_pecuaria/area_otto                  # valor caso contrário
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)


# =SE($H2<=10;$AF2*$AD2;0)
def deman_pecuaria_scbc(df, parametros=['situacao_setor', 'densidade_pec', 'area_setor'], pesos=[1, 1]):
    # H2 - situacao_setor
    # AP2 - densidade
    # AN2 - area_setor
    situacao_setor = pd.to_numeric(df['situacao_setor'], errors='coerce')
    densidade = pd.to_numeric(df['densidade_pec'], errors='coerce')*pesos[0]
    area_setor = pd.to_numeric(df['area_setor'].str.replace(',', '.'), errors='coerce')*pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            (situacao_setor <= 10),  # condição
            densidade*area_setor,                                     
            0                 # valor caso contrário
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)

def deman_pecuaria_otto(df, parametros=['deman_pecuaria_scbc', 'COBACIA'], pesos=[1]):
    deman_pecuaria_scbc = df['deman_pecuaria_scbc']*pesos[0]
    cobacia = df['COBACIA']
    return deman_pecuaria_scbc.groupby(cobacia).transform('sum')

# TODO: verificar se faz sentido usar a demanda da Ottobacia para calcular essa
# =SEERRO(AG2/AE2;0)  
def perc_deman_pecuaria(df, parametros=['deman_pecuaria_scbc', 'deman_pecuaria'], pesos=[1, 1]):
    deman_pecuaria_scbc = df['deman_pecuaria_scbc']*pesos[0]
    deman_pecuaria = df['deman_pecuaria_otto']*pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            deman_pecuaria == 0,
            0,
            deman_pecuaria_scbc/deman_pecuaria
        )
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)

def ihu_cs_ish_pec(df, parametros=['cs_ish_pec', 'perc_deman_pecuaria'], pesos=[1, 1]):
    cs_ish_pec = df['cs_ish_pec']*pesos[0]
    perc_deman_pecuaria = df['perc_deman_pecuaria']*pesos[1]
    return cs_ish_pec*perc_deman_pecuaria

def ire_cs_pec_eco(df, parametros=['ihu_cs_ish_pec', 'COBACIA'], pesos=[1]):
    ihu_cs_ish_pec = df['ihu_cs_ish_pec']*pesos[0]
    cobacia = df['COBACIA']
    return ihu_cs_ish_pec.groupby(cobacia).transform('sum')

# ind_eco
def ihu_nu_indriscoinerente(df, parametros=['fator_iminente', 'dmu_nu_vab'], pesos=[1, 1]):
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')*pesos[0]
    dmu_nu_vab = pd.to_numeric(df['dmu_nu_vab'].str.replace('.', ''), errors='coerce')*pesos[1]

    return dmu_nu_vab*fator_iminente

def ihu_nu_indriscoposdeficit(df, parametros=['fator_pos_deficit', 'dmu_nu_vab'], pesos=[1, 1]):
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')
    dmu_nu_vab = pd.to_numeric(df['dmu_nu_vab'].str.replace('.', ''), errors='coerce')
    return dmu_nu_vab*fator_pos_deficit

def ihu_nu_indriscototal(df, parametros=['fator_de_risco_total', 'dmu_nu_vab'], pesos=[1, 1]):
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')*pesos[0]
    dmu_nu_vab = pd.to_numeric(df['dmu_nu_vab'].str.replace('.', ''), errors='coerce')*pesos[1]
    return dmu_nu_vab*fator_de_risco_total

# =ARRAY_CONSTRAIN(ARRAYFORMULA(ÍNDICE(classificacao!$B$3:$F$7;CORRESP(T3;classificacao!$A$3:$A$7;1);CORRESP($P3;classificacao!$B$2:$F$2;1))); 1; 1)
# depende da tabela classificacao
def ihu_cs_ish_ind(df, parametros=['ihu_nu_indriscototal', 'fator_de_risco_total'], pesos=[1, 1]):
    ihu_nu_indriscototal = pd.to_numeric(df['ihu_nu_indriscototal'].fillna(-float('inf')), errors='coerce')*pesos[0]
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'].fillna(-float('inf')), errors='coerce')*pesos[1]
    
    # Valores de referência
    ind_referencia = np.array([0, 1, 10, 25, 150])
    risco_referencia = np.array([0, 0.1, 0.2, 0.3, 0.4])
    
    # Matriz de risco
    matriz_risco = np.array([
        [5,	5,	4,	3,	3],
        [5,	4,	3,	3,	2],
        [4,	3,	3,	2,	2],
        [3,	3,	2,	2,	1],
        [3,	2,	2,	1,	1]
    ])
    
    # Encontra índices usando busca binária (mais eficiente)
    idx_ind = np.searchsorted(ind_referencia, ihu_nu_indriscototal, side='right') - 1
    idx_risco = np.searchsorted(risco_referencia, fator_de_risco_total, side='right') - 1
    
    # Garante que os índices estão dentro dos limites
    idx_ind = np.clip(idx_ind, 0, matriz_risco.shape[0] - 1)
    idx_risco = np.clip(idx_risco, 0, matriz_risco.shape[1] - 1)
    
    # Mapeia os valores
    resultado = matriz_risco[idx_ind, idx_risco]
    
    return pd.Series(resultado)

# depende da tabela demanda (extra)
# precisa de outro arquivo csv ainda
# =SEERRO(ÍNDICE(demanda!$D:$D;CORRESP($B2;VALOR(ESQUERDA(demanda!$A:$A;15));0));0)
# TODO: corrigir lógica, está entregando dados errado
# A ideia aqui é extrair uma coluna e colocar ao final para fazer os cálculos
def deman_indus(df, parametros=[], pesos=[1]):
    # demanda!D - Valor que eu quero
    # demanda!A - COBACIA
    # B - COBACIA
    demanda_df = pd.read_csv('/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_eco/input/Indicador Industria - Bernardo - demanda.csv')
    coluna_D = 'Valor que eu quero '
    demanda_df['COBACIA'] = demanda_df['COBACIA'].astype('object')
    demanda_df[coluna_D] = pd.to_numeric(demanda_df[coluna_D].str.replace(',', '.'), errors='coerce')

    return demanda_df[coluna_D]*pesos[0]

def densidade_ind(df, parametros=['area_otto', 'deman_indus'], pesos=[1, 1]):
    area_otto = pd.to_numeric(df['area_otto'].str.replace(',', '.'), errors='coerce')*pesos[0]
    deman_indus = pd.to_numeric(df['deman_indus'], errors='coerce')*pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            (area_otto == 0) | pd.isna(area_otto),  # condição
            0,                                     # valor se for zero ou NaN
            deman_indus/area_otto                  # valor caso contrário
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)

def dem_ind_scbc(df, parametros=['situacao_setor', 'densidade_ind', 'area_setor'], pesos=[1, 1]):
    # H2 - situacao_setor - sem peso
    # AP2 - densidade
    # AN2 - area_setor
    situacao_setor = pd.to_numeric(df['situacao_setor'], errors='coerce')
    densidade = pd.to_numeric(df['densidade_ind'], errors='coerce')*pesos[0]
    area_setor = pd.to_numeric(df['area_setor'].str.replace(',', '.'), errors='coerce')*pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            (situacao_setor <= 10),  # condição
            densidade*area_setor,                                     
            0                 # valor caso contrário
        )
        
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)

def dem_ind_bacia(df, parametros=['dem_ind_scbc', 'COBACIA'], pesos=[1]):
    dem_ind_scbc = df['dem_ind_scbc']*pesos[0]
    cobacia = df['COBACIA']
    return dem_ind_scbc.groupby(cobacia).transform('sum')

def perc_scbc_ind(df, parametros=['dem_ind_scbc', 'dem_ind_bacia'], pesos=[1, 1]):
    # AQ - deman_agri_scbc
    # AO - deman_agri
    dem_ind_scbc = df['dem_ind_scbc']*pesos[0]
    deman_indus = df['dem_ind_bacia']*pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            (deman_indus == 0),  # condição
            0,                                     
            dem_ind_scbc/deman_indus # valor caso contrário
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)

def ihu_rel_ind(df, parametros=['perc_scbc_ind', 'ihu_cs_ish_ind'], pesos=[1, 1]):
    perc_scbc_ind = df['perc_scbc_ind']*pesos[0]
    ihu_cs_ish_ind = df['ihu_cs_ish_ind']*pesos[1]
    return perc_scbc_ind*ihu_cs_ish_ind

def ire_cs_ind_eco(df, parametros=['ihu_rel_ind', 'COBACIA'], pesos=[1]):
    ihu_rel = df['ihu_rel_ind']*pesos[0]
    cobacia = df['COBACIA']
    return ihu_rel.groupby(cobacia).transform('sum')

def ire_cs_eco(ind, peso_ind, irri, peso_irri, pec, peso_pec):
    # =SE(E(B4=0; C4=0); ""; (SE(B4=0; 5; B4)*0,3 + SE(C4=0; 5; C4)*0,7))
    if irri == 0 and pec == 0:
        impacto_agro = 0
    elif irri == 0:
        irri = 5
    elif pec == 0:
        pec = 5
    
    impacto_agro = pec*peso_pec + irri*peso_irri
    impacto_ind  = ind*peso_ind

    # =LET(agropec; SE(E(B2=0; C2=0); 0; SE(B2=0; 5; B2)*0,3 + SE(C2=0; 5; C2)*0,7); ind; E2; SE(agropec>0; SE(ind>0; MÍNIMO(agropec; ind); ind); SE(agropec>0; agropec; "")))
    if impacto_ind == 0:
        return impacto_agro
    elif impacto_agro < impacto_ind:
        return impacto_agro
    else:
        return impacto_ind