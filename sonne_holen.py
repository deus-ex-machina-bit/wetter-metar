import requests
import xarray as xr
import csv
import os
from io import BytesIO
from pyproj import Transformer

# Aurich-Tannenhausen
lat_ziel = 53.47
lon_ziel = 7.48

url_basis = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/duett/sunshine_duration/recent/"
datei_csv = "sonne_werte.csv"

try:
    # Verzeichnis auflisten
    r = requests.get(url_basis, timeout=30)
    zeilen = r.text.split("\n")
    dateien = [z.split('"')[1] for z in zeilen if "SDU_duett" in z and ".nc" in z]
    neueste = sorted(dateien)[-1]
    
    # NetCDF laden
    nc_url = url_basis + neueste
    nc_data = requests.get(nc_url, timeout=60).content
    ds = xr.open_dataset(BytesIO(nc_data))
    
    # Koordinaten umrechnen (EPSG:4326 → EPSG:3035)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
    x_ziel, y_ziel = transformer.transform(lon_ziel, lat_ziel)
    
    # Nächsten Punkt finden
    punkt = ds["SDU"].sel(x=x_ziel, y=y_ziel, method="nearest")
    wert = float(punkt.values.squeeze())
    
    # Zeitstempel
    zeit_str = neueste.split("_")[4][:10]
    
    neu = not os.path.exists(datei_csv)
    with open(datei_csv, "a", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        if neu:
            writer.writerow(["DatumStunde", "Sonnenscheindauer_min"])
        writer.writerow([zeit_str, round(wert, 1)])
    
    print(f"Gespeichert: {zeit_str} | {round(wert,1)} min")

except Exception as e:
    print(f"Fehler: {e}")
    
