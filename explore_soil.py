import geopandas as gpd
import os

# Get all the soil files you detected earlier
soil_dir = "data/ssurgo"
soil_files = [f for f in os.listdir(soil_dir) if f.endswith('.shp')]

print(f"{'='*60}\nSOIL DATA METADATA EXPORT\n{'='*60}")

for file in soil_files:
    path = os.path.join(soil_dir, file)
    try:
        # Load 1 row for the schema
        gdf = gpd.read_file(path, rows=1)
        
        print(f"\n--- FILE: {file} ---")
        print(f"CRS: {gdf.crs}")
        print(f"Columns: {gdf.columns.tolist()}")
        print("Sample Data:", gdf.iloc[0].to_dict())
        print("-" * 30)
        
    except Exception as e:
        print(f"Error reading {file}: {e}")