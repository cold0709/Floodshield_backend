import requests
from datetime import datetime

CLOUDBURST_MM_HR = 100   # IMD definition: >=100mm rain in 1 hour
SEVERE_MM_HR = 50
MODERATE_MM_HR = 20


def get_cloudburst_risk(lat, lon):
    """
    Detects cloudburst risk using Open-Meteo hourly precipitation forecast.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "hourly": "precipitation",
            "past_days": 1, "forecast_days": 1,
            "timezone": "Asia/Kolkata"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()["hourly"]
        times = data["time"]
        precip = data["precipitation"]

        now_str = datetime.now().strftime("%Y-%m-%dT%H:00")
        idx = times.index(now_str) if now_str in times else len(times) // 2

        current_rate = precip[idx] or 0
        future_window = precip[idx: idx + 6]
        max_forecast = max(future_window) if future_window else current_rate

        if max_forecast >= CLOUDBURST_MM_HR:
            level, score = "CLOUDBURST_IMMINENT", 100
        elif max_forecast >= SEVERE_MM_HR:
            level, score = "SEVERE_WARNING", 75
        elif max_forecast >= MODERATE_MM_HR:
            level, score = "MODERATE_WARNING", 45
        else:
            level, score = "NORMAL", round((max_forecast / MODERATE_MM_HR) * 45, 1)

        return {
            "status": "ok",
            "level": level,
            "score": score,
            "current_rate_mm_hr": round(current_rate, 1),
            "max_forecast_6hr_mm_hr": round(max_forecast, 1)
        }
    except Exception as e:
        return {
            "status": "fallback", "level": "NORMAL", "score": 0,
            "current_rate_mm_hr": 0, "max_forecast_6hr_mm_hr": 0, "error": str(e)
        }


def get_hourly_forecast(lat, lon, hours=24):
    """
    Returns hourly precipitation forecast — used by the /api/forecast endpoint
    to draw a risk trend line on the frontend.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "hourly": "precipitation", "forecast_days": 1,
            "timezone": "Asia/Kolkata"
        }
        data = requests.get(url, params=params, timeout=10).json()["hourly"]
        trend = []
        for t, p in zip(data["time"][:hours], data["precipitation"][:hours]):
            p = p or 0
            trend.append({
                "time": t,
                "predicted_rain_mm": p,
                "estimated_risk": round(min(p * 1.2, 100), 1)
            })
        return trend
    except Exception:
        return []