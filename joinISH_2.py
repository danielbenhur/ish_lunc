import pandas as pd
import os
import glob

# 1. Definir o caminho da pasta principal onde estão as pastas functions_module_ish_
caminho_base = "."  # Altere para o caminho correto, ex: "./dados"

# 2. Encontrar todas as pastas que começam com "functions_module_ish_"
padrao_pasta = os.path.join(caminho_base, "functions_module_ish_*")
pastas_encontradas = glob.glob(padrao_pasta)

# Filtrar apenas pastas (não arquivos)
pastas_encontradas = [p for p in pastas_encontradas if os.path.isdir(p)]

print(f"📁 Pastas functions_module_ish_ encontradas: {len(pastas_encontradas)}")

# 3. Lista para armazenar os dataframes extraídos
dataframes_lista = []

# 4. Para cada pasta encontrada
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
    # Exemplo: "functions_module_ish_hum" -> "hum"
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
    
    arquivo = arquivos_encontrados[0]  # Pega o primeiro arquivo encontrado
    nome_arquivo = os.path.basename(arquivo)
    print(f"  📄 Arquivo encontrado: {nome_arquivo}")
    
    try:
        # 4.5. Ler o arquivo (assumindo CSV - ajuste se necessário)
        df_temp = pd.read_csv(arquivo)
        
        # Se for Excel, use: df_temp = pd.read_excel(arquivo)
        # Se for Parquet, use: df_temp = pd.read_parquet(arquivo)
        
        # 4.6. Verificar se a coluna esperada existe
        if coluna_esperada not in df_temp.columns:
            print(f"  ⚠️ Coluna '{coluna_esperada}' não encontrada")
            print(f"     Colunas disponíveis: {df_temp.columns.tolist()}")
            continue
        
        # 4.7. Extrair a coluna
        # O nome da coluna no dataframe final será: ire_cs_hum
        nome_coluna_final = f"{coluna_esperada}"
        
        df_coluna = pd.DataFrame({
            nome_coluna_final: df_temp[coluna_esperada]
        })
        
        dataframes_lista.append(df_coluna)
        
        print(f"  ✅ Coluna '{coluna_esperada}' extraída com sucesso!")
        print(f"     📊 {len(df_temp[coluna_esperada])} linhas")
        
    except Exception as e:
        print(f"  ❌ Erro ao ler {arquivo}: {e}")
        continue

# 5. Verificar se encontramos algum dataframe
if not dataframes_lista:
    print("\n❌ Nenhum dataframe foi extraído. Verifique:")
    print("  - Se as pastas 'output' existem dentro de cada functions_module_ish_")
    print("  - Se os arquivos seguem o padrão: ish_[sufixo] (ex: ish_hum, ish_eco)")
    print("  - Se os arquivos contêm colunas no padrão: ire_cs_[sufixo] (ex: ire_cs_hum, ire_cs_eco)")
    print("  - Se os arquivos são CSV (ou ajuste o formato no código)")
    exit()

# 6. Juntar todos os dataframes lado a lado (horizontalmente)
print("\n🔗 Juntando todos os dataframes...")
df_final = pd.concat(dataframes_lista, axis=1)

# 7. Salvar o dataframe final
df_final.to_csv("dataframe_final_ire_cs.csv", index=False)
print(f"\n✅ Dataframe final criado com sucesso!")
print(f"   📊 Linhas: {df_final.shape[0]}")
print(f"   📊 Colunas: {df_final.shape[1]}")
print(f"   📋 Nomes das colunas:")
for col in df_final.columns:
    print(f"      - {col}")

# 8. Mostrar as primeiras linhas do dataframe final
print("\n📊 Primeiras 5 linhas do dataframe final:")
print(df_final.head())

# 9. Mostrar estatísticas básicas
print("\n📊 Estatísticas básicas:")
print(df_final.describe())

# 10. Salvar também em Excel (opcional)
# df_final.to_excel("dataframe_final_ire_cs.xlsx", index=False)
# print("\n✅ Arquivo Excel também salvo como 'dataframe_final_ire_cs.xlsx'")

# 11. Verificar se há valores nulos
print(f"\n🔍 Valores nulos por coluna:")
print(df_final.isnull().sum())

# 12. Mostrar resumo das pastas processadas
print(f"\n📋 Resumo das pastas processadas:")
for i, col in enumerate(df_final.columns):
    # Extrair o sufixo do nome da coluna
    if 'ire_cs_' in col:
        partes = col.split('_')
        sufixo = partes[2] if len(partes) > 2 else 'desconhecido'
        pasta_origem = col.replace(f"ire_cs_{sufixo}_", "")
        print(f"   {i+1}. {col}")
        print(f"      → Sufixo: {sufixo}, Pasta: {pasta_origem}")