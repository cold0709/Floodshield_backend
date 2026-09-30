import os

# Auto-detect project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Folders
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, 'floodshield.db')
SHELTERS_CSV = os.path.join(DATA_DIR, 'shelters.csv')

# Village Database — now includes glacial lake info & population vulnerability data
VILLAGES = [
    {
        "name": "Chamoli", "lat": 30.4167, "lon": 79.3333, "pop": 100000,
        "elev": 1370, "district": "Chamoli",
        "glacial_lake": None,
        "hospital_patients": 50, "elderly_pct": 0.12, "children_pct": 0.18, "disabled_pct": 0.03
    },
    {
        "name": "Joshimath", "lat": 30.5562, "lon": 79.5644, "pop": 22000,
        "elev": 1890, "district": "Chamoli",
        "glacial_lake": {"name": "Rishiganga Basin (2021 GLOF event site)", "risk_level": "high"},
        "hospital_patients": 30, "elderly_pct": 0.10, "children_pct": 0.15, "disabled_pct": 0.02
    },
    {
        "name": "Badrinath", "lat": 30.7433, "lon": 79.4938, "pop": 12000,
        "elev": 3133, "district": "Chamoli",
        "glacial_lake": {"name": "Alaknanda Glacial Basin", "risk_level": "critical"},
        "hospital_patients": 15, "elderly_pct": 0.08, "children_pct": 0.10, "disabled_pct": 0.02
    },
    {
        "name": "Kedarnath", "lat": 30.7346, "lon": 79.0669, "pop": 8000,
        "elev": 3583, "district": "Rudraprayag",
        "glacial_lake": {"name": "Chorabari Lake (2013 GLOF disaster site)", "risk_level": "critical"},
        "hospital_patients": 10, "elderly_pct": 0.07, "children_pct": 0.08, "disabled_pct": 0.02
    },
    {
        "name": "Gopeshwar", "lat": 30.4000, "lon": 79.3200, "pop": 15000,
        "elev": 1308, "district": "Chamoli",
        "glacial_lake": None,
        "hospital_patients": 20, "elderly_pct": 0.11, "children_pct": 0.16, "disabled_pct": 0.03
    },
]