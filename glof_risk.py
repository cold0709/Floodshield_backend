import requests
from datetime import datetime, timedelta


def get_seismic_activity(lat, lon, radius_km=150):
    """
    Checks recent earthquakes near a location using USGS Earthquake API.
    Earthquakes can trigger glacial lake outbursts and landslide dams.
    """
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=7)
        params = {
            "format": "geojson",
            "starttime": start.strftime("%Y-%m-%d"),
            "endtime": end.strftime("%Y-%m-%d"),
            "latitude": lat, "longitude": lon,
            "maxradiuskm": radius_km, "minmagnitude": 3.0
        }
        r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query", params=params, timeout=10)
        quakes = r.json().get("features", [])
        return {
            "count_7days": len(quakes),
            "max_magnitude": max([q["properties"]["mag"] for q in quakes], default=0)
        }
    except Exception:
        return {"count_7days": 0, "max_magnitude": 0}


def get_temperature_anomaly(lat, lon):
    """
    Rapid temperature spikes accelerate glacier/snowmelt, increasing GLOF risk.
    """
    try:
        params = {
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max",
            "past_days": 14, "timezone": "Asia/Kolkata"
        }
        r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
        temps = [t for t in r.json().get("daily", {}).get("temperature_2m_max", []) if t is not None]
        if len(temps) < 7:
            return {"anomaly": 0}
        recent = sum(temps[-3:]) / 3
        base = sum(temps[:-3]) / max(len(temps[:-3]), 1)
        return {"anomaly": round(recent - base, 2)}
    except Exception:
        return {"anomaly": 0}


def get_glof_risk(village):
    """
    Calculates Glacial Lake Outburst Flood risk.
    Only applicable to villages with a 'glacial_lake' entry in config.py.
    """
    lake = village.get("glacial_lake")
    if not lake:
        return {"applicable": False, "score": 0, "risk_level": "NONE"}

    seismic = get_seismic_activity(village["lat"], village["lon"])
    temp = get_temperature_anomaly(village["lat"], village["lon"])

    base_scores = {"low": 10, "medium": 30, "high": 50, "critical": 70}
    score = base_scores.get(lake["risk_level"], 20)

    if seismic["max_magnitude"] >= 5:
        score += 30
    elif seismic["max_magnitude"] >= 4:
        score += 15

    if temp["anomaly"] >= 3:
        score += 20
    elif temp["anomaly"] >= 1.5:
        score += 10

    score = min(score, 100)
    risk_level = ("CRITICAL" if score >= 70 else "HIGH" if score >= 50
                  else "MODERATE" if score >= 25 else "LOW")

    return {
        "applicable": True,
        "score": score,
        "risk_level": risk_level,
        "lake_name": lake["name"],
        "base_risk_level": lake["risk_level"],
        "seismic_activity": seismic,
        "temperature_anomaly": temp
    }