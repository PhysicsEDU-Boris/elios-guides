import json

rho = 1000  # kg/m^3, water density
g = 9.8  # m/s^2, gravity
depths = {"drain": 0.03, "rain": 0.12, "flood": 0.50}
out = {"rho": rho, "g": g}
for name, h in depths.items():
    out[f"h_{name}"] = h
    out[f"p_{name}"] = round(rho * g * h, 1)
print(json.dumps(out))
