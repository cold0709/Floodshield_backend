import os
import sys
import webbrowser
from datetime import datetime

# Import our Lego blocks
from config import VILLAGES, OUTPUT_DIR
from weather import WeatherFetcher
from risk_engine import RiskEngine
from shelters import ShelterManager
from database import Database
from visuals import Visualizer

def run_prototype():
    print("\n" + "="*60)
    print(" FLOODSHIELD PROTOTYPE - STARTING".center(60))
    print("="*60 + "\n")
    
    # 1. Init Database
    print("1️⃣  Initializing Database...")
    Database.init()
    
    # 2. Fetch Weather
    print("2️  Fetching Live Weather Data...")
    weather_data = {}
    for v in VILLAGES:
        weather_data[v['name']] = WeatherFetcher.get_data(v['lat'], v['lon'], v['name'])
    
    # 3. Calculate Risk
    print("3️⃣  Calculating Multi-Factor Risk...")
    results = []
    for v in VILLAGES:
        risk = RiskEngine.calculate(v, weather_data[v['name']])
        results.append(risk)
        print(f"   {risk['icon']} {risk['name']:12} | Score: {risk['risk_score']} | {risk['risk_level']}")
    
    # 4. Plan Evacuations
    print("4️⃣  Planning Evacuations...")
    for r in results:
        if r['people_at_risk'] > 0:
            plan = ShelterManager.find_nearest(r['lat'], r['lon'], r['people_at_risk'])
            print(f"   🚨 {r['name']}: Evacuate {r['people_at_risk']} people to {len(plan)} shelter(s).")
    
    # 5. Save to DB
    print("5️⃣  Saving to Database...")
    Database.save(results)
    
    # 6. Generate Visuals
    print("6️⃣  Generating Map & Charts...")
    map_path = Visualizer.create_map(results)
    chart_path = Visualizer.create_chart(results)
    
    print("\n" + "="*60)
    print("✅ PROTOTYPE RUN COMPLETE!".center(60))
    print("="*60)
    print(f"📁 Map saved at: {map_path}")
    print(f"📊 Chart saved at: {chart_path}")
    print("\n🌐 Opening Map in Browser...")
    
    # Open the map automatically
    webbrowser.open(map_path)

if __name__ == "__main__":
    run_prototype()