import requests
import csv
from datetime import datetime
import os
import math

def luftfeuchte(temp, dewp):
    if temp is None or dewp is None or temp == "" or dewp == "":
        return ""
    a = 17.27
    b = 237.7
    gamma = (a * float(dewp)) / (b + float(dewp)) - (a * float(temp)) / (b + float(temp))
    return round(100 * math.exp(gamma), 1)

url = "https://aviationweather.gov/api/data/metar?ids=ETNT&format=json"
datei = "metar_werte.csv"

try:
    response = requests.get(url, timeout=30)
    data = response.json()[0]
    
    temp = data.get("temp", "")
    taupunkt = data.get("dewp", "")
    wind = data.get("wspd", "")
    richtung = data.get("wdir", "")
    zeit = data.get("reportTime", "")
    feuchte = luftfeuchte(temp, taupunkt)
    
    if zeit:
        dt = datetime.fromisoformat(zeit.replace("Z", "+00:00"))
        stamp = dt.strftime("%Y%m%d%H")
    else:
        stamp = datetime.utcnow().strftime("%Y%m%d%H")
    
    neu = not os.path.exists(datei)
    
    with open(datei, "a", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        if neu:
            writer.writerow(["DatumStunde", "Temperatur", "Taupunkt", "Wind_kt", "Windrichtung", "Feuchte"])
        writer.writerow([stamp, temp, taupunkt, wind, richtung, feuchte])
    
    print(f"Gespeichert: {stamp} | {temp}°C | Taupunkt {taupunkt}°C | {feuchte}%")

except Exception as e:
    print(f"Fehler: {e}")
