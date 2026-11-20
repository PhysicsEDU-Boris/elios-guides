import json

V_m3 = 50
m_clean = 0.060
m_light = 0.075
m_heavy = 0.135
m_soot = 0.015

dens_clean = round(m_clean / V_m3, 4)
dens_light = round(m_light / V_m3, 4)
dens_heavy = round(m_heavy / V_m3, 4)
dens_soot = round(m_soot / V_m3, 4)

out = {
    "V_m3": V_m3,
    "m_clean": m_clean,
    "m_light": m_light,
    "m_heavy": m_heavy,
    "dens_clean": dens_clean,
    "dens_light": dens_light,
    "dens_heavy": dens_heavy,
    "dens_soot": dens_soot
}
print(json.dumps(out))
