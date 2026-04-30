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