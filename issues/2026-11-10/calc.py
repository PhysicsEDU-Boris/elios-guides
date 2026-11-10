# calc.py for ELIOS Guide 2026-11-10 (Jakarta heavy rain and water flow)
import json

area_m2 = 10
velocity_ms = 3
discharge_m3s = area_m2 * velocity_ms

out = {
    "area_m2": area_m2,
    "velocity_ms": velocity_ms,
    "discharge_m3s": discharge_m3s,
    "graph_1_raw": discharge_m3s,
    "graph_2_raw": discharge_m3s * 1.5,
    "graph_3_raw": discharge_m3s * 2.0
}
print(json.dumps(out))
