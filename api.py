import os
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from config import VILLAGES, OUTPUT_DIR
from weather import WeatherFetcher
from risk_engine import RiskEngine
from database import Database
from visuals import Visualizer
from shelters import ShelterManager
from cloudburst_detector import get_cloudburst_risk, get_hourly_forecast
from glof_risk import get_glof_risk, get_seismic_activity
from population_manager import generate_evacuation_plan
from sms_alert_simulator import simulate_sms_blast, get_sms_log
from report_generator import generate_district_report
from trend_predictor import predict_risk_trend
from rate_limiter import RateLimitMiddleware

# ==========================================
# APP INITIALIZATION
# ==========================================
app = FastAPI(title="FloodShield Backend API", version="2.1.0")

# ==========================================
# MIDDLEWARE
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)


# ==========================================
# GLOBAL EXCEPTION HANDLER
# ==========================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"🔥 Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error. Check backend logs.",
            "path": str(request.url.path)
        }
    )


# ==========================================
# CACHE — avoids hammering external APIs on every request
# ==========================================
CACHE = {"data": None, "timestamp": 0}
CACHE_TTL = 300  # 5 minutes


def compute_all_risks(force=False):
    now = time.time()
    if not force and CACHE["data"] and (now - CACHE["timestamp"] < CACHE_TTL):
        return CACHE["data"]

    results = []
    for v in VILLAGES:
        weather = WeatherFetcher.get_data(v['lat'], v['lon'], v['name'])
        cloudburst = get_cloudburst_risk(v['lat'], v['lon'])
        glof = get_glof_risk(v)
        risk = RiskEngine.calculate(v, weather, cloudburst, glof)
        results.append(risk)

    try:
        Database.init()
        Database.save(results)
    except Exception as e:
        print(f"⚠️ Database save skipped: {e}")

    CACHE["data"] = results
    CACHE["timestamp"] = now
    return results


def find_village_result(results, village_name):
    return next((r for r in results if r["name"].lower() == village_name.lower()), None)


def find_village_config(village_name):
    return next((v for v in VILLAGES if v["name"].lower() == village_name.lower()), None)


# ==========================================
# ROOT
# ==========================================
@app.get("/")
def root():
    return {"status": "online", "message": "FloodShield Backend v2.1 (Multi-Hazard) is running!"}


# ==========================================
# CORE: Risk Data
# ==========================================
@app.get("/api/get-risk-data")
def get_risk_data():
    results = compute_all_risks()
    return {"status": "success", "data": results}


# ==========================================
# Per-village hazard breakdown
# ==========================================
@app.get("/api/hazard-breakdown/{village_name}")
def hazard_breakdown(village_name: str):
    results = compute_all_risks()
    village = find_village_result(results, village_name)
    if not village:
        return {"status": "error", "message": "Village not found"}
    return {
        "status": "success",
        "village": village["name"],
        "risk_score": village["risk_score"],
        "risk_level": village["risk_level"],
        "breakdown": village["breakdown"],
        "cloudburst": village["cloudburst"],
        "glof": village["glof"]
    }


# ==========================================
# Cloudburst monitor (all villages)
# ==========================================
@app.get("/api/cloudburst-monitor")
def cloudburst_monitor():
    results = compute_all_risks()
    alerts = [
        {
            "village": r["name"],
            "level": r["cloudburst"]["level"],
            "current_rate_mm_hr": r["cloudburst"]["current_rate_mm_hr"],
            "max_forecast_6hr_mm_hr": r["cloudburst"]["max_forecast_6hr_mm_hr"]
        }
        for r in results if r["cloudburst"]["level"] != "NORMAL"
    ]
    return {"status": "success", "active_alerts": len(alerts), "alerts": alerts}


# ==========================================
# GLOF risk for a village
# ==========================================
@app.get("/api/glof-risk/{village_name}")
def glof_risk_endpoint(village_name: str):
    results = compute_all_risks()
    village = find_village_result(results, village_name)
    if not village:
        return {"status": "error", "message": "Village not found"}
    return {"status": "success", "village": village["name"], "glof": village["glof"]}


# ==========================================
# Seismic activity near glacial-lake villages
# ==========================================
@app.get("/api/seismic-activity")
def seismic_activity():
    activity = []
    for v in VILLAGES:
        if v.get("glacial_lake"):
            seismic = get_seismic_activity(v["lat"], v["lon"])
            activity.append({"village": v["name"], "glacial_lake": v["glacial_lake"]["name"], **seismic})
    return {"status": "success", "data": activity}


# ==========================================
# Evacuation plan for a village
# ==========================================
@app.get("/api/evacuation-plan/{village_name}")
def evacuation_plan(village_name: str, scope: str = "at_risk"):
    results = compute_all_risks()
    village_risk = find_village_result(results, village_name)
    village_config = find_village_config(village_name)
    if not village_risk or not village_config:
        return {"status": "error", "message": "Village not found"}

    # scope=full plans for the whole village.
    # scope=at_risk plans only for people_at_risk (can be 0 when risk is low).
    people = None if scope == "full" else village_risk["people_at_risk"]
    plan = generate_evacuation_plan(village_config, village_risk["risk_score"], people)
    plan["scope"] = "full" if scope == "full" else "at_risk"
    plan["risk_score"] = village_risk["risk_score"]
    plan["risk_level"] = village_risk["risk_level"]
    return {"status": "success", "plan": plan}


# ==========================================
# Shelters list
# ==========================================
@app.get("/api/shelters")
def shelters_list():
    return {"status": "success", "data": ShelterManager.get_shelters()}


# ==========================================
# 24hr risk forecast trend (for line charts)
# ==========================================
@app.get("/api/forecast/{village_name}")
def forecast(village_name: str):
    village = find_village_config(village_name)
    if not village:
        return {"status": "error", "message": "Village not found"}
    trend = get_hourly_forecast(village["lat"], village["lon"])
    return {"status": "success", "village": village["name"], "forecast": trend}


# ==========================================
# Historical data for a village (raw DB records)
# ==========================================
@app.get("/api/history/{village_name}")
def village_history(village_name: str, limit: int = 50):
    data = Database.get_history(village_name, limit)
    return {"status": "success", "village": village_name, "count": len(data), "history": data}


# ==========================================
# Risk trend summary (simplified — for charting)
# ==========================================
@app.get("/api/trend/{village_name}")
def trend_summary(village_name: str):
    data = Database.get_trend_summary(village_name)
    return {"status": "success", "village": village_name, "trend": data}


# ==========================================
# Alert log (all recent critical/warning events, any village)
# ==========================================
@app.get("/api/alert-log")
def alert_log(limit: int = 20):
    data = Database.get_latest_critical_events(limit)
    return {"status": "success", "count": len(data), "alerts": data}


# ==========================================
# SMS Alert Simulation
# ==========================================
@app.get("/api/sms-alerts")
def sms_alerts():
    results = compute_all_risks()
    shelter_lookup = {}
    for r in results:
        village_config = find_village_config(r["name"])
        if village_config:
            plan = generate_evacuation_plan(village_config, r["risk_score"], r["people_at_risk"])
            if plan["shelter_allocation"]:
                shelter_lookup[r["name"]] = plan["shelter_allocation"][0]["shelter_name"]

    blast = simulate_sms_blast(results, shelter_lookup)
    return {"status": "success", "sms_sent": len(blast), "messages": blast}


@app.get("/api/sms-log")
def sms_log(limit: int = 50):
    return {"status": "success", "log": get_sms_log(limit)}


# ==========================================
# PDF Report Export
# ==========================================
@app.get("/api/report/download")
def download_report():
    results = compute_all_risks()
    filepath = generate_district_report(results)
    return FileResponse(filepath, media_type="application/pdf", filename=os.path.basename(filepath))


# ==========================================
# ML Trend Prediction
# ==========================================
@app.get("/api/predict-trend/{village_name}")
def predict_trend_endpoint(village_name: str):
    return predict_risk_trend(village_name)


# ==========================================
# Map (regenerates from live cached data each time)
# ==========================================
@app.get("/api/map")
def get_map():
    results = compute_all_risks()
    map_path = os.path.join(OUTPUT_DIR, "map.html")
    Visualizer.create_map(results)
    return HTMLResponse(content=open(map_path, "r", encoding="utf-8").read())


# ==========================================
# Chart (regenerates from live cached data each time)
# ==========================================
@app.get("/api/chart")
def get_chart():
    results = compute_all_risks()
    chart_path = os.path.join(OUTPUT_DIR, "chart.png")
    Visualizer.create_chart(results)
    return FileResponse(chart_path, media_type="image/png")


# ==========================================
# Live WebSocket alerts (push every 60s)
# ==========================================
@app.websocket("/ws/live-alerts")
async def live_alerts(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            results = compute_all_risks()
            critical = [
                r for r in results
                if r["risk_level"] in ("CRITICAL", "WARNING")
                or r["cloudburst"]["level"] in ("CLOUDBURST_IMMINENT", "SEVERE_WARNING")
                or r["glof"]["risk_level"] in ("CRITICAL", "HIGH")
            ]
            await websocket.send_json({
                "timestamp": time.time(),
                "active_alerts": len(critical),
                "alerts": [
                    {
                        "village": r["name"],
                        "risk_level": r["risk_level"],
                        "cloudburst": r["cloudburst"]["level"],
                        "glof": r["glof"]["risk_level"]
                    } for r in critical
                ]
            })
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        print("Client disconnected from live-alerts")