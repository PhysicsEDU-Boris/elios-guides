# calc.py for issue 2026-11-10 (Jakarta PM2.5). Standard library only.
import json

rho_air = 1.2          # kg/m³, clean air near sea level (textbook value)
pm25 = 48              # µg/m³, Jakarta 07:00 WIB, 10 Nov 2026 (ANTARA [1])
who_multiple = 9.2     # times the WHO annual guideline (ANTARA [1])
rooms = {"bedroom": 30, "classroom": 150, "hall": 600}  # m³, example volumes

out = {"rho_air": rho_air, "pm25": pm25, "who_multiple": who_multiple}
out["who_guideline"] = round(pm25 / who_multiple, 2)                 # µg/m³
out["air_mass_classroom_kg"] = round(rho_air * rooms["classroom"], 1)  # m = ρ × V
for name, v in rooms.items():
    out[f"V_{name}"] = v
    out[f"pm_mg_{name}"] = round(pm25 * v / 1000, 2)                 # µg → mg
out["pm_ug_classroom"] = pm25 * rooms["classroom"]
out["who_mg_classroom"] = round(out["who_guideline"] * rooms["classroom"] / 1000, 2)
print(json.dumps(out))
