# calc.py for ELIOS Guide 11: Offshore wind power
import json

# Power calculations for wind turbines: P = W / t
# W in joules (J), t in seconds (s), P in watts (W)
turbines = [
    {"name": "Turbine A", "W": 1500000, "t": 10},
    {"name": "Turbine B", "W": 3000000, "t": 15},
    {"name": "Turbine C", "W": 800000, "t": 5}
]

out = {}
for i, turb in enumerate(turbines, 1):
    P_W = turb["W"] / turb["t"]
    P_kW = P_W / 1000
    out[f"turbine_{i}_W"] = turb["W"]
    out[f"turbine_{i}_t"] = turb["t"]
    out[f"turbine_{i}_P_W"] = P_W
    out[f"turbine_{i}_P_kW"] = P_kW

print(json.dumps(out))
