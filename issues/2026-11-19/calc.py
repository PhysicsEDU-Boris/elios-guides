import json

s_m = 1200
t_s = 40
v_ms = s_m / t_s

out = {
    "s_m": s_m,
    "t_s": t_s,
    "v_ms": v_ms,
    "v_kmh": round(v_ms * 3.6, 1)
}
print(json.dumps(out))
