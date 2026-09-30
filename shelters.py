import csv
import os
import math
from config import SHELTERS_CSV

class ShelterManager:
    @staticmethod
    def get_shelters():
        if not os.path.exists(SHELTERS_CSV):
            # Create dummy shelters if file missing
            with open(SHELTERS_CSV, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["name", "lat", "lon", "capacity"])
                writer.writerow(["Govt School Chamoli", 30.418, 79.335, 500])
                writer.writerow(["Army Base Joshimath", 30.560, 79.570, 1500])
                writer.writerow(["Relief Camp Rudraprayag", 30.285, 78.983, 2000])
        
        shelters = []
        with open(SHELTERS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                shelters.append({"name": row["name"], "lat": float(row["lat"]), "lon": float(row["lon"]), "cap": int(row["capacity"])})
        return shelters

    @staticmethod
    def find_nearest(lat, lon, people_needed):
        shelters = ShelterManager.get_shelters()
        # Calculate distance
        for s in shelters:
            s['dist'] = math.sqrt((lat - s['lat'])**2 + (lon - s['lon'])**2) * 111 # Rough km
        
        shelters.sort(key=lambda x: x['dist'])
        
        plan = []
        remaining = people_needed
        for s in shelters:
            if remaining <= 0: break
            allocate = min(remaining, s['cap'])
            plan.append({"shelter": s['name'], "people": allocate, "dist_km": round(s['dist'], 2)})
            remaining -= allocate
            
        return plan