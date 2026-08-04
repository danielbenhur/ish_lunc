import pandas as pd
import numpy as np
import yaml
import sys

# irri_eco
# funcoes dependem de tabela PAM (extra)
# =ÍNDICE('Producao irrigada '!$AC$3:$AC$1442;CORRESP($E2;'Producao irrigada '!$A$3:$A$1442;0);)
def irri_arroz(df):
    # E - código do município
    area_potencial = pd.to_numeric(df['area_arroz'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    taxa_media     = pd.to_numeric(df['taxa_arroz'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    return area_potencial*taxa_media
def irri_cafe(df):
    area_potencial = pd.to_numeric(df['Area potencial de ser colhida irrigada por municipio por cultura  (Café)'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    taxa_media     = pd.to_numeric(df['Taxa regional media de produção de Café (1000R$/ha) '].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    return area_potencial*taxa_media
def irri_cana(df):
    area_potencial = pd.to_numeric(df['Area potencial de ser colhida irrigada por municipio por cultura (Cana)'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    taxa_media     = pd.to_numeric(df['Taxa regional media de produção de Cana (1000R$/ha) '].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    return area_potencial*taxa_media
def irri_oc(df):
    area_potencial = pd.to_numeric(df['Area potencial de ser colhida irrigada por municipio por cultura (Outras Culturas)'].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    taxa_media     = pd.to_numeric(df['Taxa regional media de produção de Demais culturas (1000R$/ha) '].str.replace('.', '').str.replace(',', '.'), errors='coerce')
    return area_potencial*taxa_media

# função nos parâmetros jogada para outra parte no yaml de configuração 
def irri_total(df):
    irri_arroz = df['irri_arroz']
    irri_cafe = df['irri_cafe']
    irri_cana = df['irri_cana']
    irri_oc   = df['irri_oc']
    resultado = irri_arroz + irri_cafe + irri_cana + irri_oc
    return resultado

# derivados das dependentes de PAM
def irri_arroz_risco_iminente(df):
    irri_arroz = pd.to_numeric(df['irri_arroz'], errors='coerce')
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')
    return irri_arroz*fator_iminente

def irri_arroz_risco_pos_deficit(df):
    irri_arroz = pd.to_numeric(df['irri_arroz'], errors='coerce')
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')
    return irri_arroz*fator_pos_deficit

def irri_arroz_risco_total(df):
    irri_arroz = pd.to_numeric(df['irri_arroz'], errors='coerce')
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')
    return irri_arroz*fator_de_risco_total

def irri_cafe_risco_iminente(df):
    irri_cafe = pd.to_numeric(df['irri_cafe'], errors='coerce')
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')
    return irri_cafe*fator_iminente

def irri_cafe_risco_pos_deficit(df):
    irri_cafe = pd.to_numeric(df['irri_cafe'], errors='coerce')
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')
    return irri_cafe*fator_pos_deficit

def irri_cafe_risco_total(df):
    irri_cafe = pd.to_numeric(df['irri_cafe'], errors='coerce')
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')
    return irri_cafe*fator_de_risco_total

def irri_cana_risco_iminente(df):
    irri_cana = pd.to_numeric(df['irri_cana'], errors='coerce')
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')
    return irri_cana*fator_iminente

def irri_cana_risco_pos_deficit(df):
    irri_cana = pd.to_numeric(df['irri_cana'], errors='coerce')
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')
    return irri_cana*fator_pos_deficit

def irri_cana_risco_total(df):
    irri_cana = pd.to_numeric(df['irri_cana'], errors='coerce')
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')
    return irri_cana*fator_de_risco_total

def irri_oc_risco_iminente(df):
    irri_oc = pd.to_numeric(df['irri_oc'], errors='coerce')
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')
    return irri_oc*fator_iminente

def irri_oc_risco_pos_deficit(df):
    irri_oc = pd.to_numeric(df['irri_oc'], errors='coerce')
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')
    return irri_oc*fator_pos_deficit

def irri_oc_risco_total(df):
    irri_oc = pd.to_numeric(df['irri_oc'], errors='coerce')
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')
    return irri_oc*fator_de_risco_total

def irri_total_risco_iminente(df):
    irri_total = pd.to_numeric(df['irri_total'], errors='coerce')
    fator_iminente = pd.to_numeric(df['fator_iminente'], errors='coerce')
    return irri_total*fator_iminente

def irri_total_risco_pos_deficit(df):
    irri_total = pd.to_numeric(df['irri_total'], errors='coerce')
    fator_pos_deficit = pd.to_numeric(df['fator_pos_deficit'], errors='coerce')
    return irri_total*fator_pos_deficit

def irri_total_risco_total(df):
    irri_total = pd.to_numeric(df['irri_total'], errors='coerce')
    fator_de_risco_total = pd.to_numeric(df['fator_de_risco_total'], errors='coerce')
    return irri_total*fator_de_risco_total

# =ARRAY_CONSTRAIN(ARRAYFORMULA(ÍNDICE(classificacao!$B$3:$F$7;CORRESP($AJ2;classificacao!$A$3:$A$7;1);CORRESP($P2;classificacao!$B$2:$F$2;1))); 1; 1)
# AJ - irri_total
# P - fator_de_risco_total
def cs_ish_irri(df):
    irri_total = df['irri_total'].fillna(-float('inf'))
    fator_de_risco_total = df['fator_de_risco_total'].fillna(-float('inf'))
    
    # Valores de referência
    irri_referencia = np.array([-float('inf'), 0, 5, 10, 50])
    risco_referencia = np.array([-float('inf'), 0, 0.1, 0.2, 0.3, 0.4])
    
    # Matriz de risco
    matriz_risco = np.array([
        [5, 5, 4, 3, 3],
        [5, 4, 3, 3, 2],
        [4, 3, 3, 2, 2],
        [3, 3, 2, 2, 1],
        [3, 2, 2, 1, 1]
    ])
    
    # Encontra índices usando busca binária (mais eficiente)
    idx_irri = np.searchsorted(irri_referencia, irri_total, side='right') - 1
    idx_risco = np.searchsorted(risco_referencia, fator_de_risco_total, side='right') - 1
    
    # Garante que os índices estão dentro dos limites
    idx_irri = np.clip(idx_irri, 0, matriz_risco.shape[0] - 1)
    idx_risco = np.clip(idx_risco, 0, matriz_risco.shape[1] - 1)
    
    # Mapeia os valores
    resultado = matriz_risco[idx_irri, idx_risco]
    
    return pd.Series(resultado)
    
# depende da tabela demanda (extra)
def deman_agri(df):
    return 0
def densidade(df):
    area_setor = df['area_setor']
    deman_agri = df['deman_agri']
    return deman_agri/area_setor

# =SE($H2<=10;$AP2*$AN2;0)
def deman_agri_scbc(df):
    # H2 - situacao_setor
    # AP2 - densidade
    # AN2 - area_setor
    situacao_setor = df['situacao_setor']
    densidade = df['densidade']
    area_setor = df['area_setor']
    if situacao_setor <= 10:
        return densidade*area_setor
    else: 
        return 0
# =SOMASE($B:$B;$B2;AQ:AQ)
def deman_agri_otto(df):
    # B - COBACIA
    # AQ - deman_agri_scbc
    cobacia = df['COBACIA']
    deman_agri_scbc = df['deman_agri_scbc']
    return deman_agri_scbc.groupby(cobacia).transform('sum') 

# =SEERRO(AQ2/AO2;0)
def perc_scbc(df):
    # AQ - deman_agri_scbc
    # AO - deman_agri
    deman_agri_scbc = df['deman_agri_scbc']
    deman_agri = df['deman_agri']

    return deman_agri_scbc/deman_agri

def irri_risco_scbc(df):
    perc_scbc = df['perc_scbc']
    irri_total_risco_total = df['irri_total_risco_total']
    return perc_scbc*irri_total_risco_total

# =SEERRO(AS2*$AK2;0)
def cs_ish_scbc(df):
    cs_ish_irri = df['cs_ish_irri']
    perc_scbc = df['perc_scbc']
    return cs_ish*perc_scbc

def irri_scbc(df):
    return 0

# =SOMASE($B:$B;$B2;AU:AU)
def ire_cs_irri_eco(df):
    cobacia = df['COBACIA']
    cs_ish_scbc = df['cs_ish_scbc']
    return cs_ish_scbc.groupby(cobacia).transform('sum')


# pec_eco
# dependem da tabela PPM
def pec_bov(df):
    return 0
def pec_bub(df):
    return 0
def pec_sui(df):
    return 0
def pec_cap(df):
    return 0
def pec_ovi(df):
    return 0
def pec_gal(df):
    return 0
# =SOMA(Q2:V2)
def pec_total(df):
    resultado = pec_bov+pec_bub+pec_sui+pec_cap+pec_ovi+pec_gal
    return resultado

def pec_risco_iminente(df):
    return pec_total*fator_iminente

def pec_risco_pos_deficit(df):
    return pec_total*fator_pos_deficit
def pec_risco_total(df):
    return pec_total*fator_de_risco_total

# depende da tabela classificação
# =ARRAY_CONSTRAIN(ARRAYFORMULA(ÍNDICE(classificacao!$B$3:$F$7;CORRESP($Z2;classificacao!$A$3:$A$7;1);CORRESP($P2;classificacao!$B$2:$F$2;1))); 1; 1)
def cs_ish_urb(df):
    return 0

# depende da tabela demanda
# =SEERRO(ÍNDICE(demanda!$D:$D;CORRESP($B2;VALOR(ESQUERDA(demanda!$A:$A;15));0));0)
def deman_pecuaria(df):
    return 0

def densidade(df):
    return deman_pecuaria/area_otto
# =SE($H2<=10;$AF2*$AD2;0)
def deman_pecuaria_scbc(df):
    if situacao_setor <= 10:
        return densidade*area_setor
    else:
        return 0

def deman_pecuaria_otto(df):
    return deman_pecuaria_scbc.groupby(cobacia).transform('sum')

# =SEERRO(AG2/AE2;0)  
def perc_deman_pecuaria(df):
    return deman_pecuaria_scbc/deman_pecuaria

def cs_ish(df):
    return perc_deman_pecuaria*cs_ish_urb
def ire_cs_pec_eco(df):
    return cs_ish.groupby(cobacia).transform('sum')

# ind_eco
# =SEERRO(ÍNDICE(demanda!$D:$D;CORRESP($B3;VALOR(ESQUERDA(demanda!$A:$A;15));0));0)
# depende da tabela demanda
def deman_indus(df):
    return 0

# =ARRAY_CONSTRAIN(ARRAYFORMULA(ÍNDICE(classificacao!$B$3:$F$7;CORRESP(T3;classificacao!$A$3:$A$7;1);CORRESP($P3;classificacao!$B$2:$F$2;1))); 1; 1)
# depende da tabela classificacao
def ihu_cs_ish(df):
    return 0
# não é a mesma coisa que está no arquivo intermediário
# =SE($H3<=10;$Z3*$X3;0)
def pop_urb_scbc(df):
    if situacao_setor <= 10:
        return densidade*deman_indus
    else:
        return 0
# =SOMASE($B:$B;$B3;AA:AA)
def pop_urb_bacia(df):
    return pop_urb_scbc.groupby(cobacia).transform('sum')

# =SEERRO(AA3/Y3;0)
def perc_scbc(df):
    return pop_urb_scbc/deman_indus
def ihu_rel(df):
    return ihu_cs_ish*perc_scbc

def ire_cs_ind_eco(df):
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

def calcular_indicador(indicador, dados_calculados, functions_to_work, calculados=None):
    if calculados is None:
        calculados = set()
    
    # Se já foi calculado, retornar
    if indicador in dados_calculados.columns:
        return dados_calculados[indicador]

    # Encontrar a função
    item_func = next((item for item in functions_to_work 
                     if item['indicador'] == indicador), None)

    if not item_func:
        raise ValueError(f"Indicador {indicador} não encontrado")
    
    # Calcular dependências primeiro (recursivamente)
    parametros = []
    for dependencia in item_func['depends_on']:
        if dependencia in dados_calculados.columns:
            parametros.append(dados_calculados[dependencia])
        else:
            # Tentar como constante
            try:
                valor_constante = float(dependencia)
                coluna_constante = pd.Series([valor_constante] * len(dados_calculados),
                                            index=dados_calculados.index)
                parametros.append(coluna_constante)
            except (ValueError, TypeError):
                # É outro indicador, calcular recursivamente
                coluna_dep = calcular_indicador(dependencia, dados_calculados, 
                                               functions_to_work, calculados)
                parametros.append(coluna_dep)
    
    # Calcular o indicador atual
    funcao = globals()[indicador]
    resultado = funcao(parametros)
    # Armazenar resultado
    if 'column' in item_func:
        dados_calculados[item_func['column']] = resultado
    else:
        dados_calculados[indicador] = resultado
    
    return resultado