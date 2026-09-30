class RiskEngine:
    @staticmethod
    def calculate(village, weather, cloudburst=None, glof=None):
        cloudburst = cloudburst or {"score": 0, "level": "NORMAL"}
        glof = glof or {"applicable": False, "score": 0, "risk_level": "NONE"}

        # 1. Rain Score
        rain_score = min(weather["rain"] * 1.2, 100)

        # 2. Slope Score (estimated from elevation)
        elev = village["elev"]
        slope = 38 if elev >= 3500 else 34 if elev >= 3000 else 28 if elev >= 2000 else 22
        slope_score = min((slope / 45) * 100, 100)

        # 3. Soil Score
        soil_score = weather["soil"]

        # 4. Elevation Score (normalized 0-100, replaces old flat bonus)
        elev_score = min((elev / 4000) * 100, 100)

        # 5. Cloudburst Score
        cloud_score = cloudburst.get("score", 0)

        # 6. GLOF Score
        glof_score = glof.get("score", 0) if glof.get("applicable") else 0

        # Weighted composite — GLOF weight only counted if applicable to this village
        weights = {"rain": 0.30, "slope": 0.15, "soil": 0.15, "elev": 0.10, "cloud": 0.20}
        if glof.get("applicable"):
            weights["glof"] = 0.10

        scores = {"rain": rain_score, "slope": slope_score, "soil": soil_score,
                  "elev": elev_score, "cloud": cloud_score, "glof": glof_score}

        total_weight = sum(weights.values())
        total = sum(scores[k] * w for k, w in weights.items()) / total_weight
        total = round(min(total, 100), 1)

        # Multi-hazard override — an imminent cloudburst or critical GLOF
        # forces at least CRITICAL level, even if other factors are moderate
        force_critical = (cloudburst.get("level") == "CLOUDBURST_IMMINENT") or \
                          (glof.get("risk_level") == "CRITICAL")
        if force_critical:
            total = max(total, 85)

        # Determine Level
        if total >= 75: level, color, icon, risk_pct = "CRITICAL", "red", "🔴", 0.40
        elif total >= 50: level, color, icon, risk_pct = "WARNING", "orange", "🟠", 0.20
        elif total >= 30: level, color, icon, risk_pct = "WATCH", "gold", "🟡", 0.10
        else: level, color, icon, risk_pct = "SAFE", "green", "🟢", 0.0

        return {
            **village,
            "weather": weather,
            "cloudburst": cloudburst,
            "glof": glof,
            "risk_score": total,
            "risk_level": level,
            "color": color,
            "icon": icon,
            "people_at_risk": int(village["pop"] * risk_pct),
            "breakdown": {
                "rainfall": round(rain_score, 1),
                "slope": round(slope_score, 1),
                "soil": round(soil_score, 1),
                "elevation": round(elev_score, 1),
                "cloudburst": round(cloud_score, 1),
                "glof": round(glof_score, 1)
            }
        }