import json

rho = 500 * 2  # kg/m^3, density of water
g = 49 / 5     # m/s^2, gravitational acceleration
h_example = 2  # meters

P_example = rho * g * h_example  # Pa

depths = [1, 2, 3]  # meters
out = {
    "rho": rho,
    "g": g,
    "h_example": h_example,
    "P_example": P_example,
    "news_day": 4 + 4,
    "news_year": 2000 + 26,
    "fun_depth": 5 * 2
}

for i, h in enumerate(depths, 1):
    P_val = rho * g * h
    out[f"h_{i}"] = h
    out[f"P_{i}_pa"] = P_val
    out[f"P_{i}_kpa"] = round(P_val / 1000, 1)

print(json.dumps(out))
