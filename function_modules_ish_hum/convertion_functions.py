import pandas as pd
import numpy as np

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