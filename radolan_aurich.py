#!/usr/bin/env python3
import urllib.request
import xarray as xr
import numpy as np
from datetime import datetime, timedelta
import os

LAT = 53.46
LON = 7.50
CSV_PATH = "radolan_aurich.csv"

def get_latest_radolan_url():
    now = datetime.utcnow()
    for hours_back in range(0, 18):
        check_time = now - timedelta(hours=hours_back)
        year = check_time.strftime("%Y")
        date_str = check_time.strftime("%Y%m%d")
        hour_str = check_time.strftime("%H")
        filename = f"{date_str}_{hour_str}0000_RW_1x1.nc"
        url = f"https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/{year}/{filename}"
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
            f.write(zeile)
        print(f"CSV neu angelegt: {zeitstempel} -> {niederschlag} mm")
    else:
        with open(CSV_PATH, "r") as f:
            if zeitstempel in f.read():
                print(f"Zeitstempel {zeitstempel} bereits vorhanden.")
                return
        with open(CSV_PATH, "a") as f:
            f.write(zeile)
        print(f"CSV aktualisiert: {zeitstempel} -> {niederschlag} mm")

def main():
    url, timestamp = get_latest_radolan_url()
    if not url:
        print("Keine RADOLAN-Datei gefunden. Schreibe Platzhalter.")
        write_csv(datetime.utcnow().strftime("%Y%m%d%H"), 0.0)
        return

    print(f"Lade: {url}")
    local_nc = "/tmp/radolan_temp.nc"
    try:
        urllib.request.urlretrieve(url, local_nc)
        ds = xr.open_dataset(local_nc)
        val = ds["RW"].sel(latitude=LAT, longitude=LON, method="nearest").values
        if isinstance(val, np.ndarray):
            val = float(val.flat[0]) if val.size > 0 else 0.0
        else:
            val = float(val)
        zeitstempel = timestamp.strftime("%Y%m%d%H")
        write_csv(zeitstempel, round(val, 1))
    except Exception as e:
        print(f"Fehler beim Auslesen: {e}")
        write_csv(datetime.utcnow().strftime("%Y%m%d%H"), 0.0)
    finally:
        if os.path.exists(local_nc):
            os.remove(local_nc)

if __name__ == "__main__":
    main()
