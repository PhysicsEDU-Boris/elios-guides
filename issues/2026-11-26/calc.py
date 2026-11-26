# Calc.py for Issue 11: Wildlife escape speed during wildfires
import json

s_m = 1200
t_s = 3600
v_pangolin = round(s_m / t_s, 2)

lizard_s = 900
lizard_t = 1800
v_lizard = round(lizard_s / lizard_t, 2)

civet_s = 600
civet_t = 3000
v_civet = round(civet_s / civet_t, 2)

out = {
    "s_m": s_m,
    "t_s": t_s,
    "v_pangolin": v_pangolin,
    "lizard_s": lizard_s,
    "lizard_t": lizard_t,
    "v_lizard": v_lizard,
    "civet_s": civet_s,
    "civet_t": civet_t,
    "v_civet": v_civet
}
print(json.dumps(out))
