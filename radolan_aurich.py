#!/usr/bin/env python3
import urllib.request
import xarray as xr
import numpy as np
import wradlib as wrl
from datetime import datetime, timedelta
import os

print("Skript wird geladen...")

LAT = 53.47
LON = 7.48
CSV_PATH = "radolan_aurich.csv"

def get_latest_radolan_url():
    now = datetime.utcnow()
    base_url = "https://opendata.dwd.de/weather/radar/radolan/rw/"
    
    for hours_back in range(0, 18):
        check_time = now - timedelta(hours=hours_back)
        timestamp = check_time.strftime("%y%m%d%H00")
        filename = f"raa01-rw_10000-{timestamp}-dwd---bin.hdf5"
        url = base_url + filename
        print(f"Prüfe: {url}")
        
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    return url, check_time
        except Exception:
            continue
    return None, None

def write_csv(zeitstempel, niederschlag):
    # Prüfen, ob der Zeitstempel schon existiert
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r") as f:
            inhalt = f.read()
            if zeitstempel in inhalt:
                print(f"Zeitstempel {zeitstempel} bereits vorhanden, überspringe.")
                return
    
    header = "Zeitstempel;Niederschlag_mm\n"
    zeile = f"{zeitstempel};{niederschlag}\n"
    
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w") as f:
            f.write(header)
    
    with open(CSV_PATH, "a") as f:
        f.write(zeile)
    print(f"CSV aktualisiert: {zeitstempel} -> {niederschlag} mm")

def main():
    print("Skript gestartet")
    url, timestamp = get_latest_radolan_url()
    
    if not url:
        print("Keine RADOLAN-Datei gefunden.")
        return
    
    print(f"Lade: {url}")
    local_nc = "/tmp/radolan_temp.nc"
    
    try:
        urllib.request.urlretrieve(url, local_nc)
        print("Datei geladen, öffne Dataset...")
        
        try:
            ds = xr.open_dataset(local_nc, group="dataset1/data1")
        except Exception:
            ds = xr.open_dataset(local_nc)
        
        data = ds["data"].values
        
        # Korrekte Position mit wradlib berechnen
        radolan_grid = wrl.georef.get_radolan_grid(nrows=1200, ncols=1100, wgs84=True)
        lon_grid = radolan_grid[..., 0]
        lat_grid = radolan_grid[..., 1]
        
        dist = np.sqrt((lat_grid - LAT)**2 + (lon_grid - LON)**2)
        zeile, spalte = np.unravel_index(np.argmin(dist), dist.shape)
        
        wert = int(data[zeile, spalte])
        print(f"Nächster Punkt: Zeile {zeile}, Spalte {spalte}")
        print(f"Rohwert: {wert}")
        
        if wert == 65535 or wert < 0:
            niederschlag = 0.0
        else:
            niederschlag = wert * 0.1
        
        print(f"Niederschlag: {niederschlag} mm")
        
        zeitstempel = timestamp.strftime("%Y%m%d%H")
        write_csv(zeitstempel, round(niederschlag, 1))
        
    except Exception as e:
        print(f"Fehler: {e}")
    finally:
        if os.path.exists(local_nc):
            os.remove(local_nc)

if __name__ == "__main__":
    main()
