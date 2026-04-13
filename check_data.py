import geopandas as gpd
import os

# Paths updated to match your latest screenshots exactly
parcels = {
    "Fresno": "data/parcels/fresno/fresno_parcels.shp",
    "Kern": "data/parcels/kern/kern_parcels.shp",
    "Tulare": "data/parcels/tulare/tulare_parcels.shp",
}

soil_folder = "data/ssurgo"
# Updated to match your screenshot: i03_WaterDistricts
water_file = "data/water/i03_WaterDistricts.shp"

print(f"{'='*60}\nFINAL SYSTEM READINESS CHECK\n{'='*60}")

# 1. Check Parcels
for name, path in parcels.items():
    if os.path.exists(path):
        try:
            gdf = gpd.read_file(path)
            print(f"[OK] {name} Parcels loaded: {len(gdf):,} rows.")
            # Identifying filter columns (Use Codes, Zoning, etc.)
            cols = [c for c in gdf.columns if 'USE' in c.upper() or 'ZON' in c.upper()]
            print(f"     Potential Filter Columns: {cols}")
        except Exception as e:
            print(f"[ERROR] Found {name} but could not read it: {e}")
    else:
        print(f"[!] MISSING: {name} at {path}")

# 2. Check Water
if os.path.exists(water_file):
    try:
        w_gdf = gpd.read_file(water_file)
        print(f"\n[OK] Water Districts loaded: {len(w_gdf):,} boundaries found.")
    except Exception as e:
        print(f"\n[ERROR] Water file exists but failed to load: {e}")
else:
    print(f"\n[!] MISSING: Water Districts at {water_file}")

# 3. Check Soil
if os.path.exists(soil_folder):
    soil_files = [f for f in os.listdir(soil_folder) if f.endswith('.shp')]
    print(f"\n--- SOIL DATA: {len(soil_files)} Layers Detected ---")
    for s in soil_files:
        print(f"  - {s}")
else:
    print(f"\n[!] MISSING: Soil folder at {soil_folder}")

print(f"\n{'='*60}\nIf all parcels and water show [OK], you are ready to find Diamonds.\n{'='*60}")