import pandas as pd
import numpy as np
import re

def converter_numero_br(valor):
    """
    Converte número no formato brasileiro para float
    
    Formatos aceitos:
    - "1.234,56" -> 1234.56
    - "1.234" (ponto de milhar) -> 1234.0
    - "1234,56" -> 1234.56
    - "1234" -> 1234.0
    - "1.234.567,89" -> 1234567.89
    
    Args:
        valor: string, número ou outro tipo
        
    Returns:
        float ou np.nan se não for possível converter
    """
    
    # Validação 1: Verifica se é None ou vazio
    if valor is None:
        return np.nan
    
    # Validação 2: Se for pandas NA/NaN
    if pd.isna(valor):
        return np.nan
    
    # Converte para string, tratando diferentes tipos
    try:
        valor_str = str(valor).strip()
    except:
        return np.nan
    
    # Validação 3: Verifica se é string vazia ou apenas espaços
    if not valor_str or valor_str == '' or valor_str.isspace():
        return np.nan
    
    # Validação 4: Verifica se contém apenas caracteres válidos para número brasileiro
    # Caracteres permitidos: dígitos, vírgula, ponto, sinal negativo
    if not re.match(r'^-?[\d\.,]+$', valor_str):
        return np.nan
    
    # Validação 5: Conta vírgulas - número válido brasileiro tem no máximo 1 vírgula
    if valor_str.count(',') > 1:
        return np.nan
    
    # Validação 6: Trata números negativos
    negativo = False
    if valor_str.startswith('-'):
        negativo = True
        valor_str = valor_str[1:]
    
    try:
        # Padrão brasileiro: tem vírgula (decimal)
        if ',' in valor_str:
            # Separa parte inteira e decimal
            partes = valor_str.split(',')
            inteiro = partes[0]
            decimal = partes[1]
            
            # Validação 7: Parte decimal deve ter apenas dígitos
            if not re.match(r'^\d+$', decimal):
                return np.nan
            
            # Validação 8: Parte inteira pode ter pontos de milhar
            # Remove pontos da parte inteira (pontos de milhar)
            if '.' in inteiro:
                # Verifica padrão de ponto de milhar (pontos a cada 3 dígitos)
                partes_inteiro = inteiro.split('.')
                for parte in partes_inteiro:
                    if not re.match(r'^\d{1,3}$', parte):
                        return np.nan
                inteiro = inteiro.replace('.', '')
            
            # Validação 9: Parte inteira deve ter apenas dígitos
            if not re.match(r'^\d+$', inteiro):
                return np.nan
            
            # Monta o número
            numero_str = f"{inteiro}.{decimal}"
            resultado = float(numero_str)
        
        else:
            # Sem vírgula: pode ter pontos de milhar ou ser inteiro
            if '.' in valor_str:
                # Verifica padrão de ponto de milhar
                partes = valor_str.split('.')
                for parte in partes:
                    if not re.match(r'^\d{1,3}$', parte):
                        # Não é padrão de milhar, pode ser float com ponto
                        resultado = float(valor_str)
                        return -resultado if negativo else resultado
                
                # É ponto de milhar, remove todos
                valor_str = valor_str.replace('.', '')
            
            # Validação 10: Agora deve ter apenas dígitos
            if not re.match(r'^\d+$', valor_str):
                return np.nan
            
            resultado = float(valor_str)
        
        # Aplica sinal negativo se necessário
        resultado = -resultado if negativo else resultado
        
        # Validação 11: Verifica se é um número finito
        if not np.isfinite(resultado):
            return np.nan
        
        return resultado
        
    except (ValueError, TypeError, AttributeError) as e:
        # Qualquer erro na conversão retorna NaN
        return np.nan

arquivo_1 = pd.read_csv('tabela_inicial.csv')
arquivo_2 = pd.read_csv('arquivo_br.csv')


for i in arquivo_1.columns:
    arquivo_1[i] = arquivo_1[i].apply(converter_numero_br)
    arquivo_2[i] = arquivo_2[i].apply(converter_numero_br)


coluna_referencia = 'cod_mun'
posicao = arquivo_2.columns.get_loc(coluna_referencia)
df_comparacoes = arquivo_2.iloc[:, :posicao]

for i in arquivo_2.columns:
    if i in arquivo_1.columns:
        df_comparacoes[i] = np.where(
            abs(100*(arquivo_2[i] - arquivo_1[i])/arquivo_2[i]) > 2,
            100*(arquivo_2[i] - arquivo_1[i])/arquivo_2[i],
            0
        )

df_comparacoes.to_csv('comparacoes.csv')