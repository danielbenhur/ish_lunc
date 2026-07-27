import pandas as pd
import os
import glob
import geopandas as gpd
from shapely.geometry import Point
import fiona

def load_gpkg_with_fid(filename, layer):
    """
    Lê um GeoPackage usando fiona e inclui o FID (feature id)
    no dicionário de propriedades como 'cobacia'
    """
    features = []
    with fiona.open(filename, layer=layer) as src:
        for feat in src:
            props = dict(feat['properties'])
            try:
                props['cobacia'] = int(feat['id'])
            except ValueError:
                props['cobacia'] = feat['id']
            features.append({
                "properties": props,
                "geometry": feat["geometry"]
            })
        crs = src.crs
    return gpd.GeoDataFrame.from_features(features, crs=crs)

def compute_cs_ish(df, dim_cols):
    """
    Calcula a média das colunas de dimensão, considerando apenas valores > 0.
    Retorna uma Series com um único cs_ish por COBACIA.
    """
    # Converte para numérico
    df_numeric = df[dim_cols].apply(pd.to_numeric, errors='coerce')
    
    # Calcula a média para cada linha (ignorando valores <= 0 e NaN)
    cs_ish = df_numeric.apply(lambda row: row[row > 0.0].mean() if (row[row > 0.0].count() > 0) else 0.0, axis=1)
    
    return cs_ish

# 1. Definir o caminho da pasta principal
caminho_base = "."

# 2. Encontrar todas as pastas que começam com "functions_module_ish_"
padrao_pasta = os.path.join(caminho_base, "functions_module_ish_*")
pastas_encontradas = glob.glob(padrao_pasta)
pastas_encontradas = [p for p in pastas_encontradas if os.path.isdir(p)]

print(f"📁 Pastas functions_module_ish_ encontradas: {len(pastas_encontradas)}")

# 3. Dicionário para armazenar os dataframes
dataframes_dict = {}

# 4. Para cada pasta encontrada
for pasta in pastas_encontradas:
    print(f"\n📂 Processando: {os.path.basename(pasta)}")
    
    pasta_output = os.path.join(pasta, "output")
    if not os.path.exists(pasta_output):
        print(f"  ⚠️ Pasta 'output' não encontrada")
        continue
    
    nome_pasta = os.path.basename(pasta)
    sufixo = nome_pasta.replace("functions_module_ish_", "")
    nome_arquivo_esperado = f"ish_{sufixo}"
    coluna_esperada = f"ire_cs_{sufixo}"
    
    print(f"  🔍 Procurando arquivo: {nome_arquivo_esperado}")
    print(f"  🔍 Procurando coluna: {coluna_esperada}")
    
    padrao_arquivo = os.path.join(pasta_output, f"{nome_arquivo_esperado}*")
    arquivos_encontrados = glob.glob(padrao_arquivo)
    arquivos_encontrados = [a for a in arquivos_encontrados if os.path.isfile(a)]
    
    if not arquivos_encontrados:
        print(f"  ⚠️ Arquivo '{nome_arquivo_esperado}' não encontrado")
        continue
    
    arquivo = arquivos_encontrados[0]
    nome_arquivo = os.path.basename(arquivo)
    print(f"  📄 Arquivo encontrado: {nome_arquivo}")
    
    try:
        df_temp = pd.read_csv(arquivo)
        
        if coluna_esperada not in df_temp.columns:
            print(f"  ⚠️ Coluna '{coluna_esperada}' não encontrada")
            continue
        
        if 'COBACIA' not in df_temp.columns:
            print(f"  ⚠️ Coluna 'COBACIA' não encontrada")
            continue
        
        # 🔥 IMPORTANTE: Garantir que cada COBACIA tenha apenas um valor
        # Se houver duplicatas, mantém a média ou o primeiro valor
        df_para_merge = df_temp[['COBACIA', coluna_esperada]].copy()
        
        # Verifica se há duplicatas e as agrega (média)
        if df_para_merge['COBACIA'].duplicated().any():
            print(f"  ⚠️ Duplicatas encontradas para COBACIA. Calculando média...")
            df_para_merge = df_para_merge.groupby('COBACIA', as_index=False)[coluna_esperada].mean()
        
        dataframes_dict[sufixo] = df_para_merge
        
        print(f"  ✅ Coluna '{coluna_esperada}' extraída com sucesso!")
        print(f"     📊 {len(df_para_merge)} COBACIAS únicas")
        
    except Exception as e:
        print(f"  ❌ Erro ao ler {arquivo}: {e}")
        continue

# 5. Verificar se encontramos dataframes
if len(dataframes_dict) < 2:
    print("\n❌ Não foram encontrados arquivos suficientes.")
    exit()

# 6. Fazer o merge dos dataframes usando COBACIA
print("\n🔗 Fazendo merge dos dataframes usando COBACIA...")
chaves = list(dataframes_dict.keys())
df_final = dataframes_dict[chaves[0]]

for chave in chaves[1:]:
    df_final = pd.merge(df_final, dataframes_dict[chave], on='COBACIA', how='inner')
    print(f"  ✅ Merge com '{chave}' concluído")
    
    # Verifica se houve duplicação após o merge
    if df_final['COBACIA'].duplicated().any():
        print(f"  ⚠️ Duplicatas detectadas após merge com {chave}. Agregando...")
        # Agrega todas as colunas que não são COBACIA pela média
        cols_to_agg = [col for col in df_final.columns if col != 'COBACIA']
        df_final = df_final.groupby('COBACIA', as_index=False)[cols_to_agg].mean()

# 7. Ordenar por COBACIA
df_final = df_final.sort_values('COBACIA').reset_index(drop=True)

# 8. Calcular o cs_ish (apenas um valor por COBACIA)
colunas_ire_cs = [col for col in df_final.columns if col.startswith('ire_cs_')]
df_final["cs_ish"] = compute_cs_ish(df_final, colunas_ire_cs)

print(f"\n✅ Dataframe final com {len(df_final)} COBACIAS")
print(f"   Colunas: {df_final.columns.tolist()}")
print(f"   cs_ish - Mín: {df_final['cs_ish'].min():.2f}, Máx: {df_final['cs_ish'].max():.2f}, Média: {df_final['cs_ish'].mean():.2f}")

# 9. Salvar CSV (backup)
df_final.to_csv("dataframe_final_ire_cs.csv", index=False)
print(f"\n✅ CSV salvo: dataframe_final_ire_cs.csv")

# =====================================================
# 10. LER O GEODATAFRAME BHO_area.gpkg E FAZER JOIN
# =====================================================

print("\n🗺️ Carregando o GeoPackage BHO_area.gpkg...")

# 10.1. Verificar se o arquivo BHO_area.gpkg existe
gpkg_file = "/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/cnr_A/input/BHO_area.gpkg"
layer = "bho_area"  # default

try:
    # Carrega o GeoPackage utilizando a função que extrai a FID como 'cobacia'
    gdf = load_gpkg_with_fid(gpkg_file, layer)
    
    # Converte COBACIA para float para fazer o merge
    gdf['COBACIA'] = gdf['cobacia'].astype(float)
    gdf = gdf.drop(columns=['cobacia'])
    
    # 🔥 FAZ O MERGE FINAL - Garantindo que cada COBACIA tenha apenas um registro
    print(f"📊 GeoDataFrame: {len(gdf)} registros")
    print(f"📊 DataFrame final: {len(df_final)} registros")
    
    gdf_final = gdf.merge(df_final, on='COBACIA', how='inner')
    
    # Verifica duplicatas no resultado final
    if gdf_final['COBACIA'].duplicated().any():
        print("⚠️ Duplicatas detectadas no resultado final. Removendo...")
        gdf_final = gdf_final.drop_duplicates(subset=['COBACIA'], keep='first')
    
    print(f"✅ Merge final concluído: {len(gdf_final)} COBACIAS")
    
    # Salva como CSV
    gdf_final.to_csv('resultado.csv', index=False)
    print(f"✅ CSV salvo: resultado.csv")
    
    # Salva como GeoPackage se quiser
    gdf_final.to_file('resultado.gpkg', layer='resultado', driver='GPKG')
    
except FileNotFoundError:
    print(f"❌ Arquivo não encontrado: {gpkg_file}")
except Exception as e:
    print(f"❌ Erro ao processar GeoPackage: {e}")

print("\n🎯 Processamento concluído!")
print(f"   Últimas 5 COBACIAs: {gdf_final.head()}")