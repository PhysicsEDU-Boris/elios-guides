# Example calc.py for schema/example.en.json. Standard library only, no network, no files.
import json

m_kg = 1
dT_example = 5
c = {"water": 4200, "concrete": 880, "asphalt": 920}  # J/kg·°C
Q_J = m_kg * c["water"] * dT_example
out = {"m_kg": m_kg, "dT_example": dT_example, "Q_J": Q_J}
for name, cv in c.items():
    out[f"c_{name}"] = cv
    out[f"dT_{name}"] = round(Q_J / (m_kg * cv), 2)  # ΔT = Q ÷ (m × c)
print(json.dumps(out))
