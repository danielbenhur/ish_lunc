# --- gdfhead.py ---

import geopandas as gpd
import sys
f=sys.argv[1]
gdf=gpd.read_file(f)
gdf.plot()
print(gdf.head())
