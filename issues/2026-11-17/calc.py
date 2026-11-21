# calc.py for Issue 07 · Kinetic energy of wind
import json

m_kg = 1
v_breeze = 5
v_strong = 15
v_storm = 25

ek_breeze = 0.5 * m_kg * (v_breeze ** 2)
ek_strong = 0.5 * m_kg * (v_strong ** 2)
ek_storm = 0.5 * m_kg * (v_storm ** 2)

out = {
    "m_kg": m_kg,
    "v_breeze": v_breeze,
    "v_strong": v_strong,
    "v_storm": v_storm,
    "ek_breeze": ek_breeze,
    "ek_strong": ek_strong,
    "ek_storm": ek_storm
}
print(json.dumps(out))
