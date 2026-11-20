import json

Ein_J = 1000
appliances = {
    "LED lamp": 800,
    "Electric fan": 500,
    "Incandescent bulb": 50
}
out = {"Ein_J": Ein_J}
for name, Eout in appliances.items():
    out[f"Eout_{name}"] = Eout
    out[f"eta_{name}"] = round((Eout / Ein_J) * 100, 1)
print(json.dumps(out))
