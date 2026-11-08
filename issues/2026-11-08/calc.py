import json

m_kg = 1000
g = 9.81
h_example = 10
Ep_J = m_kg * g * h_example

heights = [5, 10, 20]
out = {
    "m_kg": m_kg,
    "g": g,
    "h_example": h_example,
    "Ep_J": Ep_J,
    "Ep_kJ": round(Ep_J / 1000, 2)
}

for i, h in enumerate(heights, 1):
    ep = m_kg * g * h
    out[f"h_{i}"] = h
    out[f"Ep_{i}_J"] = ep
    out[f"Ep_{i}_kJ"] = round(ep / 1000, 2)

out["_graph.1.raw"] = out["Ep_1_kJ"]
out["_graph.2.raw"] = out["Ep_2_kJ"]
out["_graph.3.raw"] = out["Ep_3_kJ"]

print(json.dumps(out))
