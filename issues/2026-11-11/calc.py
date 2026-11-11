# calc.py for ELIOS Guide Issue 01: Jakarta floods and water flow speed (Torricelli's law)
import json

g = 9.81  # m/s^2, acceleration due to gravity
depths = {"h1": 2.0, "h2": 1.0, "h3": 0.5}  # metres
area = 10.0  # m^2, channel cross-sectional area

out = {
    "g": g,
    "area_m2": area,
    "h1": 2.0,
    "h2": 1.0,
    "h3": 0.5,
    "stat_g": 9.81,
    "stat_v2m": round((2 * g * 2.0) ** 0.5, 2),
    "stat_flow_rate": round(round((2 * g * 2.0) ** 0.5, 2) * area, 2),
    "news_day": 10,
    "news_year": 2026,
    "fun_fact_height": 2,
    "fun_fact_speed_over": 6
}

for key, h in depths.items():
    v = round((2 * g * h) ** 0.5, 2)
    out[f"v_{key}_m_s"] = v
    out[f"Q_{key}_m3_s"] = round(v * area, 2)

print(json.dumps(out))
