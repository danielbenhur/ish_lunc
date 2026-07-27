import pandas as pd
import os
import glob

def compute_cs_ish(df, dim_cols):
    """
    Recebe um GeoDataFrame e uma lista de colunas de dimensão (por exemplo,
    ['ire_cs_hum', 'ire_cs_eco', ...]). Retorna uma Series contendo a média
    das colunas, considerando apenas valores maiores que 0.0 (ignorando zeros e NaN).
    Quando não tiver valores na linha, o cs_ish será 0
    """
    df_numeric = df[dim_cols].apply(pd.to_numeric, errors='coerce')
    # Para cada linha, filtra apenas valores > 0 e calcula a média
    return df_numeric.apply(lambda row: row[row > 0.0].mean() if (row[row > 0.0].count() > 0) else 0.0, axis=1)

# Definir o caminho da pasta principal onde estão as pastas functions_module_ish_
caminho_base = "."  # Altere para o caminho correto, ex: "./dados"

# Encontrar todas as pastas que começam com "functions_module_ish_"
padrao_pasta = os.path.join(caminho_base, "functions_module_ish_*")
pastas_encontradas = glob.glob(padrao_pasta)

# Filtrar apenas pastas (não arquivos)
pastas_encontradas = [p for p in pastas_encontradas if os.path.isdir(p)]

print(f"📁 Pastas functions_module_ish_ encontradas: {len(pastas_encontradas)}")

#  Dicionário para armazenar os dataframes de cada arquivo
dataframes_dict = {}

# Para cada pasta encontrada
for pasta in pastas_encontradas:
    print(f"\n📂 Processando: {os.path.basename(pasta)}")
    
    # 4.1. Construir o caminho para a subpasta output
    pasta_output = os.path.join(pasta, "output")
    
    # 4.2. Verificar se a pasta output existe
    if not os.path.exists(pasta_output):
        print(f"  ⚠️ Pasta 'output' não encontrada")
        continue
    
    # 4.3. Determinar qual arquivo procurar baseado no nome da pasta
    nome_pasta = os.path.basename(pasta)
    
    # Extrair o sufixo da pasta (hum, eco, etc.)
    sufixo = nome_pasta.replace("functions_module_ish_", "")
    
    # Construir o nome do arquivo correspondente
    nome_arquivo_esperado = f"ish_{sufixo}"
    coluna_esperada = f"ire_cs_{sufixo}"
    
    print(f"  🔍 Procurando arquivo: {nome_arquivo_esperado}")
    print(f"  🔍 Procurando coluna: {coluna_esperada}")
    
    # 4.4. Procurar o arquivo específico
    padrao_arquivo = os.path.join(pasta_output, f"{nome_arquivo_esperado}*")
    arquivos_encontrados = glob.glob(padrao_arquivo)
    
    # Filtrar apenas arquivos (não pastas)
    arquivos_encontrados = [a for a in arquivos_encontrados if os.path.isfile(a)]
    
    if not arquivos_encontrados:
        print(f"  ⚠️ Arquivo '{nome_arquivo_esperado}' não encontrado em {pasta_output}")
        print(f"     Arquivos disponíveis: {os.listdir(pasta_output)}")
        continue
    
    arquivo = arquivos_encontrados[0]
    nome_arquivo = os.path.basename(arquivo)
    print(f"  📄 Arquivo encontrado: {nome_arquivo}")
    
    try:
        # 4.5. Ler o arquivo (assumindo CSV - ajuste se necessário)
        df_temp = pd.read_csv(arquivo)
        
        # 4.6. Verificar se a coluna esperada existe
        if coluna_esperada not in df_temp.columns:
            print(f"  ⚠️ Coluna '{coluna_esperada}' não encontrada")
            print(f"     Colunas disponíveis: {df_temp.columns.tolist()}")
            continue
        
        # 4.7. Verificar se a coluna COBACIA existe
        if 'COBACIA' not in df_temp.columns:
            print(f"  ⚠️ Coluna 'COBACIA' não encontrada em {nome_arquivo}")
            print(f"     Colunas disponíveis: {df_temp.columns.tolist()}")
            continue
        
        # 4.8. Armazenar o dataframe com COBACIA e a coluna de interesse
        df_para_merge = df_temp[['COBACIA', coluna_esperada]].copy()
        
        # 4.9. Adicionar ao dicionário (usando o sufixo como chave)
        dataframes_dict[sufixo] = df_para_merge
        
        print(f"  ✅ Coluna '{coluna_esperada}' extraída com sucesso!")
        print(f"     📊 {len(df_temp)} linhas")
        print(f"     🔑 COBACIA: {df_temp['COBACIA'].nunique()} valores únicos")
        
    except Exception as e:
        print(f"  ❌ Erro ao ler {arquivo}: {e}")
        continue

# Verificar se encontramos dataframes para fazer o merge
if len(dataframes_dict) < 2:
    print("\n❌ Não foram encontrados arquivos suficientes para fazer o merge.")
    print(f"   Encontrados: {list(dataframes_dict.keys())}")
    print("   Esperados: hum, eco (pelo menos 2)")
    exit()

# Fazer o merge dos dataframes usando COBACIA como chave
print("\n🔗 Fazendo merge dos dataframes usando COBACIA...")

# Começar com o primeiro dataframe
chaves = list(dataframes_dict.keys())
df_final = dataframes_dict[chaves[0]]

# Fazer merge com os demais
for chave in chaves[1:]:
    df_final = pd.merge(df_final, dataframes_dict[chave], on='COBACIA', how='outer')
    print(f"  ✅ Merge com '{chave}' concluído")

# Ordenar por COBACIA 
df_final = df_final.sort_values('COBACIA').reset_index(drop=True)

# Verificar se há valores nulos após o merge
# print(f"\n🔍 Verificando valores nulos após o merge:")
# print(df_final.isnull().sum())

# Calcular o cs_ish (apenas com as colunas ire_cs_*)
colunas_ire_cs = [col for col in df_final.columns if col.startswith('ire_cs_')]
df_final["cs_ish"] = compute_cs_ish(df_final, colunas_ire_cs)


# Mostrar quantos COBACIA únicos em cada coluna
print(f"\n🔑 Quantidade de COBACIA únicos por coluna:")
for col in df_final.columns:
    if col != 'cs_ish':
        print(f"   {col}: {df_final[col].count()} valores não-nulos")