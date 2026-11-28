import json

rho = 1000  # kg/m³
g = 9.8  # m/s²
depths = [1.0, 1.5, 2.0]
results = {}
for i, h in enumerate(depths, 1):
    p = rho * g * h
    results[f"depth_{i}_m"] = h
    results[f"pressure_{i}_Pa"] = p

results["rho"] = rho
results["g"] = g
print(json.dumps(results))
