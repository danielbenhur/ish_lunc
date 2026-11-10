import pandas as pd
import numpy as np
import yaml
import sys


def _aplicar_value(df, value):
    """Normaliza o parâmetro value para uma Series alinhada ao df (ou None)."""
    if value is None:
        return None
    if isinstance(value, pd.Series):
        return value.reindex(df.index)
    return pd.Series(value, index=df.index)

def disp_q95_cap_2(df, parametros=['disp_q95_cap'], pesos=[1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v

    # Base: valor original de disp_q95_cap como numérico
    disp_q95_cap = (df[parametros[0]]
                    .astype(str)
                    .str.replace(',', '.')
                    .str.replace('#DIV/0!', 'nan')
                    .str.replace('#N/A', 'nan')
                    .str.strip()
                    .pipe(pd.to_numeric, errors='coerce')) * pesos[0]

    # Máscara: True onde o município é Vila Velha
    if 'mun_nm' in df.columns:
        mascara_vila_velha = df['mun_nm'].astype(str).str.strip() == 'Vila Velha'
    else:
        mascara_vila_velha = pd.Series(False, index=df.index)

    # Soma 1 apenas em Vila Velha
    resultado = disp_q95_cap + mascara_vila_velha.astype(float)

    return resultado
    

def bal_perc_cap(df, parametros=['dem_acm_cap', 'disp_q95_cap_2'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    dem_acm = pd.to_numeric(df[parametros[0]].str.replace(',', '.'), errors='coerce') * pesos[0]
    # disp_q95 = pd.to_numeric(df[parametros[1]].str.replace(',', '.'), errors='coerce') * pesos[1]
    disp_q95 = df[parametros[1]]
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [
                (disp_q95 == 0) & (dem_acm == 0),
                (disp_q95 == 0),
            ],
            [
                0,
                999999,
            ],
            default=100 * dem_acm / disp_q95,
        )

    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)


def bal_perc_bho(df, parametros=['dem_acm_bho', 'disp_q95_bho'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    dem_acm = pd.to_numeric(df[parametros[0]].str.replace(',', '.'), errors='coerce') * pesos[0]
    disp_q95 = pd.to_numeric(df[parametros[1]].str.replace(',', '.'), errors='coerce') * pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [
                (disp_q95 == 0) & (dem_acm == 0),
                (disp_q95 == 0),
            ],
            [
                999999,
                0,
            ],
            default=100 * dem_acm / disp_q95,
        )

    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)


def disp_dem_cap(df, parametros=['bal_perc_cap'], pesos=[1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    bal_perc_cap_ = pd.to_numeric(df[parametros[0]], errors='coerce') * pesos[0]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [(bal_perc_cap_ == 0)],
            [999999],
            default=100 / bal_perc_cap_,
        )

    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)


def ft_imi(df, parametros=['disp_dem_cap'], pesos=[0.333333], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    disp_dem_cap_ = df[parametros[0]]
    peso = pesos[0]
    return np.where(
        disp_dem_cap_ >= 1,
        peso * (disp_dem_cap_ ** (-2)),
        peso * disp_dem_cap_,
    )


def ft_pd(df, parametros=['disp_dem_cap'], pesos=[1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    disp_dem_cap_ = df[parametros[0]] * pesos[0]
    return disp_dem_cap_.apply(lambda x: 0 if x >= 1 else 1 - x)


def ft_tot(df, parametros=['ft_imi', 'ft_pd'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ft_imi_ = df[parametros[0]] * pesos[0]
    ft_pd_ = df[parametros[1]] * pesos[1]
    return ft_imi_ + ft_pd_


def ihu_nu_popriscoinerente(df, parametros=['ft_imi', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ft_imi_ = df[parametros[0]] * pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]].str.replace('.', ''), errors='coerce') * pesos[1]
    return (ft_imi_ * dmu_nu_popurbana).round(2)


def ihu_pc_risco_inerente(df, parametros=['ihu_nu_popriscoinerente', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ihu_nu_popriscoinerente_ = df[parametros[0]].fillna(0) * pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]].str.replace('.', ''), errors='coerce') * pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            dmu_nu_popurbana == 0,
            0,
            ihu_nu_popriscoinerente_ / dmu_nu_popurbana,
        )
    return resultado


def ihu_nu_popriscoposdeficit(df, parametros=['ft_pd', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ft_pd_ = df[parametros[0]] * pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]].str.replace('.', ''), errors='coerce') * pesos[1]
    return ft_pd_ * dmu_nu_popurbana


def ihu_pc_riscoposdeficit(df, parametros=['ihu_nu_popriscoposdeficit', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ihu_nu_popriscoposdeficit_ = df[parametros[0]] * pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]].str.replace('.', ''), errors='coerce') * pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            dmu_nu_popurbana == 0,
            0,
            ihu_nu_popriscoposdeficit_ / dmu_nu_popurbana,
        )
    return resultado


def ihu_nu_popriscototal(df, parametros=['ft_tot', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ft_tot_ = df[parametros[0]] * pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]].str.replace('.', ''), errors='coerce') * pesos[1]
    return ft_tot_ * dmu_nu_popurbana


def ihu_pc_risco(df, parametros=['ihu_nu_popriscototal', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ihu_nu_popriscototal_ = df[parametros[0]] * pesos[0]
    dmu_nu_popurbana = pd.to_numeric(df[parametros[1]].str.replace('.', ''), errors='coerce') * pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            dmu_nu_popurbana == 0,
            0,
            ihu_nu_popriscototal_ / dmu_nu_popurbana,
        )
    return resultado


def densidade(df, parametros=['pop', 'area_setor'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    pop = (df[parametros[0]]
           .astype(str)
           .str.replace(',', '.')
           .str.replace('#DIV/0!', 'nan')
           .str.replace('#N/A', 'nan')
           .str.strip()
           .pipe(pd.to_numeric, errors='coerce')) * pesos[0]
    area_setor = (df[parametros[1]]
                  .astype(str)
                  .str.replace(',', '.')
                  .str.replace('#DIV/0!', 'nan')
                  .str.replace('#N/A', 'nan')
                  .str.strip()
                  .pipe(pd.to_numeric, errors='coerce')) * pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [
                (area_setor == 0) & (pop == 0),
                (area_setor == 0),
            ],
            [
                0,
                10000000,
            ],
            default=round(pop / area_setor, 3),
        )
    return resultado


def cs_risco(df, parametros=['ihu_nu_popriscototal', 'ihu_pc_risco'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ihu_nu_popriscototal_ = df[parametros[0]] * pesos[0]
    ihu_pc_risco_ = df[parametros[1]] * pesos[1]

    bins_pop = [-float('inf'), 0, 2000, 5000, 10000, 50000, float('inf')]
    labels_pop = [0, 0, 1, 2, 3, 4]
    idx_pop = pd.cut(ihu_nu_popriscototal_.fillna(-1), bins=bins_pop, labels=labels_pop,
                     right=False, ordered=False).astype(int)

    bins_risco = [-float('inf'), 0, 0.2, 0.4, 0.6, 0.8, float('inf')]
    labels_risco = [0, 0, 1, 2, 3, 4]
    idx_risco = pd.cut(ihu_pc_risco_.fillna(-1), bins=bins_risco, labels=labels_risco,
                       right=False, ordered=False).astype(int)

    matriz_risco = [
        [5, 5, 4, 4, 3],
        [5, 4, 3, 3, 2],
        [4, 3, 3, 2, 2],
        [4, 3, 2, 2, 1],
        [3, 2, 2, 1, 1],
    ]

    resultado = np.array([matriz_risco[i][j] for i, j in zip(idx_pop, idx_risco)])
    return pd.Series(resultado, index=df.index)


def cs_cobred(df, parametros=['ihu_pc_cobrede'], pesos=[1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ihu_pc_cobrede = (df[parametros[0]]
                      .astype(str)
                      .str.replace(',', '.')
                      .str.replace('#DIV/0!', 'nan')
                      .str.replace('#N/A', 'nan')
                      .str.strip()
                      .pipe(pd.to_numeric, errors='coerce')) * pesos[0]

    bins = [-float('inf'), 0, 0.8, 0.9, 0.95, 0.98, 1, float('inf')]
    labels = [0, 1, 2, 3, 4, 5, 5]
    return pd.cut(ihu_pc_cobrede.fillna(-1), bins=bins, labels=labels,
                  right=False, ordered=False).astype(int)


def area_considerada_scbc(df, parametros=['situacao_setor', 'area_scbc', 'fator_analisavel'], pesos=[1, 3], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    situacao_setor = pd.to_numeric(df[parametros[0]], errors='coerce')
    area_scbc = pd.to_numeric(df[parametros[1]].astype(str).str.replace(',', '.'), errors='coerce') * pesos[0]
    fator_analisavel = pesos[1]

    return np.where(
        situacao_setor <= fator_analisavel,
        area_scbc,
        0,
    )


def area_considerada_bho(df, parametros=['cobacia', 'area_considerada_scbc'], pesos=[1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    cobacia = df[parametros[0]]
    area_considerada_scbc_ = df[parametros[1]] * pesos[0]
    return area_considerada_scbc_.groupby(cobacia).transform('sum')


def pop_urb_scbc(df, parametros=['densidade', 'area_considerada_scbc'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    densidade_ = df[parametros[0]] * pesos[0]
    area_considerada_scbc_ = df[parametros[1]] * pesos[1]
    return densidade_ * area_considerada_scbc_


def pop_urb_bacia(df, parametros=['cobacia', 'pop_urb_scbc'], pesos=[1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    cobacia = df[parametros[0]]
    pop_urb_scbc_ = df[parametros[1]] * pesos[0]
    return pop_urb_scbc_.groupby(cobacia).transform('sum')


def perc_scbc(df, parametros=['pop_urb_scbc', 'pop_urb_bacia'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    pop_urb_scbc_ = df[parametros[0]] * pesos[0]
    pop_urb_bacia_ = df[parametros[1]] * pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [(pop_urb_scbc_ == 0) & (pop_urb_bacia_ == 0)],
            [0],
            default=pop_urb_scbc_ / pop_urb_bacia_,
        )

    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)


def ihu_nu_popriscoinerente_scbc(df, parametros=['ft_imi', 'pop_urb_scbc'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ft_imi_ = pd.to_numeric(df[parametros[0]], errors='coerce') * pesos[0]
    pop_urb_scbc_ = pd.to_numeric(df[parametros[1]], errors='coerce') * pesos[1]
    return ft_imi_ * pop_urb_scbc_


def ihu_nu_popriscoposdeficit_scbc(df, parametros=['ft_pd', 'pop_urb_scbc'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ft_pd_ = pd.to_numeric(df[parametros[0]], errors='coerce') * pesos[0]
    pop_urb_scbc_ = pd.to_numeric(df[parametros[1]], errors='coerce') * pesos[1]
    return ft_pd_ * pop_urb_scbc_


def ihu_nu_popriscototal_scbc(df, parametros=['ft_tot', 'pop_urb_scbc'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ft_tot_ = pd.to_numeric(df[parametros[0]], errors='coerce') * pesos[0]
    pop_urb_scbc_ = pd.to_numeric(df[parametros[1]], errors='coerce') * pesos[1]
    return ft_tot_ * pop_urb_scbc_


def ihu_cs_ish(df, parametros=['cs_cobred', 'cs_risco'], pesos=[0.7, 0.3], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    cs_risco_ = df[parametros[0]]
    cs_cobred_ = df[parametros[1]]

    resultado = np.where(
        cs_cobred_ < cs_risco_,
        pesos[0] * cs_risco_ + pesos[1] * cs_cobred_,
        cs_risco_,
    )
    return pd.Series(resultado, index=df.index)


def ihu_rel_pop(df, parametros=['perc_scbc', 'cs_risco'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    perc_scbc_ = df[parametros[0]] * pesos[0]
    cs_risco_ = df[parametros[1]] * pesos[1]
    return perc_scbc_ * cs_risco_


def ihu_rel_cobred(df, parametros=['perc_scbc', 'cs_cobred'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    perc_scbc_ = df[parametros[0]] * pesos[0]
    cs_cobred_ = df[parametros[1]] * pesos[1]

    resultado = perc_scbc_ * cs_cobred_
    return resultado


def ihu_nu_popriscoinerente_otto(df, parametros=['cobacia', 'ihu_nu_popriscoinerente_scbc'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    cobacia = df['cobacia']
    ihu_nu_popriscoinerente_scbc_ = df[parametros[1]] * pesos[0]
    return ihu_nu_popriscoinerente_scbc_.groupby(cobacia).transform('sum')


def ihu_nu_popriscoposdeficit_otto(df, parametros=['cobacia', 'ihu_nu_popriscoposdeficit_scbc'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    cobacia = df['cobacia']
    ihu_nu_popriscoposdeficit_scbc_ = df[parametros[1]] * pesos[0]
    return ihu_nu_popriscoposdeficit_scbc_.groupby(cobacia).transform('sum')


def ihu_nu_popriscototal_otto(df, parametros=['cobacia', 'ihu_nu_popriscototal_scbc'], pesos=[1, 1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    cobacia = df['cobacia']
    ihu_nu_popriscototal_scbc_ = df[parametros[1]] * pesos[0]
    return ihu_nu_popriscototal_scbc_.groupby(cobacia).transform('sum')


def ire_hu_pop(df, parametros=['cobacia', 'ihu_rel_pop'], pesos=[1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    cobacia = df['cobacia']
    ihu_rel_pop_ = pd.to_numeric(df[parametros[1]], errors='coerce') * pesos[0]
    return ihu_rel_pop_.groupby(cobacia).transform('sum')


def ire_hu_cobred(df, parametros=['cobacia', 'ihu_rel_cobred'], pesos=[1], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    cobacia = df['cobacia']
    ihu_rel_cobred_ = pd.to_numeric(df[parametros[1]], errors='coerce') * pesos[0]
    return ihu_rel_cobred_.groupby(cobacia).transform('sum')


def ire_cs_hum(df, parametros=['ire_hu_cobred', 'ire_hu_pop'], pesos=[0.3, 0.7], value=None):
    v = _aplicar_value(df, value)
    if v is not None:
        return v
    ire_hu_cobred_ = df[parametros[0]]
    ire_hu_pop_ = df[parametros[1]]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [ire_hu_cobred_ > ire_hu_pop_],
            [ire_hu_pop_],
            default=ire_hu_cobred_ * pesos[0] + ire_hu_pop_ * pesos[1],
        )
    return resultado