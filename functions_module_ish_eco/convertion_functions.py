import pandas as pd
import numpy as np
import yaml
import sys

# irri_eco
# funcoes dependem de tabela PAM
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
    return 0
def irri_arroz_risco_pos_deficit(df):
    return 0
def irri_arroz_risco_total(df):
    return 0
def irri_cafe_risco_iminente(df):
    return 0
def irri_cafe_risco_pos_deficit(df):
    return 0
def irri_cafe_risco_total(df):
    return 0
def irri_cana_risco_iminente(df):
    return 0
def irri_cana_risco_pos_deficit(df):
    return 0
def irri_cana_risco_total(df):
    return 0
def irri_oc_risco_iminente(df):
    return 0
def irri_oc_risco_pos_deficit(df):
    return 0
def irri_oc_risco_total(df):
    return 0
def irri_total_risco_iminente(df):
    return 0
def irri_total_risco_pos_deficit(df):
    return 0
def irri_total_risco_total(df):
    return 0
def cs_ish(df):
    return 0
def deman_agri(df):
    return 0
def densidade(df):
    return 0
def deman_agri_scbc(df):
    return 0
def deman_agri_otto(df):
    return 0
def perc_scbc(df):
    return 0
def irri_risco_scbc(df):
    return 0
def cs_ish_scbc(df):
    return 0
def irri_scbc(df):
    return 0
def ire_cs_irri_eco(df):
    return 0


# pec_eco
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
def pec_total(df):
    return 0
def pec_risco_iminente(df):
    return 0
def pec_risco_pos_deficit(df):
    return 0
def pec_risco_total(df):
    return 0
def cs_ish_urb(df):
    return 0
def deman_pecuaria(df):
    return 0
def densidade(df):
    return 0
def deman_pecuaria_scbc(df):
    return 0
def deman_pecuaria_otto(df):
    return 0
def perc_deman_pecuaria(df):
    return 0
def cs_ish(df):
    return 0
def ire_cs_pec_eco(df):
    return 0

# ind_eco
def deman_indus(df):
    return 0
def pop_urb_scbc(df): # conferir se está em arquivo intermediário
    return 0
def pop_urb_bacia(df):
    return 0
def perc_scbc(df):
    return 0
def ihu_rel(df):
    return 0
def ire_cs_ind_eco(df):
    return 0

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