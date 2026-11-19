# calc.py for Issue 09: Coastal ocean waves and speed
import json

f_hz = 1 / 5
lam_m = 30 // 2
v_ms = f_hz * lam_m
chop_f = 0.5
chop_lam = 4
tsunami_f = 0.002
tsunami_lam = 100000
news_day = 18

out = {
    "f_hz": f_hz,
    "lam_m": lam_m,
    "v_ms": round(v_ms, 2),
    "chop_f": chop_f,
    "chop_lam": chop_lam,
    "tsunami_f": tsunami_f,
    "tsunami_lam": tsunami_lam,
    "news_day": news_day,
    "swell_v": round(f_hz * lam_m, 2),
    "chop_v": round(0.5 * 4, 2),
    "tsunami_v": round(0.002 * 100000, 2)
}
print(json.dumps(out))
