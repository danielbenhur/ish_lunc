import pandas as pd
import numpy as np

# ==============================================================================
# CONFIGURAÇÃO: Defina aqui a coluna única que identifica a linha em ambos os arquivos
# Exemplo: 'CD_SETOR', 'ID', 'COD_IBGE', etc.
COLUNA_CHAVE = 'CD_SETOR' 
# ==============================================================================

print("Lendo os arquivos CSV...")
# Usando low_memory=False para evitar o DtypeWarning de tipos mistos
arquivo_1 = pd.read_csv('./dim_hum_cnr_fmea.csv', low_memory=False)
arquivo_2 = pd.read_csv('./dados_calculados.csv', low_memory=False)  # Ajuste o nome do arquivo 2 aqui

# Verificar se a coluna chave existe em ambos os arquivos
if COLUNA_CHAVE not in arquivo_1.columns or COLUNA_CHAVE not in arquivo_2.columns:
    raise ValueError(f"A coluna chave '{COLUNA_CHAVE}' precisa existir em ambos os arquivos para alinhar os dados.")

print(f"Arquivo 1: {len(arquivo_1)} linhas")
print(f"Arquivo 2: {len(arquivo_2)} linhas")

# Lista de colunas para comparar (removendo a coluna chave da lista de comparação se ela estiver lá)
colunas_comparar = [
    'FT_TOT', 'AREA_SETOR', 'MUN_NM', 'SITUACAO_SETOR', 'IHU_NU_POPRISCOINERENTE', 
    'POP_URB_BACIA', 'CS_COBRED', 'POP_URB_SCBC', 'CS_RISCO', 'IHU_PC_RISCOPOSDEFICIT', 
    'DMU_NU_POPURBANA', 'IHU_CS_ISH', 'IHU_PC_COBREDE', 'PERC_SCBC', 'TIPO_SETOR', 
    'UF', 'IHU_NU_POPRISCOPOSDEFICIT', 'FT_IMI', 'IHU_PC_RISCO_INERENTE', 'POP', 
    'IHU_PC_RISCO', 'IRE_CS_HUM', 'BAL_PERC', 'IHU_NU_POPRISCOTOTAL', 'DENSIDADE'
]

# Garante que vamos processar apenas colunas que realmente existem em ambos
colunas_validas = [col for col in colunas_comparar if col in arquivo_1.columns and col in arquivo_2.columns]

print(f"\nUnindo os arquivos com base na chave '{COLUNA_CHAVE}'...")
# O merge traz as colunas de ambos os arquivos lado a lado: col_arq1 e col_arq2
df_comparacao = pd.merge(arquivo_1, arquivo_2, on=COLUNA_CHAVE, suffixes=('_arq1', '_arq2'))
print(f"Total de registros correspondentes encontrados: {len(df_comparacao)} linhas.")

# Dicionário para armazenar os relatórios de diferenças
relatorio_diferencas = {}

for col in colunas_validas:
    print(f"Processando coluna: {col}")
    
    col_1 = f"{col}_arq1"
    col_2 = f"{col}_arq2"
    
    # Tenta converter para numérico caso haja tipos mistos (ignora colunas de texto como UF ou MUN_NM)
    try:
        v1 = pd.to_numeric(df_comparacao[col_1])
        v2 = pd.to_numeric(df_comparacao[col_2])
        is_numeric = True
    except ValueError:
        v1 = df_comparacao[col_1].astype(str)
        v2 = df_comparacao[col_2].astype(str)
        is_numeric = False

    if is_numeric:
        # Preenche NaNs com 0 para o cálculo matemático não quebrar
        v1 = v1.fillna(0)
        v2 = v2.fillna(0)
        
        # Evita divisão por zero substituindo 0 por NaN temporariamente no denominador
        diferenca_percentual = 100 * (v2 - v1) / v2.replace(0, np.nan)
        diferenca_percentual = diferenca_percentual.fillna(0) # Se era 0/0, vira 0
        
        # Consideramos diferença se o percentual for maior que um pequeno limite (ex: 0.01%)
        mask_diferente = np.abs(diferenca_percentual) > 0.01
        
        if mask_diferente.any():
            print(f" -> Encontradas {mask_diferente.sum()} linhas com divergência numérica.")
            # Salva no relatório as linhas divergentes
            df_erros = df_comparacao.loc[mask_diferente, [COLUNA_CHAVE, col_1, col_2]].copy()
            df_erros['DIF_PERCENTUAL'] = diferenca_percentual[mask_diferente]
            relatorio_diferencas[col] = df_erros
    else:
        # Comparação para colunas de texto
        mask_diferente = v1 != v2
        if mask_diferente.any():
            print(f" -> Encontradas {mask_diferente.sum()} linhas com divergência de texto.")
            df_erros = df_comparacao.loc[mask_diferente, [COLUNA_CHAVE, col_1, col_2]].copy()
            relatorio_diferencas[col] = df_erros

print("\n=== COMPARAÇÃO CONCLUÍDA ===")
if not relatorio_diferencas:
    print("Sucesso! Nenhuma diferença encontrada entre as colunas comparadas.")
else:
    print(f"Diferenças encontradas em {len(relatorio_diferencas)} colunas.")
    # Exemplo: Mostra as primeiras 5 linhas com erro da primeira coluna divergente
    primeira_col_erro = list(relatorio_diferencas.keys())[0]
    print(f"\nAmostra de divergências na coluna '{primeira_col_erro}':")
    print(relatorio_diferencas[primeira_col_erro].head())