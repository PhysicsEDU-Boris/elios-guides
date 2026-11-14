# calc.py for ELIOS Guide 2026-11-14
import json

m_kg = 14  # Mass in kg
V_m3 = 7   # Volume in cubic metres
rho = m_kg / V_m3  # Density = Mass / Volume

out = {
    "m_kg": m_kg,
    "V_m3": V_m3,
    "rho": rho,
    "c_water_m": 10,
    "c_water_V": 5,
    "c_water_rho": 2,
    "c_air_m": 14,
    "c_air_V": 7,
    "c_air_rho": 2,
    "c_dense_m": 20,
    "c_dense_V": 5,
    "c_dense_rho": 4
}
print(json.dumps(out))
