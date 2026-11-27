import json

F_N = 500
A_m2 = 2
p_Pa = F_N / A_m2
out = {"F_N": F_N, "A_m2": A_m2, "p_Pa": p_Pa}
for area in [1, 2, 5]:
    out[f"area_{area}"] = area
    out[f"pressure_{area}"] = round(F_N / area, 2)
print(json.dumps(out))
