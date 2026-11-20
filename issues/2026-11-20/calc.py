# calc.py for issue 10: hydrostatic pressure calculation
import json

rho = 1000  # kg/m³
g = 9.8  # m/s²
depths = [1, 5, 10, 20]
out = {"rho": rho, "g": g}
for d in depths:
    p = rho * g * d
    out[f"h_{d}"] = d
    out[f"p_{d}"] = round(p, 1)
print(json.dumps(out))
