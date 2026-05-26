import pandas as pd
import numpy as np
import yaml
import sys

def disp_por_dem(parametros):
    bal_perc_series = parametros[0]
    return np.where((pd.isna(bal_perc_series)) | (bal_perc_series == 0), 0, 100/bal_perc_series)

def fator_iminente(parametros):
    disp_dem = parametros[0]
    return np.where(
        disp_dem >=1,
        (1/3)*(disp_dem**(-2)),
        (1/3)*(disp_dem)
    )

def fator_pos_deficit(parametros):
    disp_dem = parametros[0]
    
    return disp_dem.apply(lambda x: 0 if x >= 1 else 1 - x)

def fator_de_risco_total(parametros):
    fator_iminente = parametros[0]
    fator_pos_deficit = parametros[1]
    return fator_iminente + fator_pos_deficit

def ihu_nu_popriscoinerente(parametros):
    fator_iminente = parametros[0] 
    dmu_nu_popurbana = parametros[1]

    fator_iminente = fator_iminente.fillna(0)
    dmu_nu_popurbana = dmu_nu_popurbana.fillna(0)
    
    resultado = fator_iminente + dmu_nu_popurbana
    
    resultado = resultado.where(np.isfinite(resultado), 0)

    return resultado.round(2)

def ihu_pc_risco_inerente(parametros):
    ihu_nu_popriscoinerente = parametros[0]
    dmu_nu_popurbana = parametros[1]

    ihu_nu_popriscoinerente = ihu_nu_popriscoinerente.fillna(0)
    dmu_nu_popurbana = dmu_nu_popurbana.fillna(0)

    resultado = ihu_nu_popriscoinerente/dmu_nu_popurbana

    resultado = resultado.where(np.isfinite(resultado), 0)
    
    return resultado.round(2)

def ihu_nu_popriscoposdeficit(parametros):
    fator_pos_deficit = parametros[0]
    dmu_nu_popurbana = parametros[1]

    fator_pos_deficit = fator_pos_deficit.fillna(0)
    dmu_nu_popurbana = dmu_nu_popurbana.fillna(0)

    resultado = fator_pos_deficit*dmu_nu_popurbana

    resultado = resultado.where(np.isfinite(resultado), 0)
    
    return resultado.round(2)

def ihu_pc_riscoposdeficit(parametros):
    ihu_nu_popriscoposdeficit = parametros[0]
    dmu_nu_popurbana = parametros[1]

    ihu_nu_popriscoposdeficit = ihu_nu_popriscoposdeficit.fillna(0)
    dmu_nu_popurbana = dmu_nu_popurbana.fillna(0)

    resultado = ihu_nu_popriscoposdeficit/dmu_nu_popurbana
    resultado = resultado.where(np.isfinite(resultado), 0)
    
    return resultado.round(2)

def ihu_nu_popriscototal(parametros):
    fator_de_risco_total = parametros[0]
    dmu_nu_popurbana = parametros[1]
    
    fator_de_risco_total = fator_de_risco_total.fillna(0)
    dmu_nu_popurbana = dmu_nu_popurbana.fillna(0)

    resultado = fator_de_risco_total*dmu_nu_popurbana
    resultado = resultado.where(np.isfinite(resultado), 0)
    
    return resultado.round(2)

def ihu_pc_risco(parametros):
    ihu_nu_popriscototal = parametros[0]
    dmu_nu_popurbana = parametros[1]
    
    ihu_nu_popriscototal = ihu_nu_popriscototal.fillna(0)
    dmu_nu_popurbana = dmu_nu_popurbana.fillna(0)

    resultado = ihu_nu_popriscototal/dmu_nu_popurbana
    resultado = resultado.where(np.isfinite(resultado), 0)
    
    return resultado.round(2)

def densidade(parametros):
    pop = parametros[0]
    area_setor = parametros[1]

    pop = pop.fillna(0)
    area_setor = area_setor.fillna(0)

    resultado = pop/area_setor
    resultado = resultado.where(np.isfinite(resultado), 0)
    
    return resultado.round(2)

# cs_risco: busca de dados em matriz
def cs_risco(parametros):
    ihu_nu_popriscototal = parametros[0]
    ihu_pc_risco = parametros[1]
    
    bins_pop = [-float('inf'), 0, 2000, 5000, 10000, 50000, float('inf')]
    labels_pop = [0, 0, 1, 2, 3, 4]
    idx_pop = pd.cut(ihu_nu_popriscototal.fillna(-1), bins=bins_pop, labels=labels_pop, right=False, ordered=False).astype(int)
    
    # Define os bins e labels para pc_risco
    bins_risco = [-float('inf'), 0, 0.2, 0.4, 0.6, 0.8, float('inf')]
    labels_risco = [0, 0, 1, 2, 3, 4]
    idx_risco = pd.cut(ihu_pc_risco.fillna(-1), bins=bins_risco, labels=labels_risco, right=False, ordered=False).astype(int)
    
    # Matriz de risco
    matriz_risco = [
        [5, 5, 4, 4, 3],
        [5, 4, 3, 3, 2],
        [4, 3, 3, 2, 2],
        [4, 3, 2, 2, 1],
        [3, 2, 2, 1, 1]
    ]
    
    # Mapeia os valores usando numpy
    resultado = np.array([matriz_risco[i][j] for i, j in zip(idx_pop, idx_risco)])
    
    return pd.Series(resultado)

def cs_cobred(parametros):
    bins = [-float('inf'), 0, 0.8, 0.9, 0.95, 0.98, 1, float('inf')]
    labels = [0, 1, 2, 3, 4, 5, 0]
    return pd.cut(ihu_pc_cobrede.fillna(-1), bins=bins, labels=labels, right=False).astype(int)

def perc_scbc(parametros):
    pop_urb_scbc = parametros[0]
    pop_urb_bacia = parametros[1]

    pop_urb_scbc = pop_urb_scbc.fillna(0)
    pop_urb_bacia = pop_urb_bacia.fillna(0)
    
    resultado = pop_urb_scbc / pop_urb_bacia
    resultado = resultado.where(np.isfinite(resultado), 0)
    
    return resultado.round(2)

def ihu_cs_ish(parametros):
    cs_risco = parametros[0]
    peso_cs_risco = parametros[1]
    cs_cobred = parametros[2]
    peso_cs_cobred = parametros[3]
    
    if cs_cobred < cs_risco:
        return peso_cs_risco*cs_risco + peso_cs_cobred*cs_cobred
    else:
        return cs_risco

def ihu_rel_pop(parametros):
    perc_scbc = parametros[0]
    cs_risco = parametros[1]
    return perc_scbc*cs_risco

def ihu_rel_cobred(parametros):
    perc_scbc = parametros[0]
    cs_cobred = parametros[1]
    return perc_scbc*cs_cobred

# TODO: adaptar essas funções
def ire_hu_pop(parametros):
    return round(df.groupby('COBACIA')[ihu_rel_pop].transform('sum'),2)

def ire_hu_cobred(parametros):
    return round(df.groupby('COBACIA')[ihu_rel_cobred].transform('sum'),2)

def ire_cs_hum(parametros):
    ire_hu_pop = parametros[0]
    peso_ire_hu_pop = parametros[1]
    ire_hu_cobred = parametros[2]
    peso_ire_hu_cobred = parametros[3]

    if ire_hu_cobred < ire_hu_pop:
        return peso_cs_risco*ire_hu_pop + peso_cs_cobred*ire_hu_cobred
    else:
        return ire_hu_pop

def pop_urb_scbc_ind(parametros):
    situacao_setor = parametros[0]
    densidade = parametros[1]
    area_scbc = parametros[2]
    
    return np.where(
        situacao_setor <= 10,
        densidade*area_scbc,
        0
    )

def pop_urb_bacia(parametros):
    return 0
    
def perc_scbc_ind(parametros):
    pop_urb_scbc = parametros[0]
    deman_indus = parametros[1]
    
    pop_urb_scbc = pop_urb_scbc.fillna(0)
    deman_indus = deman_indus.fillna(0)
    
    resultado = pop_urb_scbc / deman_indus
    resultado = resultado.where(np.isfinite(resultado), 0)
    
    return resultado.round(2)

def igh_ind(parametros):
    disp_q95 = parametros[0]
    deman_indus = parametros[1]

    disp_q95 = disp_q95.fillna(0)
    deman_indus = deman_indus.fillna(0)

    resultado = disp_q95/deman_indus
    resultado = resultado.where(np.isfinite(resultado), 0)
    
    return resultado.round(2)

def ihu_rel(parametros):
    perc_scbc = parametros[0]
    ihu_cs_ish = parametros[1]

    resultado = perc_scbc*ihu_cs_ish

    return resultado.round(2)

def ire_cs_hum_ind(parametros):
    return 0

def list_functions(dimensao):
    return_list = []
    
    for item in dimensao['indicadores']:
        if item == None:
            continue

        nome_funcao = item['indicador']

        # Verifica se a função existe no módulo importado
        if nome_funcao in globals() and callable(globals()[nome_funcao]):
            return_list.append(item)
        # else:
            # print(f"  ✗ Função '{nome_funcao}' NÃO encontrada em convertion_functions")

    return return_list
