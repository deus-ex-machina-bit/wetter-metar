import requests
import xarray as xr
import csv
import os
from datetime import datetime
from io import BytesIO

# Aurich-Tannenhausen (ungefähr – bei Bedarf anpassen)
lat_ziel = 53.47
lon_ziel = 7.48

url_basis = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/duett/sunshine_duration/recent/"
datei_csv = "sonne_werte.csv"

try:
    # Verzeichnis auflisten und neueste Datei finden
    r = requests.get(url_basis, timeout=30)
    zeilen = r.text.split("\n")
    dateien = [z.split('"')[1] for z in zeilen if "SDU_duett" in z and ".nc" in z]
    if not dateien:
        print("Keine Dateien gefunden")
        exit()
    neueste = sorted(dateien)[-1]
    
    # NetCDF herunterladen
    nc_url = url_basis + neueste
    nc_data = requests.get(nc_url, timeout=60).content
    
    # Öffnen und nächsten Punkt finden
    ds = xr.open_dataset(BytesIO(nc_data))
    var_name = list(ds.data_vars)[0]
    punkt = ds[var_name].sel(lat=lat_ziel, lon=lon_ziel, method="nearest")
    wert = float(punkt.values)
    
    # Zeitstempel aus Dateiname (YYYYMMDDHH)
    zeit_str = neueste.split("_")[4][:10]
    stamp = zeit_str
    
    neu = not os.path.exists(datei_csv)
    with open(datei_csv, "a", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        if neu:
            writer.writerow(["DatumStunde", "Sonnenscheindauer_min"])
        writer.writerow([stamp, round(wert, 1)])
    
    print(f"Gespeichert: {stamp} | {round(wert,1)} min")

except Exception as e:
    print(f"Fehler: {e}")
