import pandas as pd
import numpy as np
import yaml
import sys

def bal_perc_cap(df, parametros=['dem_acm_cap', 'disp_q95_cap'], pesos=[1,1]):
    dem_acm = pd.to_numeric(df[parametros[0]].str.replace(',', '.'), errors='coerce')*pesos[0]
    disp_q95 = pd.to_numeric(df[parametros[1]].str.replace(',', '.'), errors='coerce')*pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [
                (disp_q95 == 0) & (dem_acm == 0),   # I3=0 E K3=0
                (disp_q95 == 0),                    # I3=0 (K3 != 0)
            ],
            [
                0,   # classificacao!$B$42
                999999,    # classificacao!$B$41
            ],
            default=100 * dem_acm / disp_q95,
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index) 

def bal_perc_bho(df, parametros=['dem_acm_bho', 'disp_q95_bho'], pesos=[1,1]):
    dem_acm = pd.to_numeric(df[parametros[0]].str.replace(',', '.'), errors='coerce')*pesos[0]
    disp_q95 = pd.to_numeric(df[parametros[1]].str.replace(',', '.'), errors='coerce')*pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [
                (disp_q95 == 0) & (dem_acm == 0),   # I3=0 E K3=0
                (disp_q95 == 0),                    # I3=0 (K3 != 0)
            ],
            [
                999999,   # classificacao!$B$42
                0,    # classificacao!$B$41
            ],
            default=100 * dem_acm / disp_q95,
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index) 

def disp_dem_cap(df, parametros=['bal_perc_cap'], pesos=[1]):
    bal_perc_cap = pd.to_numeric(df[parametros[0]], errors='coerce')*pesos[0]
    
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [
                (bal_perc_cap == 0),
            ],
            [
                999999,
            ],
            default= 100 / bal_perc_cap,
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)

def ft_imi(df, parametros=['disp_dem_cap'], pesos=[0.333333]):
    disp_dem_cap = df[parametros[0]]
    
    peso_disp_dem_cap = pesos[0]
    return np.where(
        disp_dem_cap >=1,
        peso_disp_dem_cap*(disp_dem_cap**(-2)),
        peso_disp_dem_cap*disp_dem_cap
    )


def ft_pd(df, parametros=['disp_dem_cap'], pesos=[1]):
    disp_dem_cap = df[parametros[0]]*pesos[0]
    
    return disp_dem_cap.apply(lambda x: 0 if x >= 1 else 1 - x)

def ft_tot(df, parametros=['ft_imi', 'ft_pd'], pesos=[1, 1]):
    ft_imi = df[parametros[0]]*pesos[0]
    ft_pd = df[parametros[1]]*pesos[1]
    
    return ft_imi + ft_pd

def ihu_nu_popriscoinerente(df, parametros=['ft_imi', 'dmu_nu_popurbana'], pesos=[1, 1]):
    ft_imi = df[parametros[0]]*pesos[0] 
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[1]
    
    resultado = ft_imi*dmu_nu_popurbana

    return resultado.round(2)

def ihu_pc_risco_inerente(df, parametros=['ihu_nu_popriscoinerente', 'dmu_nu_popurbana'], pesos=[1, 1]):
    ihu_nu_popriscoinerente = df[parametros[0]].fillna(0)*pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]], errors='coerce').fillna(0)*pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            dmu_nu_popurbana == 0,  # condição
            0,                                       # valor se for zero ou NaN
            ihu_nu_popriscoinerente/dmu_nu_popurbana # valor caso contrário
        )
    
    return resultado

def ihu_nu_popriscoposdeficit(df, parametros=['ft_pd', 'dmu_nu_popurbana'], pesos=[1, 1]):
    ft_pd = df[parametros[0]]*pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[1]

    resultado = ft_pd*dmu_nu_popurbana
    
    return resultado

def ihu_pc_riscoposdeficit(df, parametros=['ihu_nu_popriscoposdeficit', 'dmu_nu_popurbana'], pesos=[1, 1]):
    ihu_nu_popriscoposdeficit = df[parametros[0]]*pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            dmu_nu_popurbana == 0,  # condição
            0,                                       # valor se for zero ou NaN
            ihu_nu_popriscoposdeficit/dmu_nu_popurbana # valor caso contrário
        )

    return resultado

def ihu_nu_popriscototal(df, parametros=['ft_tot', 'dmu_nu_popurbana'], pesos=[1, 1]):
    ft_tot = df[parametros[0]]*pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[1]

    resultado = ft_tot*dmu_nu_popurbana
    
    return resultado

def ihu_pc_risco(df, parametros=['ihu_nu_popriscototal', 'dmu_nu_popurbana'], pesos=[1, 1]):
    ihu_nu_popriscototal = df[parametros[0]]*pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            dmu_nu_popurbana == 0,  # condição
            0,                                       # valor se for zero ou NaN
            ihu_nu_popriscototal/dmu_nu_popurbana # valor caso contrário
        )
    
    return resultado

def densidade(df, parametros=['pop', 'area_setor'], pesos=[1, 1]):
    pop = (df[parametros[0]]
                    .astype(str)
                    .str.replace(',', '.')
                    .str.replace('#DIV/0!', 'nan')
                    .str.replace('#N/A', 'nan')
                    .str.strip()
                    .pipe(pd.to_numeric, errors='coerce'))*pesos[0]
    area_setor = (df[parametros[1]]
                    .astype(str)
                    .str.replace(',', '.')
                    .str.replace('#DIV/0!', 'nan')
                    .str.replace('#N/A', 'nan')
                    .str.strip()
                    .pipe(pd.to_numeric, errors='coerce'))*pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            area_setor == 0,  # condição
            0,                                       # valor se for zero ou NaN
            pop/area_setor # valor caso contrário
        )

    return resultado

# cs_risco: busca de dados em matriz
def cs_risco(df, parametros=['ihu_nu_popriscototal', 'ihu_pc_risco'], pesos=[1, 1]):
    ihu_nu_popriscototal = df[parametros[0]]*pesos[0]
    ihu_pc_risco = df[parametros[1]]*pesos[1]
    
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

def cs_cobred(df, parametros=['ihu_pc_cobrede'], pesos=[1]):
    ihu_pc_cobrede = (df[parametros[0]]
                    .astype(str)
                    .str.replace(',', '.')
                    .str.replace('#DIV/0!', 'nan')
                    .str.replace('#N/A', 'nan')
                    .str.strip()
                    .pipe(pd.to_numeric, errors='coerce'))*pesos[0]

    bins = [-float('inf'), 0, 0.8, 0.9, 0.95, 0.98, 1, float('inf')]
    labels = [0, 1, 2, 3, 4, 5, 5]  
    return pd.cut(ihu_pc_cobrede.fillna(-1), bins=bins, labels=labels, right=False, ordered=False).astype(int)

def area_considerada_scbc(df, parametros=['situacao_setor', 'area_scbc', 'fator_analisavel'], pesos=[1, 3]):
    situacao_setor = pd.to_numeric(df[parametros[0]], errors='coerce')
    area_scbc = pd.to_numeric(df[parametros[1]].astype(str).str.replace(',', '.'), errors='coerce')*pesos[0]
    fator_analisavel = pesos[1]

    return np.where(
        situacao_setor <= fator_analisavel,
        area_scbc,
        0
    )

def area_considerada_bho(df, parametros=['cobacia', 'area_considerada_scbc'], pesos = [1]):
    cobacia = df[parametros[0]]
    area_considerada_scbc = df[parametros[1]]*pesos[0]
    resultado = area_considerada_scbc.groupby(cobacia).transform('sum')

    return resultado

def pop_urb_scbc(df, parametros=['densidade', 'area_considerada_scbc'], pesos=[1, 1]):
    densidade = df[parametros[0]]*pesos[0]
    area_considerada_scbc = df[parametros[1]]*pesos[1]

    return densidade*area_considerada_scbc

def pop_urb_bacia(df, parametros=['cobacia', 'pop_urb_scbc'], pesos=[1]):
    cobacia = df[parametros[0]]
    pop_urb_scbc = df[parametros[1]]*pesos[0]
    resultado = pop_urb_scbc.groupby(cobacia).transform('sum')

    return resultado

def perc_scbc(df, parametros=['pop_urb_scbc', 'pop_urb_bacia'], pesos=[1, 1]):
    pop_urb_scbc = pd.to_numeric(df[parametros[0]], errors='coerce')*pesos[0]
    pop_urb_bacia = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[1]
    
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [
                (pop_urb_scbc == 0) & (pop_urb_bacia == 0)
            ],
            [
                0,   # classificacao!$B$42
            ],
            default= pop_urb_scbc / pop_urb_bacia,
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index) 

def ihu_nu_popriscoinerente_scbc(df, parametros=['ft_imi', 'pop_urb_scbc'], pesos=[1,1]):
    ft_imi = pd.to_numeric(df[parametros[0]], errors='coerce')*pesos[0]
    pop_urb_scbc = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[1]

    return ft_imi*pop_urb_scbc

def ihu_nu_popriscoposdeficit_scbc(df, parametros=['ft_pd', 'pop_urb_scbc'], pesos=[1,1]):
    ft_pd = pd.to_numeric(df[parametros[0]], errors='coerce')*pesos[0]
    pop_urb_scbc = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[1]

    return ft_pd*pop_urb_scbc

def ihu_nu_popriscototal_scbc(df, parametros=['ft_tot', 'pop_urb_scbc'], pesos=[1,1]):
    ft_tot = pd.to_numeric(df[parametros[0]], errors='coerce')*pesos[0]
    pop_urb_scbc = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[1]

    return ft_tot*pop_urb_scbc

def ihu_cs_ish(df, parametros=['cs_cobred', 'cs_risco'], pesos=[0.7, 0.3]):
    cs_risco = df[parametros[0]]
    cs_cobred = df[parametros[1]]

    resultado = np.where(
        cs_cobred < cs_risco,
        pesos[0] * cs_risco + pesos[1] * cs_cobred,
        cs_risco
    )

    return pd.Series(resultado)
    
def ihu_rel_pop(df, parametros=['perc_scbc', 'cs_risco'], pesos=[1, 1]):
    perc_scbc = df[parametros[0]]*pesos[0]
    cs_risco = df[parametros[1]]*pesos[1]
    return perc_scbc*cs_risco

def ihu_rel_cobred(df, parametros=['perc_scbc', 'cs_cobred'], pesos=[1, 1]):
    perc_scbc = df[parametros[0]]*pesos[0]
    cs_cobred = df[parametros[1]]*pesos[1]
    return perc_scbc*cs_cobred

def ihu_nu_popriscoinerente_otto(df, parametros=['cobacia', 'ihu_nu_popriscoinerente_scbc'], pesos=[1,1]):
    cobacia = df['cobacia']
    ihu_nu_popriscoinerente_scbc = df[parametros[1]]*pesos[0]
    resultado = ihu_nu_popriscoinerente_scbc.groupby(cobacia).transform('sum')

    return resultado

def ihu_nu_popriscoposdeficit_otto(df, parametros=['cobacia', 'ihu_nu_popriscoposdeficit_scbc'], pesos=[1,1]):
    cobacia = df['cobacia']
    ihu_nu_popriscoposdeficit_scbc = df[parametros[1]]*pesos[0]
    resultado = ihu_nu_popriscoposdeficit_scbc.groupby(cobacia).transform('sum')

    return resultado

def ihu_nu_popriscototal_otto(df, parametros=['cobacia', 'ihu_nu_popriscototal_scbc'], pesos=[1,1]):
    cobacia = df['cobacia']
    ihu_nu_popriscototal_scbc = df[parametros[1]]*pesos[0]
    resultado = ihu_nu_popriscototal_scbc.groupby(cobacia).transform('sum')

    return resultado

def ire_hu_pop(df, parametros=['cobacia', 'ihu_rel_pop'], pesos=[1]):
    cobacia = df['cobacia']
    ihu_rel_pop = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[0]
    
    return ihu_rel_pop.groupby(cobacia).transform('sum')
    
def ire_hu_cobred(df, parametros=['cobacia', 'ihu_rel_cobred'], pesos=[1]):
    cobacia = df['cobacia']
    ihu_rel_cobred = pd.to_numeric(df[parametros[1]], errors='coerce')*pesos[0]
    
    return ihu_rel_cobred.groupby(cobacia).transform('sum')

def ire_cs_hum(ire_hu_pop, peso_ire_hu_pop, ire_hu_cobred, peso_ire_hu_cobred):
    impacto_hu_cobred = ire_hu_cobred*peso_ire_hu_cobred
    impacto_hu_pop    = ire_hu_pop*peso_ire_hu_pop
    
    if ire_hu_cobred < ire_hu_pop:
        return impacto_hu_cobred + impacto_hu_pop
    else:
        return ire_hu_pop