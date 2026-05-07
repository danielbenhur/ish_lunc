import pandas as pd
import numpy as np

def disp_dem(bal_perc: float):
    if pd.isna(bal_perc) or bal_perc == 0:
        return 0
    else:
        return 100/bal_perc

def fator_iminente(disp_dem: float):
    if disp_dem >= 1:
        return (1/3) * (disp_dem ** (-2))
    else:
        return (1/3) * (disp_dem ** 1)

def fator_pos_deficit(disp_dem:float):
    if disp_dem >= 1:
        return 0
    else:
        return 1-disp_dem

def ihu_nu_popriscoinerente(row: pd.DataFrame):
    fator_iminente = row['fator_iminente'] 
    dmu_nu_popurbana = row['dmu_nu_popurbana']

    fator_iminente = 0 if pd.isna(fator_iminente) else fator_iminente
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana
    
    resultado = fator_iminente + dmu_nu_popurbana
    
    if not np.isfinite(resultado): 
        resultado = 0
    
    return round(resultado,2)

def ihu_pc_risco_inerente(row: pd.DataFrame):
    ihu_nu_popriscoinerente = row['ihu_nu_popriscoinerente']
    dmu_nu_popurbana = row['dmu_nu_popurbana']

    ihu_nu_popriscoinerente = 0 if pd.isna(ihu_nu_popriscoinerente) else ihu_nu_popriscoinerente
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana

    resultado = ihu_nu_popriscoinerente/dmu_nu_popurbana

    if not np.isfinite(resultado):
        resultado = 0
    
    return round(resultado,2)

def ihu_nu_popriscoposdeficit(row: pd.DataFrame):
    fator_pos_deficit = row['fator_pós_deficit']
    dmu_nu_popurbana = row['dmu_nu_popurbana']

    fator_pos_deficit = 0 if pd.isna(fator_pos_deficit) else fator_pos_deficit
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana

    resultado = fator_pos_deficit*dmu_nu_popurbana

    if not np.isfinite(resultado):
        resultado = 0
    
    return round(resultado,2)

def ihu_pc_riscoposdeficit(row: pd.DataFrame):
    ihu_nu_popriscoposdeficit = row['ihu_nu_popriscoposdeficit']
    dmu_nu_popurbana = row['dmu_nu_popurbana']

    ihu_nu_popriscoposdeficit = 0 if pd.isna(ihu_nu_popriscoposdeficit) else ihu_nu_popriscoposdeficit
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana

    resultado = ihu_nu_popriscoposdeficit/dmu_nu_popurbana
    if not np.isfinite(resultado):
        resultado = 0
    
    return round(resultado,2)

def ihu_nu_popriscototal(row: pd.DataFrame):
    fator_de_risco_total = row['fator_de_risco_total']
    dmu_nu_popurbana = row['dmu_nu_popurbana']
    
    fator_de_risco_total = 0 if pd.isna(fator_de_risco_total) else fator_de_risco_total
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana

    resultado = fator_de_risco_total*dmu_nu_popurbana
    if not np.isfinite(resultado):
        resultado = 0
    
    return round(resultado,2)

def ihu_pc_risco(row: pd.DataFrame):
    ihu_nu_popriscototal = row['ihu_nu_popriscototal']
    dmu_nu_popurbana = row['dmu_nu_popurbana']
    
    ihu_nu_popriscototal = 0 if pd.isna(ihu_nu_popriscototal) else ihu_nu_popriscototal
    dmu_nu_popurbana = 0 if pd.isna(dmu_nu_popurbana) else dmu_nu_popurbana

    resultado = ihu_nu_popriscototal/dmu_nu_popurbana
    if not np.isfinite(resultado):
        resultado = 0
    
    return round(resultado,2)

def densidade(row: pd.DataFrame):
    pop = row['pop']
    area_setor = row['area_setor']

    pop = 0 if pd.isna(pop) else pop
    area_setor = 0 if pd.isna(area_setor) else area_setor

    resultado = pop/area_setor
    if not np.isfinite(resultado):
        resultado = 0
  
    return round(resultado,2)

# cs_risco: busca de dados em matriz
def cs_risco(row: pd.DataFrame):
    ihu_nu_popriscototal = row['ihu_nu_popriscototal']
    ihu_pc_risco = row['ihu_pc_risco']
    
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

def cs_cobred(ihu_pc_cobrede: float):
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

def perc_scbc(row: pd.DataFrame):
    pop_urb_scbc = row['pop_urb_scbc']
    pop_urb_bacia = row['pop_urb_bacia']

    pop_urb_scbc = 0 if pd.isna(pop_urb_scbc) else pop_urb_scbc
    pop_urb_bacia = 0 if pd.isna(pop_urb_bacia) else pop_urb_bacia

    if pop_urb_bacia == 0:
        return 0.0
    
    resultado = pop_urb_scbc / pop_urb_bacia
    
    if not np.isfinite(resultado):
        return 0.0
    
    return round(resultado, 2)

def ihu_cs_ish(row: pd.DataFrame, peso_cs_risco: float, peso_cs_cobred: float):
    cs_risco = row['cs_risco']
    cs_cobred = row['cs_cobred']
    
    if cs_cobred < cs_risco:
        return peso_cs_risco*cs_risco + peso_cs_cobred*cs_cobred
    else:
        return cs_risco

def ire_cs_hum(row: pd.DataFrame, peso_cs_risco: float, peso_cs_cobred: float):
    ire_hu_pop = row['ire_hu_pop']
    ire_hu_cobred = row['ire_hu_cobred']

    if ire_hu_cobred < ire_hu_pop:
        return peso_cs_risco*ire_hu_pop + peso_cs_cobred*ire_hu_cobred
    else:
        return ire_hu_pop