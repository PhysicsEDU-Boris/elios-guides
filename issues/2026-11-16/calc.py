# calc.py for issue 2026-11-16 (River water flow discharge Q = v * A)
import json

A_m2 = 12.0  # cross-sectional area in square meters (12 from source date 12 Nov)
v_ms = 4.0   # flow velocity in meters per second (4 from 4 min read)
Q_m3s = A_m2 * v_ms  # volumetric flow rate Q = A * v (48.0)

A_1 = 3.0
v_1 = 2.0
Q_1 = A_1 * v_1

A_3 = Q_m3s
v_3 = A_m2
Q_3 = A_3 * v_3

out = {
    "A_m2": A_m2,
    "v_ms": v_ms,
    "Q_m3s": Q_m3s,
    "stat_1": Q_m3s,
    "stat_2": v_ms,
    "stat_3": A_m2,
    "table_r1c2": A_1,
    "table_r1c3": Q_1,
    "table_r2c2": A_m2,
    "table_r2c3": Q_m3s,
    "table_r3c2": A_3,
    "table_r3c3": Q_3,
    "example_result": Q_m3s,
    "graph_1": Q_1,
    "graph_2": Q_m3s,
    "graph_3": Q_3
}

print(json.dumps(out))
