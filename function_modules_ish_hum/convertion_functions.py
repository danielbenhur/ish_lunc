import pandas as pd
import numpy as np
import yaml
import sys

def disp_por_dem(parametros):
    # bal_perc_series = parametros[0]
    # return np.where((pd.isna(bal_perc_series)) | (bal_perc_series == 0), 0, 100/bal_perc_series)
    bal_perc_series = pd.to_numeric(parametros[0], errors='coerce')
    
    # Substitui 0 por NaN para a divisão não quebrar, faz a conta e limpa os NaNs restando 0
    resultado = 100 / bal_perc_series.replace(0, np.nan)
    return resultado.fillna(0)

def ft_imi(parametros):
    disp_dem = pd.to_numeric(parametros[0], errors='coerce')
    return np.where(
        disp_dem >=1,
        (1/3)*(disp_dem**(-2)),
        (1/3)*(disp_dem)
    )

def ft_pd(parametros):
    disp_dem = pd.to_numeric(parametros[0], errors='coerce')
    
    return disp_dem.apply(lambda x: 0 if x >= 1 else 1 - x)

def ft_tot(parametros):
    fator_iminente = parametros[0]
    fator_pos_deficit = parametros[1]
    return fator_iminente + fator_pos_deficit

def ihu_nu_popriscoinerente(parametros):
    fator_iminente = parametros[0] 
    dmu_nu_popurbana = parametros[1]

    fator_iminente = fator_iminente.fillna(0)
    dmu_nu_popurbana = dmu_nu_popurbana.fillna(0)
    
    resultado = fator_iminente*dmu_nu_popurbana

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
    ft_tot = parametros[0]
    dmu_nu_popurbana = parametros[1]
    
    ft_tot = ft_tot.fillna(0)
    dmu_nu_popurbana = dmu_nu_popurbana.fillna(0)

    resultado = ft_tot*dmu_nu_popurbana
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
    ihu_pc_cobrede = parametros[0]
    bins = [-float('inf'), 0, 0.8, 0.9, 0.95, 0.98, 1, float('inf')]
    labels = [0, 1, 2, 3, 4, 5, 5]  
    return pd.cut(ihu_pc_cobrede.fillna(-1), bins=bins, labels=labels, right=False, ordered=False).astype(int)

# não gosto dessa solução
def converter_br_para_float(serie):
    """Converte uma série de números no formato brasileiro para float"""
    if serie.dtype == 'object':
        # Remove espaços
        serie = serie.str.strip()
        # Substitui ponto de milhar (remove todos os pontos)
        serie = serie.str.replace('.', '', regex=False)
        # Substitui vírgula decimal por ponto
        serie = serie.str.replace(',', '.', regex=False)
        # Converte para numérico
        return pd.to_numeric(serie, errors='coerce').fillna(0)
    else:
        return pd.to_numeric(serie, errors='coerce').fillna(0)

def pop_urb_scbc(parametros):
    situacao_setor = parametros[0]
    densidade = parametros[1]
    area_scbc = parametros[2]
    fator_analisavel = parametros[3]
    return np.where(
        situacao_setor < fator_analisavel,
        densidade*area_scbc,
        0
    )

def pop_urb_bacia(parametros):
    cobacia = parametros[0]
    pop_urb_scbc = parametros[1]
    resultado = pop_urb_scbc.groupby(cobacia).transform('sum')

    return resultado

def perc_scbc(parametros):
    pop_urb_scbc = parametros[0]
    pop_urb_bacia = parametros[1]

    pop_urb_scbc = converter_br_para_float(pop_urb_scbc)
    pop_urb_bacia = converter_br_para_float(pop_urb_bacia)
    
    # Evitar divisão por zero
    resultado = np.where(
        pop_urb_bacia != 0,
        pop_urb_scbc / pop_urb_bacia,
        0
    )
  
    return pd.Series(resultado, index=pop_urb_scbc.index)

def ihu_cs_ish(parametros):
    cs_risco = parametros[0]
    peso_cs_risco = parametros[1]
    cs_cobred = parametros[2]
    peso_cs_cobred = parametros[3]
    
    resultado = np.where(
        cs_cobred < cs_risco,
        peso_cs_risco * cs_risco + peso_cs_cobred * cs_cobred,
        cs_risco
    )

    return pd.Series(resultado)
    
def ihu_rel_pop(parametros):
    perc_scbc = parametros[0]
    cs_risco = parametros[1]
    return perc_scbc*cs_risco

def ihu_rel_cobred(parametros):
    perc_scbc = parametros[0]
    cs_cobred = parametros[1]
    return perc_scbc*cs_cobred

def ire_hu_pop(parametros):
    cobacia = parametros[0]
    ihu_rel_pop = pd.to_numeric(parametros[1], errors='coerce').fillna(0)
    
    resultado = ihu_rel_pop.groupby(cobacia).transform('sum')
    return resultado.round(2)

def ire_hu_cobred(parametros):
    cobacia = parametros[0]
    ihu_rel_cobred = pd.to_numeric(parametros[1], errors='coerce').fillna(0)
    
    resultado = ihu_rel_cobred.groupby(cobacia).transform('sum')
    return resultado.round(2)

def ire_cs_hum(parametros):
    ire_hu_pop = parametros[0]
    peso_ire_hu_pop = parametros[1]
    ire_hu_cobred = parametros[2]
    peso_ire_hu_cobred = parametros[3]

    return np.where(
        ire_hu_cobred < ire_hu_pop,
        peso_ire_hu_pop*ire_hu_pop + peso_ire_hu_cobred*ire_hu_cobred,
        ire_hu_pop
    )
    
def perc_scbc_ind(parametros):
    pop_urb_scbc = pd.to_numeric(parametros[0], errors='coerce').fillna(0)
    deman_indus = pd.to_numeric(parametros[1], errors='coerce').fillna(0)
    
    # Usa operações vetorizadas do pandas
    resultado = pop_urb_scbc / deman_indus.replace(0, np.nan)
    resultado = resultado.fillna(0).round(2)
    
    return resultado

def igh_ind(parametros):
    disp_q95 = parametros[0]
    deman_indus = parametros[1]

    disp_q95 = disp_q95.fillna(0)
    deman_indus = deman_indus.fillna(0)

    resultado = np.where(
        deman_indus != 0,
        disp_q95 / deman_indus,
        0
    )
    
    return resultado.round(2)

def ihu_rel(parametros):
    perc_scbc = pd.to_numeric(parametros[0], errors='coerce').fillna(0)
    ihu_cs_ish = pd.to_numeric(parametros[1], errors='coerce').fillna(0)

    resultado = perc_scbc * ihu_cs_ish
    
    # Convert to numeric, coercing errors to NaN
    resultado = pd.to_numeric(resultado, errors='coerce')
    
    # Round only if not all values are NaN
    if resultado.notna().any():
        return resultado.round(2)
    else:
        return resultado

# def ire_cs_ind(parametros):
    # ihu_rel = parametros[0]
    # peso_ihu_rel = parametros[1]
    # igh_ind = parametros[2]
    # peso_igh_ind = parametros[3]
    # 
    # resultado = np.where(
        # ihu_rel < igh_ind,
        # peso_igh_ind * igh_ind + peso_ihu_rel * ihu_rel,
        # igh_ind
    # )
# 
    # return pd.Series(resultado)


def list_functions(dimensao):
    return_list = []
    
    for item in dimensao['indicadores']:
        if item == None:
            continue

        nome_funcao = item['indicador']

        # Verifica se a função existe no módulo importado
        if nome_funcao in globals() and callable(globals()[nome_funcao]):
            return_list.append(item)

    return return_list

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