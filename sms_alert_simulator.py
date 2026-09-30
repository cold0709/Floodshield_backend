from datetime import datetime

# In-memory log of "sent" messages — resets on server restart.
# For persistence across restarts, could write to a JSON file or DB table.
CARRIER_SIM_LOG = []

SMS_TEMPLATES = {
    "CRITICAL": (
        "🚨 FLOOD ALERT - {village}\n"
        "Risk Level: CRITICAL ({score}/100)\n"
        "{hazard_note}"
        "IMMEDIATE EVACUATION ADVISED.\n"
        "Move to nearest shelter: {shelter}\n"
        "Est. people at risk: {people}\n"
        "- District Disaster Management Authority"
    ),
    "WARNING": (
        "⚠️ Flood Warning - {village}\n"
        "Risk Level: WARNING ({score}/100)\n"
        "{hazard_note}"
        "Stay alert, prepare to evacuate if instructed.\n"
        "- District Disaster Management Authority"
    ),
}


def build_hazard_note(village_result):
    notes = []
    cb = village_result.get("cloudburst", {})
    if cb.get("level") in ("SEVERE_WARNING", "CLOUDBURST_IMMINENT"):
        notes.append(f"Cloudburst risk: {cb['level'].replace('_', ' ')}. ")

    glof = village_result.get("glof", {})
    if glof.get("applicable") and glof.get("risk_level") in ("HIGH", "CRITICAL"):
        notes.append(f"GLOF risk near {glof.get('lake_name')}: {glof['risk_level']}. ")

    return "".join(notes)


def generate_sms_for_village(village_result, nearest_shelter="nearest designated shelter"):
    level = village_result["risk_level"]
    if level not in SMS_TEMPLATES:
        return None

    template = SMS_TEMPLATES[level]
    message = template.format(
        village=village_result["name"],
        score=village_result["risk_score"],
        hazard_note=build_hazard_note(village_result),
        shelter=nearest_shelter,
        people=village_result.get("people_at_risk", 0)
    )

    return {
        "village": village_result["name"],
        "risk_level": level,
        "message": message,
        "recipients_simulated": max(village_result.get("people_at_risk", 0) // 5, 1),
        "timestamp": datetime.now().isoformat(),
        "status": "SIMULATED_SENT",
        "provider": "Twilio (Simulated — no real SMS sent, no credits used)"
    }


def simulate_sms_blast(results, shelter_lookup=None):
    """
    results: list of village risk dicts (from RiskEngine)
    shelter_lookup: optional dict {village_name: nearest_shelter_name}
    """
    blast = []
    for r in results:
        shelter = shelter_lookup.get(r["name"]) if shelter_lookup else None
        sms = generate_sms_for_village(r, shelter or "nearest designated shelter")
        if sms:
            blast.append(sms)
            CARRIER_SIM_LOG.append(sms)
    return blast


def get_sms_log(limit=50):
    return CARRIER_SIM_LOG[-limit:][::-1]  # most recent first