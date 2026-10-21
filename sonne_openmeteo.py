import requests
import csv
import os
from datetime import datetime, timezone

# Aurich-Tannenhausen
lat = 53.47
lon = 7.48

url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={lat}&longitude={lon}"
    "&hourly=sunshine_duration"
    "&past_days=2"
    "&forecast_days=1"
    "&timezone=UTC"
)

datei_csv = "sonne_openmeteo.csv"

try:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()

    times = data["hourly"]["time"]
    values = data["hourly"]["sunshine_duration"]

    # Bestehende Zeitstempel einlesen
    vorhandene = set()
    if os.path.exists(datei_csv):
        with open(datei_csv, "r", newline="") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)  # Header überspringen
            for row in reader:
                if row:
                    vorhandene.add(row[0])

    neu = not os.path.exists(datei_csv)
    hinzugefuegt = 0

    with open(datei_csv, "a", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        if neu:
            writer.writerow(["Zeitstempel", "Sonnenscheindauer_min"])

        for t, v in zip(times, values):
            # Zeitstempel ins Format YYYYMMDDHH bringen
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
            zeit_str = dt.strftime("%Y%m%d%H")

            if zeit_str not in vorhandene and v is not None:
                writer.writerow([zeit_str, round(v / 60, 1)])  # Sekunden → Minuten
                vorhandene.add(zeit_str)
                hinzugefuegt += 1

    print(f"Open-Meteo: {hinzugefuegt} neue Zeile(n) hinzugefügt.")

except Exception as e:
    print(f"Fehler: {e}")
