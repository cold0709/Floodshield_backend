from math import radians, sin, cos, sqrt, atan2
from shelters import ShelterManager


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def estimate_evacuation_time(population, distance_km, vehicles=5,
                               vehicle_capacity=40, vehicle_speed_kmh=20,
                               walking_speed_kmh=4):
    if population <= 0:
        return 0
    vehicle_time = float('inf')
    if vehicles > 0:
        trips_needed = max(population / (vehicles * vehicle_capacity), 1)
        vehicle_time = trips_needed * ((distance_km / vehicle_speed_kmh) * 2)
    walking_time = distance_km / walking_speed_kmh
    return round(min(vehicle_time, walking_time), 2)


def prioritize_population(village):
    pop = village["pop"]
    hospital = village.get("hospital_patients", 0)
    disabled = int(pop * village.get("disabled_pct", 0.02))
    elderly = int(pop * village.get("elderly_pct", 0.10))
    children = int(pop * village.get("children_pct", 0.15))
    general = max(pop - disabled - elderly - children - hospital, 0)

    groups = [
        {"group": "Hospital Patients", "priority": 1, "count": hospital},
        {"group": "Disabled", "priority": 1, "count": disabled},
        {"group": "Elderly (65+)", "priority": 2, "count": elderly},
        {"group": "Children (0-10)", "priority": 2, "count": children},
        {"group": "General Population", "priority": 3, "count": general},
    ]
    return sorted(groups, key=lambda x: x["priority"])


def generate_evacuation_plan(village, risk_score, people_at_risk=None):
    """
    Builds a full evacuation plan: shelter allocation + time estimates + priority groups.
    """
    shelters = ShelterManager.get_shelters()
    target_population = people_at_risk if people_at_risk is not None else village["pop"]

    for s in shelters:
        s['dist'] = haversine(village["lat"], village["lon"], s["lat"], s["lon"])
    shelters.sort(key=lambda s: s['dist'])

    plan = []
    remaining = target_population
    for s in shelters:
        if remaining <= 0:
            break
        allocated = min(remaining, s["cap"])
        plan.append({
            "shelter_name": s["name"],
            "distance_km": round(s["dist"], 2),
            "allocated_population": allocated,
            "estimated_time_hours": estimate_evacuation_time(allocated, s["dist"]),
            "alert_priority": "IMMEDIATE" if risk_score >= 75 else
                               "URGENT" if risk_score >= 50 else "STANDBY"
        })
        remaining -= allocated

    warning = None
    if remaining > 0:
        warning = f"⚠️ {remaining} people unaccommodated — additional shelters/resources needed"

    return {
        "village": village["name"],
        "total_to_evacuate": target_population,
        "priority_groups": prioritize_population(village),
        "shelter_allocation": plan,
        "warning": warning
    }