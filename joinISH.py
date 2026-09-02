import yaml 
import pandas as pd
import geopandas as gpd
import fiona

def load_gpkg_with_fid(filename, layer, merge_column):
    """
    Lê um GeoPackage usando fiona e inclui o FID (feature id)
    no dicionário de propriedades como merge_column
    """
    features = []
    with fiona.open(filename, layer=layer) as src:
        for feat in src:
            props = dict(feat['properties'])
            try:
                props[merge_column] = int(feat['id'])
            except ValueError:
                props[merge_column] = feat['id']
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

def main():
    # a escolha das dimensões a serem integradas é feita no arquivo yaml
    # dimensões a serem integradas feitas a partir das escolhas do usuário
    yaml_file_path = 'parameters.yaml'
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)

    dataframes_dict = {}
    for dimension in config['dimensions']:
        arquivo = dimension['path']
        df_temp = pd.read_csv(arquivo)
        # print(df_temp.head())
        coluna_esperada = dimension['column']
        merge_column = dimension['merge_column']
        df_para_merge = df_temp[[merge_column, coluna_esperada]].copy()
        
        # Verifica se há duplicatas e as agrega (média)
        if df_para_merge[merge_column].duplicated().any():
            print(f"  ⚠️ Duplicatas encontradas para COBACIA. Calculando média...")
            df_para_merge = df_para_merge.groupby(merge_column, as_index=False)[coluna_esperada].mean()
        
        dataframes_dict[coluna_esperada] = df_para_merge
    
    print("\n🔗 Fazendo merge dos dataframes usando COBACIA...")
    chaves = list(dataframes_dict.keys())
    df_final = dataframes_dict[chaves[0]]

    for chave in chaves[1:]:
        df_final = pd.merge(df_final, dataframes_dict[chave], on=merge_column, how='left')
        # print(f"  ✅ Merge com '{chave}' concluído")

        # Verifica se houve duplicação após o merge
        if df_final[merge_column].duplicated().any():
            # print(f"  ⚠️ Duplicatas detectadas após merge com {chave}. Agregando...")
            # Agrega todas as colunas que não são COBACIA pela média
            cols_to_agg = [col for col in df_final.columns if col != merge_column]
            df_final = df_final.groupby(merge_column, as_index=False)[cols_to_agg].mean()
    
    # Ordenar por COBACIA
    df_final = df_final.sort_values(merge_column).reset_index(drop=True)

    # Calcular o cs_ish (apenas um valor por COBACIA)
    colunas_ire_cs = [col for col in df_final.columns if col.startswith('ire_cs_')]
    df_final["cs_ish"] = compute_cs_ish(df_final, colunas_ire_cs)
    print(df_final.head())

    # Integrando o GPKG ao projeto
    gpkg_file = config['bho']['path']
    layer = config['bho']['layer']
    gdf = load_gpkg_with_fid(gpkg_file, layer, 'cobacia')

    # juntando as colunas calculadas com o mapa
    gdf_final = gdf.merge(df_final, on=merge_column, how='left')

    caminho_final = config['output']
    caminho_csv = caminho_final['folder'] + '/' + caminho_final['csv_name']
    caminho_gpkg = caminho_final['folder'] + '/' + caminho_final['gpkg_name']
    gdf_final.to_csv(caminho_csv, index=False)
    gdf_final.to_file(caminho_gpkg, layer='resultado', driver='GPKG')
    
if __name__ == "__main__":
    main()