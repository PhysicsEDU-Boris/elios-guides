import json

m_kg = 1246
V_m3 = 2
rho = m_kg / V_m3
out = {"m_kg": m_kg, "V_m3": V_m3, "rho": round(rho, 2)}
print(json.dumps(out))
