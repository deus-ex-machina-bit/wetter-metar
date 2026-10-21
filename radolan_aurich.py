#!/usr/bin/env python3
import urllib.request
import xarray as xr
import numpy as np
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
        write_csv(datetime.utcnow().strftime("%Y%m%d%H"), 0.0)
        return
    
    print(f"Lade: {url}")
    local_nc = "/tmp/radolan_temp.nc"
    
    try:
        urllib.request.urlretrieve(url, local_nc)
        print("Datei geladen, öffne Dataset...")
        ds = xr.open_dataset(local_nc)
        
        # ODIM_H5 Struktur
        if "dataset1" in ds:
            data = ds["dataset1"]["data1"]["data"]
        else:
            data = list(ds.data_vars.values())[0]
        
        print("Nächster Rasterpunkt wird gesucht...")
        point = data.sel(latitude=LAT, longitude=LON, method="nearest")
        print("Nächster Rasterpunkt:", float(point.latitude), float(point.longitude))
        print("Wert am nächsten Punkt:", float(point.values))
        
        val = float(point.values)
        zeitstempel = timestamp.strftime("%Y%m%d%H")
        write_csv(zeitstempel, round(val, 1))
        
    except Exception as e:
        print(f"Fehler: {e}")
        write_csv(datetime.utcnow().strftime("%Y%m%d%H"), 0.0)
    finally:
        if os.path.exists(local_nc):
            os.remove(local_nc)

if __name__ == "__main__":
    main()
