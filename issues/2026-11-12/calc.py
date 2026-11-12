import json

A1 = 10  # m² cross-section area
v1 = 2   # m/s water velocity
Q = A1 * v1  # m³/s discharge

A2 = 4   # narrower section 2
v2 = Q / A2

A3 = 5   # section 3
v3 = Q / A3

out = {
    "A1": A1,
    "v1": v1,
    "Q": Q,
    "A2": A2,
    "v2": round(v2, 1),
    "A3": A3,
    "v3": round(v3, 1)
}
print(json.dumps(out))
