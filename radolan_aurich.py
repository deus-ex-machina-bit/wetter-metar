#!/usr/bin/env python3
import urllib.request
import xarray as xr
import numpy as np
from datetime import datetime, timedelta
import os

LAT = 53.46
LON = 7.50

def get_latest_radolan_url():
    now = datetime.utcnow()
    for hours_back in range(0, 12):  # etwas weiter zurückschauen
        check_time = now - timedelta(hours=hours_back)
        year = check_time.strftime("%Y")
        date_str = check_time.strftime("%Y%m%d")
        hour_str = check_time.strftime("%H")
        filename = f"{date_str}_{hour_str}0000_RW_1x1.nc"
        url = f"https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/{year}/{filename}"
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return url, check_time
        except Exception:
            continue
    return None, None

def main():
    csv_path = "radolan_aurich.csv"
    url, timestamp = get_latest_radolan_url()

    if not url:
        print("Keine aktuelle RADOLAN-Datei gefunden. Erstelle leere CSV falls nötig.")
        if not os.path.exists(csv_path):
            with open(csv_path, "w") as f:
                f.write("Zeitstempel;Niederschlag_mm\n")
                f.write(f"{datetime.utcnow().strftime('%Y%m%d%H')};0.0\n")
        return

    print(f"Lade: {url}")
    local_nc = "/tmp/radolan_temp.nc"
    urllib.request.urlretrieve(url, local_nc)

    ds = xr.open_dataset(local_nc)
    val = ds["RW"].sel(latitude=LAT, longitude=LON, method="nearest").values
    if isinstance(val, np.ndarray):
        val = float(val.flat[0]) if val.size > 0 else 0.0
    else:
        val = float(val)

    zeitstempel = timestamp.strftime("%Y%m%d%H")
    niederschlag = round(val, 1)

    header = "Zeitstempel;Niederschlag_mm\n"
    zeile = f"{zeitstempel};{niederschlag}\n"

    if not os.path.exists(csv_path):
        with open(csv_path, "w") as f:
            f.write(header)
            f.write(zeile)
    else:
        with open(csv_path, "r") as f:
            inhalt = f.read()
        if zeitstempel not in inhalt:
            with open(csv_path, "a") as f:
                f.write(zeile)
        else:
            print(f"Zeitstempel {zeitstempel} bereits vorhanden.")

    print(f"Gespeichert: {zeitstempel} -> {niederschlag} mm")

    if os.path.exists(local_nc):
        os.remove(local_nc)

if __name__ == "__main__":
    main()
