# calc.py for issue 04: Jakarta coastal flood and hydrostatic pressure
import json

rho = 1
g = 9

depths = [1, 2, 3]
out = {"rho": rho, "g": g}

for h in depths:
    P_kPa = rho * g * h
    out[f"h_{h}"] = h
    out[f"P_kPa_{h}"] = P_kPa

out["example_h"] = 2
out["example_P_kPa"] = rho * g * 2
out["graph_1"] = rho * g * 1
out["graph_2"] = rho * g * 2
out["graph_3"] = rho * g * 3

print(json.dumps(out))
