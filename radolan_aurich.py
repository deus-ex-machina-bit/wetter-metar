#!/usr/bin/env python3
import urllib.request
import xarray as xr
import numpy as np
from datetime import datetime, timedelta
import os

# Koordinaten Aurich (Näherung)
LAT = 53.46
LON = 7.50

def get_latest_radolan_url():
    """Baut die URL zur neuesten verfügbaren stündlichen RADOLAN-Datei."""
    # RADOLAN-Dateien werden mit etwas Verzögerung bereitgestellt.
    # Wir versuchen die letzten 6 Stunden.
    now = datetime.utcnow()
    for hours_back in range(0, 7):
        check_time = now - timedelta(hours=hours_back)
        year = check_time.strftime("%Y")
        date_str = check_time.strftime("%Y%m%d")
        hour_str = check_time.strftime("%H")
        filename = f"{date_str}_{hour_str}0000_RW_1x1.nc"
        url = f"https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/{year}/{filename}"
        try:
            # Kurzer HEAD-Request, um zu prüfen, ob die Datei existiert
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return url, check_time
        except Exception:
            continue
    return None, None

def main():
    url, timestamp = get_latest_radolan_url()
    if not url:
        print("Keine aktuelle RADOLAN-Datei gefunden.")
        return

    print(f"Lade: {url}")
    # Datei temporär speichern
    local_nc = "/tmp/radolan_temp.nc"
    urllib.request.urlretrieve(url, local_nc)

    # NetCDF öffnen und Pixel extrahieren
    ds = xr.open_dataset(local_nc)
    # Variable heißt meist "RW" (Regenwasser)
    val = ds["RW"].sel(latitude=LAT, longitude=LON, method="nearest").values
    # Manchmal ist der Wert ein Array, wir nehmen den ersten
    if isinstance(val, np.ndarray):
        val = float(val.flat[0]) if val.size > 0 else 0.0
    else:
        val = float(val)

    # Zeitstempel im Format wie bei den anderen Daten
    zeitstempel = timestamp.strftime("%Y%m%d%H")
    niederschlag = round(val, 1)

    # CSV schreiben (anhängend oder überschreiben – hier überschreiben wir mit dem neuesten Wert)
    csv_path = "radolan_aurich.csv"
    header = "Zeitstempel;Niederschlag_mm\n"
    zeile = f"{zeitstempel};{niederschlag}\n"

    # Wenn die Datei noch nicht existiert, Header schreiben
    if not os.path.exists(csv_path):
        with open(csv_path, "w") as f:
            f.write(header)
            f.write(zeile)
    else:
        # Prüfen, ob der Zeitstempel schon existiert
        with open(csv_path, "r") as f:
            inhalt = f.read()
        if zeitstempel not in inhalt:
            with open(csv_path, "a") as f:
                f.write(zeile)
        else:
            print(f"Zeitstempel {zeitstempel} bereits vorhanden, überspringe.")

    print(f"Gespeichert: {zeitstempel} -> {niederschlag} mm")

    # Aufräumen
    if os.path.exists(local_nc):
        os.remove(local_nc)

if __name__ == "__main__":
    main()
