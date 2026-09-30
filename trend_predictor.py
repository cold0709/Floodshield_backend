import numpy as np
from datetime import datetime
from database import Database


def predict_risk_trend(village_name, lookback=20):
    """
    Simple linear regression on recent risk_score history to estimate
    how fast risk is rising/falling (per hour), and forecast next few hours.
    """
    history = Database.get_trend_summary(village_name)

    if len(history) < 3:
        return {
            "status": "insufficient_data",
            "message": "Need at least 3 historical readings to predict a trend. "
                       "Keep the server running to accumulate more data.",
            "data_points": len(history)
        }

    recent = history[-lookback:]
    scores = np.array([h["risk_score"] for h in recent], dtype=float)

    times = [datetime.fromisoformat(h["timestamp"]) for h in recent]
    t0 = times[0]
    hours = np.array([(t - t0).total_seconds() / 3600 for t in times])

    if np.all(hours == hours[0]):
        return {
            "status": "insufficient_time_spread",
            "message": "All data points occurred at nearly the same time — need readings spread over time."
        }

    # Least-squares linear fit: risk_score = slope * hours + intercept
    slope, intercept = np.polyfit(hours, scores, 1)

    current_score = scores[-1]
    next_1hr = slope * (hours[-1] + 1) + intercept
    next_3hr = slope * (hours[-1] + 3) + intercept
    next_6hr = slope * (hours[-1] + 6) + intercept

    trend_direction = "RISING" if slope > 0.5 else "FALLING" if slope < -0.5 else "STABLE"

    return {
        "status": "ok",
        "village": village_name,
        "data_points_used": len(recent),
        "current_risk_score": round(current_score, 1),
        "trend_direction": trend_direction,
        "rate_per_hour": round(slope, 2),
        "forecast": {
            "next_1hr": round(min(max(next_1hr, 0), 100), 1),
            "next_3hr": round(min(max(next_3hr, 0), 100), 1),
            "next_6hr": round(min(max(next_6hr, 0), 100), 1),
        },
        "confidence_note": "Based on linear regression over recent historical readings. "
                           "Accuracy improves as more data accumulates."
    }