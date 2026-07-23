import pandas as pd
import numpy as np
import yaml
import sys

def disp_por_dem(df):
    if df['bal_perc'].dtype == 'object':  # object geralmente indica strings
        bal_perc = pd.to_numeric(df['bal_perc'].str.replace(',', '.'), errors='coerce')
    else:
        # Se já for numérica, usa diretamente
        bal_perc = pd.to_numeric(df['bal_perc'], errors='coerce')
    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            (bal_perc == 0) | pd.isna(bal_perc),  # condição
            0,                                     # valor se for zero ou NaN
            100 / bal_perc                         # valor caso contrário
        )
    
    # Converte para Series para manter compatibilidade
    resultado = np.where(np.isinf(resultado), 0, resultado)

    return pd.Series(resultado, index=df.index)

def fator_iminente(df):
    disp_por_dem = df['disp_por_dem']
    
    return np.where(
        disp_por_dem >=1,
        (1/3)*(disp_por_dem**(-2)),
        (1/3)*(disp_por_dem)
    )


def fator_pos_deficit(df):
    disp_por_dem = df['disp_por_dem']
    
    return disp_por_dem.apply(lambda x: 0 if x >= 1 else 1 - x)

def fator_de_risco_total(df):
    fator_iminente = df['fator_iminente']
    fator_pos_deficit = df['fator_pos_deficit']
    
    return fator_iminente + fator_pos_deficit

def ihu_nu_popriscoinerente(df):
    fator_iminente = df['fator_iminente'] 
    dmu_nu_popurbana = df['dmu_nu_popurbana']
    
    resultado = fator_iminente*dmu_nu_popurbana

    return resultado.round(2)

def ihu_pc_risco_inerente(df):
    ihu_nu_popriscoinerente = df['ihu_nu_popriscoinerente']
    dmu_nu_popurbana = df['dmu_nu_popurbana']

    ihu_nu_popriscoinerente = ihu_nu_popriscoinerente.fillna(0)
    dmu_nu_popurbana = dmu_nu_popurbana.fillna(0)

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            dmu_nu_popurbana == 0,  # condição
            0,                                       # valor se for zero ou NaN
            ihu_nu_popriscoinerente/dmu_nu_popurbana # valor caso contrário
        )
    
    return resultado

def ihu_nu_popriscoposdeficit(df):
    fator_pos_deficit = df['fator_pos_deficit']
    dmu_nu_popurbana = df['dmu_nu_popurbana']

    resultado = fator_pos_deficit*dmu_nu_popurbana
    
    return resultado

def ihu_pc_riscoposdeficit(df):
    ihu_nu_popriscoposdeficit = df['ihu_nu_popriscoposdeficit']
    dmu_nu_popurbana = df['dmu_nu_popurbana']

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            dmu_nu_popurbana == 0,  # condição
            0,                                       # valor se for zero ou NaN
            ihu_nu_popriscoposdeficit/dmu_nu_popurbana # valor caso contrário
        )

    return resultado

def ihu_nu_popriscototal(df):
    fator_de_risco_total = df['fator_de_risco_total']
    dmu_nu_popurbana = df['dmu_nu_popurbana']

    resultado = fator_de_risco_total*dmu_nu_popurbana
    
    return resultado

def ihu_pc_risco(df):
    ihu_nu_popriscototal = df['ihu_nu_popriscototal']
    dmu_nu_popurbana = df['dmu_nu_popurbana']

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            dmu_nu_popurbana == 0,  # condição
            0,                                       # valor se for zero ou NaN
            ihu_nu_popriscototal/dmu_nu_popurbana # valor caso contrário
        )
    
    return resultado

def densidade(df):
    pop = (df['pop']
                    .astype(str)
                    .str.replace(',', '.')
                    .str.replace('#DIV/0!', 'nan')
                    .str.replace('#N/A', 'nan')
                    .str.strip()
                    .pipe(pd.to_numeric, errors='coerce'))
    area_setor = (df['area_setor']
                    .astype(str)
                    .str.replace(',', '.')
                    .str.replace('#DIV/0!', 'nan')
                    .str.replace('#N/A', 'nan')
                    .str.strip()
                    .pipe(pd.to_numeric, errors='coerce'))

    with np.errstate(divide='ignore', invalid='ignore'):
        resultado = np.where(
            area_setor == 0,  # condição
            0,                                       # valor se for zero ou NaN
            pop/area_setor # valor caso contrário
        )

    return resultado

# cs_risco: busca de dados em matriz
def cs_risco(df):
    ihu_nu_popriscototal = df['ihu_nu_popriscototal']
    ihu_pc_risco = df['ihu_pc_risco']
    
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

def cs_cobred(df):
    ihu_pc_cobrede = pd.to_numeric(df['ihu_pc_cobrede'], errors='coerce')
    bins = [-float('inf'), 0, 0.8, 0.9, 0.95, 0.98, 1, float('inf')]
    labels = [0, 1, 2, 3, 4, 5, 5]  
    return pd.cut(ihu_pc_cobrede.fillna(-1), bins=bins, labels=labels, right=False, ordered=False).astype(int)

def pop_urb_scbc(df):
    situacao_setor = df['situacao_setor']
    densidade = df['densidade']
    area_scbc = df['area_scbc']
    fator_analisavel = df['fator_analisavel']
    return np.where(
        situacao_setor < fator_analisavel,
        densidade*area_scbc,
        0
    )

def pop_urb_bacia(df):
    cobacia = df['COBACIA']
    pop_urb_scbc = df['pop_urb_scbc']
    resultado = pop_urb_scbc.groupby(cobacia).transform('sum')

    return resultado

def perc_scbc(df):
    # Limpeza da primeira coluna
    pop_urb_scbc = (df['pop_urb_scbc']
                    .astype(str)
                    .str.replace(',', '.')
                    .str.replace('#DIV/0!', 'nan')
                    .str.replace('#N/A', 'nan')
                    .str.strip()
                    .pipe(pd.to_numeric, errors='coerce'))
    
    # Limpeza da segunda coluna
    pop_urb_bacia = (df['pop_urb_bacia']
                     .astype(str)
                     .str.replace(',', '.')
                     .str.replace('#DIV/0!', 'nan')
                     .str.replace('#N/A', 'nan')
                     .str.strip()
                     .pipe(pd.to_numeric, errors='coerce'))
    
    # Cálculo seguro
    resultado = pop_urb_scbc / pop_urb_bacia
    resultado = resultado.fillna(0).replace([np.inf, -np.inf], 0)
    
    return resultado

def ihu_cs_ish(df, peso_cs_cobred=0.7, peso_cs_risco=0.3):
    cs_risco = df['cs_risco']
    cs_cobred = df['cs_cobred']
    
    resultado = np.where(
        cs_cobred < cs_risco,
        peso_cs_risco * cs_risco + peso_cs_cobred * cs_cobred,
        cs_risco
    )

    return pd.Series(resultado)
    
def ihu_rel_pop(df):
    perc_scbc = df['perc_scbc']
    cs_risco = df['cs_risco']
    return perc_scbc*cs_risco

def ihu_rel_cobred(df):
    perc_scbc = df['perc_scbc']
    cs_cobred = df['cs_cobred']
    return perc_scbc*cs_cobred

def ire_hu_pop(df):
    cobacia = df['COBACIA']
    ihu_rel_pop = pd.to_numeric(df['ihu_rel_pop'], errors='coerce')
    
    return ihu_rel_pop.groupby(cobacia).transform('sum')
    
def ire_hu_cobred(df):
    cobacia = df['COBACIA']
    ihu_rel_cobred = pd.to_numeric(df['ihu_rel_cobred'], errors='coerce')
    
    return ihu_rel_cobred.groupby(cobacia).transform('sum')

def ire_cs_hum(ire_hu_pop, peso_ire_hu_pop, ire_hu_cobred, peso_ire_hu_cobred):
    impacto_hu_cobred = ire_hu_cobred*peso_ire_hu_cobred
    impacto_hu_pop    = ire_hu_pop*peso_ire_hu_pop
    
    if ire_hu_cobred < ire_hu_pop:
        return impacto_hu_cobred + impacto_hu_pop
    else:
        return ire_hu_pop

def list_functions(dimensao):
    return_list = []
    
    for item in dimensao['indicadores']:
        if item == None:
            continue

        nome_funcao = item['name']

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
                     if item['name'] == indicador), None)

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