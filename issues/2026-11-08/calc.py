import json

rho = 1000  # kg/m^3
g = 9.81    # m/s^2
h_example = 0.5  # m
P_example = rho * g * h_example

depths = {"shallow": 0.2, "doorstep": 0.5, "knee": 0.7}
out = {
    "rho": rho,
    "g": g,
    "h_example": h_example,
    "example_result": P_example
}
for name, h in depths.items():
    out[f"h_{name}"] = h
    out[f"P_{name}"] = round(rho * g * h, 1)

print(json.dumps(out))
