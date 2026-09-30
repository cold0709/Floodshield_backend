import requests
import random

class WeatherFetcher:
    @staticmethod
    def get_data(lat, lon, name):
        print(f"  🌦️  Fetching weather for {name}...")
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,precipitation",
                "hourly": "precipitation,soil_moisture_0_to_7cm",
                "timezone": "Asia/Kolkata"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            rain = sum(data['hourly']['precipitation'][-24:] or [])
            soil = data['hourly']['soil_moisture_0_to_7cm'][-1] or 0.2
            temp = data['current']['temperature_2m']
            
            return {"rain": round(rain, 2), "soil": round(min(soil*250, 100), 1), "temp": temp}
        except:
            print(f"    ️ API failed, using fallback data.")
            return {"rain": round(random.uniform(5, 80), 2), "soil": round(random.uniform(40, 80), 1), "temp": 15}