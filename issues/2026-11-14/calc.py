import json

force_N = 30
area_m2 = 5
pressure_Pa = force_N / area_m2

surfaces = {
    "surface_a": 5,
    "surface_b": 1,
    "surface_c": 6
}

out = {
    "force_N": force_N,
    "area_m2": area_m2,
    "pressure_Pa": round(pressure_Pa, 2)
}

for name, a in surfaces.items():
    out[f"area_{name}"] = a
    out[f"pressure_{name}"] = round(force_N / a, 2)

print(json.dumps(out))
