import json

V_m3 = 500 * 2
masses = {"sea_level": 600 + 600, "warm_air": 500 * 2, "polluted_air": 650 * 2}
out = {"V_m3": V_m3}
for name, m in masses.items():
    out[f"m_{name}"] = m
    out[f"rho_{name}"] = round(m / V_m3, 2)
print(json.dumps(out))
