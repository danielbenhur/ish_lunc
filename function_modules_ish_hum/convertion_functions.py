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

    fator_iminente = 0 if pd.isna(fator_iminente) else fator_iminente
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana
    
    resultado = fator_iminente + dmu_nu_popurbana
    
    if not np.isfinite(resultado): 
        resultado = 0
    
    return round(resultado,2)

def ihu_pc_risco_inerente(parametros):
    ihu_nu_popriscoinerente = parametros[0]
    dmu_nu_popurbana = parametros[1]

    ihu_nu_popriscoinerente = 0 if pd.isna(ihu_nu_popriscoinerente) else ihu_nu_popriscoinerente
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana

    resultado = ihu_nu_popriscoinerente/dmu_nu_popurbana

    if not np.isfinite(resultado):
        resultado = 0
    
    return round(resultado,2)

def ihu_nu_popriscoposdeficit(parametros):
    fator_pos_deficit = parametros[0]
    dmu_nu_popurbana = parametros[1]

    fator_pos_deficit = 0 if pd.isna(fator_pos_deficit) else fator_pos_deficit
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana

    resultado = fator_pos_deficit*dmu_nu_popurbana

    if not np.isfinite(resultado):
        resultado = 0
    
    return round(resultado,2)

def ihu_pc_riscoposdeficit(parametros):
    ihu_nu_popriscoposdeficit = parametros[0]
    dmu_nu_popurbana = parametros[1]

    ihu_nu_popriscoposdeficit = 0 if pd.isna(ihu_nu_popriscoposdeficit) else ihu_nu_popriscoposdeficit
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana

    resultado = ihu_nu_popriscoposdeficit/dmu_nu_popurbana
    if not np.isfinite(resultado):
        resultado = 0
    
    return round(resultado,2)

def ihu_nu_popriscototal(parametros):
    fator_de_risco_total = parametros[0]
    dmu_nu_popurbana = parametros[1]
    
    fator_de_risco_total = 0 if pd.isna(fator_de_risco_total) else fator_de_risco_total
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana

    resultado = fator_de_risco_total*dmu_nu_popurbana
    if not np.isfinite(resultado):
        resultado = 0
    
    return round(resultado,2)

def ihu_pc_risco(parametros):
    ihu_nu_popriscototal = parametros[0]
    dmu_nu_popurbana = parametros[1]
    
    ihu_nu_popriscototal = 0 if pd.isna(ihu_nu_popriscototal) else ihu_nu_popriscototal
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana

    resultado = ihu_nu_popriscototal/dmu_nu_popurbana
    if not np.isfinite(resultado):
        resultado = 0
    
    return round(resultado,2)

def densidade(parametros):
    pop = parametros[0]
    area_setor = parametros[1]

    pop = 0 if pd.isna(pop) else pop
    area_setor = 0 if pd.isna(area_setor) else area_setor

    resultado = pop/area_setor
    if not np.isfinite(resultado):
        resultado = 0
  
    return round(resultado,2)

# cs_risco: busca de dados em matriz
def cs_risco(parametros):
    ihu_nu_popriscototal = parametros[0]
    ihu_pc_risco = parametros[1]
    
    matriz_risco = [
            #    0% 20% 40% 60% 80%
                [5, 5, 4, 4, 3],  # 0
                [5, 4, 3, 3, 2],  # 2000
                [4, 3, 3, 2, 2],  # 5000
                [4, 3, 2, 2, 1],  # 10000
                [3, 2, 2, 1, 1]   # 50000
    ]
    
    # Define os índices manualmente
    if pd.isna(ihu_nu_popriscototal) or ihu_nu_popriscototal < 0:
        idx_pop = 0
    elif ihu_nu_popriscototal < 2000:
        idx_pop = 0
    elif ihu_nu_popriscototal < 5000:
        idx_pop = 1
    elif ihu_nu_popriscototal < 10000:
        idx_pop = 2
    elif ihu_nu_popriscototal < 50000:
        idx_pop = 3
    else:
        idx_pop = 4
    
    if pd.isna(ihu_pc_risco) or ihu_pc_risco < 0:
        idx_risco = 0
    elif ihu_pc_risco < 0.2:
        idx_risco = 0
    elif ihu_pc_risco < 0.4:
        idx_risco = 1
    elif ihu_pc_risco < 0.6:
        idx_risco = 2
    elif ihu_pc_risco < 0.8:
        idx_risco = 3
    else:
        idx_risco = 4
    
    return matriz_risco[idx_pop][idx_risco]

def cs_cobred(parametros):
    if pd.isna(ihu_pc_cobrede):
        return 0
    if ihu_pc_cobrede < 0.8:
        return 1
    if ihu_pc_cobrede < 0.9:
        return 2
    if ihu_pc_cobrede < 0.95:
        return 3
    if ihu_pc_cobrede < 0.98:
        return 4
    if ihu_pc_cobrede <= 1:
        return 5
    return 0 

def perc_scbc(parametros):
    pop_urb_scbc = parametros[0]
    pop_urb_bacia = parametros[1]

    pop_urb_scbc = 0 if pd.isna(pop_urb_scbc) else pop_urb_scbc
    pop_urb_bacia = 0 if pd.isna(pop_urb_bacia) else pop_urb_bacia

    if pop_urb_bacia == 0:
        return 0.0
    
    resultado = pop_urb_scbc / pop_urb_bacia
    
    if not np.isfinite(resultado):
        return 0.0
    
    return round(resultado, 2)

def ihu_cs_ish(parametros):
    cs_risco = parametros[0]
    cs_cobred = parametros[1]
    
    if cs_cobred < cs_risco:
        return peso_cs_risco*cs_risco + peso_cs_cobred*cs_cobred
    else:
        return cs_risco

def ihu_rel_pop(parametros):
    return perc_scbc*cs_risco

def ihu_rel_cobred(parametros):
    return perc_scbc*cs_cobred

def ire_hu_pop(parametros):
    return round(df.groupby('COBACIA')[ihu_rel_pop].transform('sum'),2)

def ire_hu_cobred(parametros):
    return round(df.groupby('COBACIA')[ihu_rel_cobred].transform('sum'),2)

def ire_cs_hum(parametros):
    ire_hu_pop = parametros[0]
    ire_hu_cobred = parametros[1]

    if ire_hu_cobred < ire_hu_pop:
        return peso_cs_risco*ire_hu_pop + peso_cs_cobred*ire_hu_cobred
    else:
        return ire_hu_pop

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
