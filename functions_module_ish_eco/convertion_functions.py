import pandas as pd
import numpy as np
import yaml
import sys

# irri_eco
# funcoes dependem de tabela PAM (extra)
def irri_arroz(df):
    return 0
def irri_cafe(df):
    return 0
def irri_cana(df):
    return 0
def irri_oc(df):
    return 0
def irri_total(df):
    return 0

# derivados das dependentes de PAM
def irri_arroz_risco_iminente(df):
    irri_arroz = df['irri_arroz']
    fator_iminente = df['fator_iminente']
    return irri_arroz*fator_iminente

def irri_arroz_risco_pos_deficit(df):
    irri_arroz = df['irri_arroz']
    fator_pos_deficit = df['fator_pos_deficit']
    return irri_arroz*fator_iminente

def irri_arroz_risco_total(df):
    irri_arroz = df['irri_arroz']
    fator_de_risco_total = df['fator_de_risco_total']
    return irri_arroz*fator_de_risco_total

def irri_cafe_risco_iminente(df):
    irri_cafe = df['irri_cafe']
    fator_iminente = df['fator_iminente']
    return irri_cafe*fator_iminente

def irri_cafe_risco_pos_deficit(df):
    irri_cafe = df['irri_cafe']
    fator_pos_deficit = df['fator_pos_deficit']
    return irri_cafe*fator_iminente

def irri_cafe_risco_total(df):
    irri_cafe = df['irri_cafe']
    fator_de_risco_total = df['fator_de_risco_total']
    return irri_cafe*fator_de_risco_total

def irri_cana_risco_iminente(df):
    irri_cana = df['irri_cana']
    fator_iminente = df['fator_iminente']
    return irri_cana*fator_iminente

def irri_cana_risco_pos_deficit(df):
    irri_cana = df['irri_cana']
    fator_pos_deficit = df['fator_pos_deficit']
    return irri_cana*fator_iminente

def irri_cana_risco_total(df):
    irri_cana = df['irri_cana']
    fator_de_risco_total = df['fator_de_risco_total']
    return irri_cana*fator_de_risco_total

def irri_oc_risco_iminente(df):
    irri_oc = df['irri_oc']
    fator_iminente = df['fator_iminente']
    return irri_oc*fator_iminente

def irri_oc_risco_pos_deficit(df):
    irri_oc = df['irri_oc']
    fator_pos_deficit = df['fator_pos_deficit']
    return irri_oc*fator_pos_deficit

def irri_oc_risco_total(df):
    irri_oc = df['irri_oc']
    fator_de_risco_total = df['fator_de_risco_total']
    return irri_oc*fator_de_risco_total

def irri_total_risco_iminente(df):
    irri_total = df['irri_total']
    fator_iminente = df['fator_iminente']
    return irri_total*fator_iminente

def irri_total_risco_pos_deficit(df):
    irri_total = df['irri_total']
    fator_pos_deficit = df['fator_pos_deficit']
    return irri_total*fator_pos_deficit

def irri_total_risco_total(df):
    irri_total = df['irri_total']
    fator_de_risco_total = df['fator_de_risco_total']
    return irri_total*fator_de_risco_total

# depende da tabela classificação (extra)
def cs_ish(df):
    return 0
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
    cs_ish = df['cs_ish']
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