import geopandas as gpd

# Checking the big ones to see their labels
files = {
    "Fresno": "data/parcels/fresno/fresno_parcels.shp",
    "Kern": "data/parcels/kern/kern_parcels.shp",
    "Tulare": "data/parcels/tulare/tulare_parcels.shp"
}

for name, path in files.items():
    print(f"\n--- {name} Metadata ---")
    gdf = gpd.read_file(path, rows=1) # Fast look at just one row
    print(f"CRS: {gdf.crs}") # The 'map language'
    print(f"Columns: {gdf.columns.tolist()}") # The headers
    print(f"Sample Data: {gdf.iloc[0].to_dict()}") # One actual row