import geopandas as gpd
import pandas as pd
import os
import glob
from shapely.validation import make_valid

# --- CONFIG ---
COUNTIES = ["tulare", "fresno", "kern"]
WATER_PATH = "data/water/i03_WaterDistricts.shp"
SOIL_DIR = "data/ssurgo/" 
JOIN_CRS = "EPSG:3310" 
MAP_CRS = "EPSG:4326"
MIN_ACRES = 2.0 

def run_analysis():
    print("--- 1. LOADING REFERENCE LAYERS ---")
    water = gpd.read_file(WATER_PATH).to_crs(JOIN_CRS)
    
    soil_list = []
    for f in glob.glob(os.path.join(SOIL_DIR, "*.shp")):
        temp_soil = gpd.read_file(f).to_crs(JOIN_CRS)
        for col in ['musym', 'MUSYM', 'mukey', 'MUKEY']:
            if col in temp_soil.columns:
                temp_soil = temp_soil.rename(columns={col: 'musym_raw'})
                break
        soil_list.append(temp_soil[['geometry', 'musym_raw']])
    
    full_soil = gpd.GeoDataFrame(pd.concat(soil_list, ignore_index=True), crs=JOIN_CRS)

    all_county_processed = []

    print(f"--- 2. PROCESSING GEOGRAPHY ---")
    for county in COUNTIES:
        p_path = f"data/parcels/{county}/{county}_parcels.shp"
        if not os.path.exists(p_path): continue
        
        print(f"Processing {county.capitalize()}...")
        parcels = gpd.read_file(p_path).to_crs(JOIN_CRS)
        parcels['geometry'] = parcels.geometry.map(lambda x: make_valid(x) if not x.is_valid else x)
        
        # Calculate Acreage & Filter
        parcels['Acres'] = (parcels.geometry.area / 4046.86).round(1).astype('float32')
        parcels = parcels[parcels['Acres'] >= MIN_ACRES].copy()
        
        # Join Water (1 for Yes, 0 for No to save space)
        parcels = gpd.sjoin(parcels, water[['geometry']], how="left", predicate="intersects")
        parcels['W_Dist'] = parcels['index_right'].apply(lambda x: 1 if pd.notnull(x) else 0).astype('int8')
        parcels.drop(columns=['index_right'], inplace=True)

        # Join Soil
        joined = gpd.sjoin(parcels, full_soil, how="left", predicate="intersects")
        
        prime_prefixes = ('1', '2', 'A', 'B', 'Ha', 'Ma', 'Va', 'Ce', 'Han', 'Gr')
        def categorize_soil(val):
            val = str(val)
            if val.startswith(prime_prefixes): return 1 # Prime
            return 0 # Marginal

        joined['S_Bin'] = joined['musym_raw'].apply(categorize_soil).astype('int8')

        def assign_id(row):
            if row['S_Bin'] == 1:
                return 1 if row['W_Dist'] == 1 else 2
            return 3

        joined['C_ID'] = joined.apply(assign_id, axis=1).astype('int8')
        joined['County'] = county.capitalize()
        
        all_county_processed.append(joined[['geometry', 'APN', 'C_ID', 'S_Bin', 'W_Dist', 'Acres', 'County']])

    print("--- 3. SCRUBBING & INDEXING ---")
    full_gdf = gpd.GeoDataFrame(pd.concat(all_county_processed, ignore_index=True), crs=JOIN_CRS)
    
    # Precision reduction for Lat/Lon
    centroids_4326 = full_gdf.geometry.centroid.to_crs(MAP_CRS)
    full_gdf['lat'] = centroids_4326.y.round(6).astype('float32')
    full_gdf['lon'] = centroids_4326.x.round(6).astype('float32')
    
    full_gdf = full_gdf.to_crs(MAP_CRS)
    
    # Save optimized CSV Index
    full_gdf[['APN', 'lat', 'lon', 'C_ID', 'S_Bin', 'W_Dist', 'Acres', 'County']].to_csv("search_index.csv", index=False)
    
    print("--- 4. FINAL EXPORT ---")
    full_gdf.to_file("all_counties_diamonds.geojson", driver='GeoJSON')
    print(f"SUCCESS: {len(full_gdf)} parcels optimized.")

if __name__ == "__main__":
    run_analysis()
