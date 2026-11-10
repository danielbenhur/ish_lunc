import pandas as pd
import numpy as np


# ======================================================================
# Helpers de override
# ======================================================================
def _normalizar_value(value, parametros):
    """
    Converte o `value` do YAML em dict {nome_param: valor}.
      - None            -> None
      - dict            -> {param: valor}
      - list/tuple      -> casa posicionalmente com `parametros` (None pula)
      - escalar/Series  -> aplica a todos os parâmetros
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, (list, tuple)):
        if len(value) != len(parametros):
            raise ValueError(
                f"value tem {len(value)} itens, mas há {len(parametros)} parâmetros: {parametros}"
            )
        return {p: v for p, v in zip(parametros, value) if v is not None}
    return {p: value for p in parametros}


def _param(df, nome, ov, cast="raw"):
    """
    Devolve o valor do parâmetro `nome` respeitando o override `ov`.
    cast: "raw"  -> como está (pode ser Series ou escalar)
          "num"  -> string->float (vírgula, #DIV/0!, #N/A)
          "pop"  -> remove '.' (população com separador de milhar)
    """
    if ov is not None and nome in ov:
        raw = ov[nome]
        base = raw.reindex(df.index) if isinstance(raw, pd.Series) else pd.Series(raw, index=df.index)
    else:
        base = df[nome]

    if cast == "raw":
        return base
    if cast == "pop":
        return pd.to_numeric(base.astype(str).str.replace('.', '', regex=False), errors='coerce')
    # cast == "num"
    return (base.astype(str)
                .str.replace(',', '.', regex=False)
                .str.replace('#DIV/0!', 'nan', regex=False)
                .str.replace('#N/A', 'nan', regex=False)
                .str.strip()
                .pipe(pd.to_numeric, errors='coerce'))


# ======================================================================
# Funções
# ======================================================================
def disp_q95_cap_2(df, parametros=['disp_q95_cap'], pesos=[1], value=None):
    ov = _normalizar_value(value, parametros)
    disp_q95_cap = _param(df, parametros[0], ov, cast="num") * pesos[0]

    if 'mun_nm' in df.columns:
        mascara_vila_velha = df['mun_nm'].astype(str).str.strip() == 'Vila Velha'
    else:
        mascara_vila_velha = pd.Series(False, index=df.index)

    return disp_q95_cap + mascara_vila_velha.astype(float)


def bal_perc_cap(df, parametros=['dem_acm_cap', 'disp_q95_cap_2'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    dem_acm = _param(df, parametros[0], ov, cast="num") * pesos[0]
    disp_q95 = _param(df, parametros[1], ov, cast="raw") * pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [(disp_q95 == 0) & (dem_acm == 0), (disp_q95 == 0)],
            [0, 999999],
            default=100 * dem_acm / disp_q95,
        )
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)


def bal_perc_bho(df, parametros=['dem_acm_bho', 'disp_q95_bho'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    dem_acm = _param(df, parametros[0], ov, cast="num") * pesos[0]
    disp_q95 = _param(df, parametros[1], ov, cast="num") * pesos[1]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [(disp_q95 == 0) & (dem_acm == 0), (disp_q95 == 0)],
            [999999, 0],
            default=100 * dem_acm / disp_q95,
        )
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)


def disp_dem_cap(df, parametros=['bal_perc_cap'], pesos=[1], value=None):
    ov = _normalizar_value(value, parametros)
    bal_perc_cap_ = pd.to_numeric(_param(df, parametros[0], ov, cast="raw"), errors='coerce') * pesos[0]

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select([(bal_perc_cap_ == 0)], [999999], default=100 / bal_perc_cap_)
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)


def ft_imi(df, parametros=['disp_dem_cap'], pesos=[0.333333], value=None):
    ov = _normalizar_value(value, parametros)
    disp_dem_cap_ = _param(df, parametros[0], ov, cast="raw")
    peso = pesos[0]
    return np.where(disp_dem_cap_ >= 1, peso * (disp_dem_cap_ ** (-2)), peso * disp_dem_cap_)


def ft_pd(df, parametros=['disp_dem_cap'], pesos=[1], value=None):
    ov = _normalizar_value(value, parametros)
    disp_dem_cap_ = _param(df, parametros[0], ov, cast="raw") * pesos[0]
    return disp_dem_cap_.apply(lambda x: 0 if x >= 1 else 1 - x)


def ft_tot(df, parametros=['ft_imi', 'ft_pd'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    ft_imi_ = _param(df, parametros[0], ov) * pesos[0]
    ft_pd_ = _param(df, parametros[1], ov) * pesos[1]
    return ft_imi_ + ft_pd_


def ihu_nu_popriscoinerente(df, parametros=['ft_imi', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    ft_imi_ = _param(df, parametros[0], ov) * pesos[0]
    pop = _param(df, parametros[1], ov, cast="pop") * pesos[1]
    return (ft_imi_ * pop).round(2)


def ihu_pc_risco_inerente(df, parametros=['ihu_nu_popriscoinerente', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    num = _param(df, parametros[0], ov).fillna(0) * pesos[0]
    den = _param(df, parametros[1], ov, cast="pop") * pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(den == 0, 0, num / den)


def ihu_nu_popriscoposdeficit(df, parametros=['ft_pd', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    ft_pd_ = _param(df, parametros[0], ov) * pesos[0]
    pop = _param(df, parametros[1], ov, cast="pop") * pesos[1]
    return ft_pd_ * pop


def ihu_pc_riscoposdeficit(df, parametros=['ihu_nu_popriscoposdeficit', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    num = _param(df, parametros[0], ov) * pesos[0]
    den = _param(df, parametros[1], ov, cast="pop") * pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(den == 0, 0, num / den)


def ihu_nu_popriscototal(df, parametros=['ft_tot', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    ft_tot_ = _param(df, parametros[0], ov) * pesos[0]
    pop = _param(df, parametros[1], ov, cast="pop") * pesos[1]
    return ft_tot_ * pop


def ihu_pc_risco(df, parametros=['ihu_nu_popriscototal', 'dmu_nu_popurbana'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    num = _param(df, parametros[0], ov) * pesos[0]
    den = _param(df, parametros[1], ov, cast="pop") * pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(den == 0, 0, num / den)


def densidade(df, parametros=['pop', 'area_setor'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    pop = _param(df, parametros[0], ov, cast="num") * pesos[0]
    area_setor = _param(df, parametros[1], ov, cast="num") * pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [(area_setor == 0) & (pop == 0), (area_setor == 0)],
            [0, 10000000],
            default=round(pop / area_setor, 3),
        )
    return resultado


def cs_risco(df, parametros=['ihu_nu_popriscototal', 'ihu_pc_risco'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    pop = _param(df, parametros[0], ov) * pesos[0]
    risco = _param(df, parametros[1], ov) * pesos[1]

    bins_pop = [-float('inf'), 0, 2000, 5000, 10000, 50000, float('inf')]
    labels_pop = [0, 0, 1, 2, 3, 4]
    idx_pop = pd.cut(pop.fillna(-1), bins=bins_pop, labels=labels_pop,
                     right=False, ordered=False).astype(int)

    bins_risco = [-float('inf'), 0, 0.2, 0.4, 0.6, 0.8, float('inf')]
    labels_risco = [0, 0, 1, 2, 3, 4]
    idx_risco = pd.cut(risco.fillna(-1), bins=bins_risco, labels=labels_risco,
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
    ov = _normalizar_value(value, parametros)
    ihu_pc_cobrede = _param(df, parametros[0], ov, cast="num") * pesos[0]
    bins = [-float('inf'), 0, 0.8, 0.9, 0.95, 0.98, 1, float('inf')]
    labels = [0, 1, 2, 3, 4, 5, 5]
    return pd.cut(ihu_pc_cobrede.fillna(-1), bins=bins, labels=labels,
                  right=False, ordered=False).astype(int)


def area_considerada_scbc(df, parametros=['situacao_setor', 'area_scbc', 'fator_analisavel'], pesos=[1, 3], value=None):
    ov = _normalizar_value(value, parametros)
    situacao_setor = pd.to_numeric(_param(df, parametros[0], ov, cast="raw"), errors='coerce')
    area_scbc = _param(df, parametros[1], ov, cast="num") * pesos[0]
    fator_analisavel = pesos[1]
    return np.where(situacao_setor <= fator_analisavel, area_scbc, 0)


def area_considerada_bho(df, parametros=['cobacia', 'area_considerada_scbc'], pesos=[1], value=None):
    ov = _normalizar_value(value, parametros)
    cobacia = _param(df, parametros[0], ov, cast="raw")
    area = _param(df, parametros[1], ov) * pesos[0]
    return area.groupby(cobacia).transform('sum')


def pop_urb_scbc(df, parametros=['densidade', 'area_considerada_scbc'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    densidade_ = _param(df, parametros[0], ov) * pesos[0]
    area_ = _param(df, parametros[1], ov) * pesos[1]
    return densidade_ * area_


def pop_urb_bacia(df, parametros=['cobacia', 'pop_urb_scbc'], pesos=[1], value=None):
    ov = _normalizar_value(value, parametros)
    cobacia = _param(df, parametros[0], ov, cast="raw")
    pop = _param(df, parametros[1], ov) * pesos[0]
    return pop.groupby(cobacia).transform('sum')


def perc_scbc(df, parametros=['pop_urb_scbc', 'pop_urb_bacia'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    num = _param(df, parametros[0], ov) * pesos[0]
    den = _param(df, parametros[1], ov) * pesos[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select([(num == 0) & (den == 0)], [0], default=num / den)
    resultado = np.where(np.isinf(resultado), 0, resultado)
    return pd.Series(resultado, index=df.index)


def ihu_nu_popriscoinerente_scbc(df, parametros=['ft_imi', 'pop_urb_scbc'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    ft_imi_ = pd.to_numeric(_param(df, parametros[0], ov, cast="raw"), errors='coerce') * pesos[0]
    pop = pd.to_numeric(_param(df, parametros[1], ov, cast="raw"), errors='coerce') * pesos[1]
    return ft_imi_ * pop


def ihu_nu_popriscoposdeficit_scbc(df, parametros=['ft_pd', 'pop_urb_scbc'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    ft_pd_ = pd.to_numeric(_param(df, parametros[0], ov, cast="raw"), errors='coerce') * pesos[0]
    pop = pd.to_numeric(_param(df, parametros[1], ov, cast="raw"), errors='coerce') * pesos[1]
    return ft_pd_ * pop


def ihu_nu_popriscototal_scbc(df, parametros=['ft_tot', 'pop_urb_scbc'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    ft_tot_ = pd.to_numeric(_param(df, parametros[0], ov, cast="raw"), errors='coerce') * pesos[0]
    pop = pd.to_numeric(_param(df, parametros[1], ov, cast="raw"), errors='coerce') * pesos[1]
    return ft_tot_ * pop


def ihu_cs_ish(df, parametros=['cs_risco', 'cs_cobred'], pesos=[0.7, 0.3], value=None):
    ov = _normalizar_value(value, parametros)
    cs_risco_ = _param(df, parametros[0], ov)
    cs_cobred_ = _param(df, parametros[1], ov)
    resultado = np.where(
        cs_cobred_ < cs_risco_,
        pesos[0] * cs_risco_ + pesos[1] * cs_cobred_,
        cs_risco_,
    )
    return pd.Series(resultado, index=df.index)


def ihu_rel_pop(df, parametros=['perc_scbc', 'cs_risco'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    return _param(df, parametros[0], ov) * pesos[0] * _param(df, parametros[1], ov) * pesos[1]


def ihu_rel_cobred(df, parametros=['perc_scbc', 'cs_cobred'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    return _param(df, parametros[0], ov) * pesos[0] * _param(df, parametros[1], ov) * pesos[1]


def ihu_nu_popriscoinerente_otto(df, parametros=['cobacia', 'ihu_nu_popriscoinerente_scbc'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    cobacia = _param(df, parametros[0], ov, cast="raw")
    val = _param(df, parametros[1], ov) * pesos[0]
    return val.groupby(cobacia).transform('sum')


def ihu_nu_popriscoposdeficit_otto(df, parametros=['cobacia', 'ihu_nu_popriscoposdeficit_scbc'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    cobacia = _param(df, parametros[0], ov, cast="raw")
    val = _param(df, parametros[1], ov) * pesos[0]
    return val.groupby(cobacia).transform('sum')


def ihu_nu_popriscototal_otto(df, parametros=['cobacia', 'ihu_nu_popriscototal_scbc'], pesos=[1, 1], value=None):
    ov = _normalizar_value(value, parametros)
    cobacia = _param(df, parametros[0], ov, cast="raw")
    val = _param(df, parametros[1], ov) * pesos[0]
    return val.groupby(cobacia).transform('sum')


def ire_hu_pop(df, parametros=['cobacia', 'ihu_rel_pop'], pesos=[1], value=None):
    ov = _normalizar_value(value, parametros)
    cobacia = _param(df, parametros[0], ov, cast="raw")
    val = pd.to_numeric(_param(df, parametros[1], ov, cast="raw"), errors='coerce') * pesos[0]
    return val.groupby(cobacia).transform('sum')


def ire_hu_cobred(df, parametros=['cobacia', 'ihu_rel_cobred'], pesos=[1], value=None):
    ov = _normalizar_value(value, parametros)
    cobacia = _param(df, parametros[0], ov, cast="raw")
    val = pd.to_numeric(_param(df, parametros[1], ov, cast="raw"), errors='coerce') * pesos[0]
    return val.groupby(cobacia).transform('sum')


def ire_cs_hum(df, parametros=['ire_hu_cobred', 'ire_hu_pop'], pesos=[0.3, 0.7], value=None):
    ov = _normalizar_value(value, parametros)
    cob = _param(df, parametros[0], ov)
    pop = _param(df, parametros[1], ov)
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.select(
            [cob > pop],
            [pop],
            default=cob * pesos[0] + pop * pesos[1],
        )
    return resultado