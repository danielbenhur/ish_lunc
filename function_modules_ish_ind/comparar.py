import pandas as pd
import numpy as np
import re


diferenca_percentual_geral = 5

def converter_numero_br(valor):
    """Converte número no formato brasileiro para float"""
    if pd.isna(valor):
        return np.nan
    
    valor_str = str(valor).strip()
    
    # Verifica se o valor é um número (inclui dígitos, pontos, vírgulas, sinal negativo)
    # Se tiver letras ou outros caracteres que não são de número, retorna NaN
    if not re.match(r'^-?[\d\.,]+$', valor_str):
        return np.nan
    
    try:
        # Padrão brasileiro: 1.234.567,89
        # Se tem vírgula, é decimal
        if ',' in valor_str:
            # Remove pontos que estão antes da vírgula (milhar)
            partes = valor_str.split(',')
            inteiro = partes[0].replace('.', '')  # Remove todos os pontos da parte inteira
            decimal = partes[1]
            return float(f"{inteiro}.{decimal}")
        else:
            # Sem vírgula, pode ter ponto de milhar ou ser inteiro
            # Se o padrão for algo como "1.234" (ponto de milhar)
            if '.' in valor_str and len(valor_str.split('.')[-1]) == 3:
                return float(valor_str.replace('.', ''))
            else:
                return float(valor_str)
    except (ValueError, TypeError):
        return np.nan

# Ler os arquivos
arquivo_1 = pd.read_csv('tabela_inicial.csv')
arquivo_2 = pd.read_csv('arquivo_br.csv')

# Colunas que devem ser mantidas como estão (identificadores)
colunas_identificadores = ['fid', 'COBACIA', 'cod_setor', 'cod_mun']

# Colunas que serão comparadas (exclui identificadores)
colunas_comuns = list(set(arquivo_1.columns) & set(arquivo_2.columns))
colunas_comparar = [col for col in colunas_comuns if col not in colunas_identificadores]

# Criar DataFrame de comparações com as colunas identificadoras do arquivo_2
df_comparacoes = arquivo_2[colunas_identificadores].copy()

# Comparar apenas colunas numéricas
for col in colunas_comparar:
    # Converter apenas se a coluna for do tipo object (string)
    if arquivo_1[col].dtype == 'object':
        arquivo_1[col] = arquivo_1[col].apply(converter_numero_br)
    else:
        arquivo_1[col] = pd.to_numeric(arquivo_1[col], errors='coerce')
    
    if arquivo_2[col].dtype == 'object':
        arquivo_2[col] = arquivo_2[col].apply(converter_numero_br)
    else:
        arquivo_2[col] = pd.to_numeric(arquivo_2[col], errors='coerce')
    
    # Calcular diferença percentual (evitando divisão por zero)
    with np.errstate(divide='ignore', invalid='ignore'):
        # Verificar onde ambos os valores são válidos
        mask_valida = (~np.isnan(arquivo_1[col])) & (~np.isnan(arquivo_2[col])) & (arquivo_2[col] != 0)
        
        diferenca_percentual = np.zeros(len(arquivo_2))
        diferenca_percentual[mask_valida] = 100 * (arquivo_2[col][mask_valida] - arquivo_1[col][mask_valida]) / arquivo_2[col][mask_valida]
    
    # Marcar apenas diferenças > diferenca_percentual_geral %
    df_comparacoes[col] = np.where(
        np.abs(diferenca_percentual) > diferenca_percentual_geral,
        diferenca_percentual,
        0
    )

# Salvar resultado
df_comparacoes.to_csv('comparacoes.csv', index=False)

# Mostrar estatísticas básicas
print("\nResumo das diferenças encontradas:")
for col in colunas_comparar:
    n_diferencas = (df_comparacoes[col] != 0).sum()
    if n_diferencas > 0:
        max_diff = df_comparacoes[col].abs().max()
        print(f"  {col}: {n_diferencas} registros com diferença > {diferenca_percentual_geral}% (máx: {max_diff:.2f}%)")