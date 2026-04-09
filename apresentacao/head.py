import geopandas as gpd 

gdf = gpd.read_file("./mun_es.gpkg")

print(gdf.head)