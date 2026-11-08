# calc.py for ELIOS Guide #01: Utah Goosenecks & River Flow
import json

s_m = 120  # distance in meters
t_s = 20   # time in seconds
v_mps = s_m / t_s  # speed m/s

streams = {
    "Goosenecks": v_mps,
    "Rapid": round(v_mps * 1.5, 1),
    "Creek": round(v_mps * 0.8, 1)
}

out = {
    "s_m": s_m,
    "t_s": t_s,
    "v_mps": v_mps
}

for name, val in streams.items():
    out[f"v_{name.lower()}"] = val

print(json.dumps(out))
