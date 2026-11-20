import json

m_kg = 1000
V_m3 = 2
rho = m_kg / V_m3

out = {
    "m_kg": m_kg,
    "V_m3": V_m3,
    "rho": rho,
    "r1_m": 1000, "r1_V": 2, "r1_rho": 500,
    "r2_m": 850, "r2_V": 2, "r2_rho": 425,
    "r3_m": 500, "r3_V": 2, "r3_rho": 250
}
print(json.dumps(out))
