import json

m_kg_1 = 1000
m_kg_2 = 2000
m_kg_5 = 5000
g = 9.81
h_m = 300

Ep_1 = m_kg_1 * g * h_m  # Joules
Ep_2 = m_kg_2 * g * h_m
Ep_5 = m_kg_5 * g * h_m

out = {
    "m_kg_1": m_kg_1,
    "m_kg_2": m_kg_2,
    "m_kg_5": m_kg_5,
    "ton_1": 1,
    "ton_2": 2,
    "ton_3": 5,
    "g": g,
    "h_m": h_m,
    "Ep_1_kJ": round(Ep_1 / 1000, 1),
    "Ep_2_kJ": round(Ep_2 / 1000, 1),
    "Ep_5_kJ": round(Ep_5 / 1000, 1),
    "_graph_1": round(Ep_1 / 1000, 1),
    "_graph_2": round(Ep_2 / 1000, 1),
    "_graph_3": round(Ep_5 / 1000, 1)
}
print(json.dumps(out))
