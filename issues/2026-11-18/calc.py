# Calculation script for Issue 08: Solar panel output (P = eta * A * G)
import json

eta = 2 / 10
A = 4 / 2
G = 250 * 2
P = int(eta * A * G)

eta_2 = 1 / 10
A_2 = 4 / 2
P_2 = int(eta_2 * A_2 * G)

A_3 = 2 / 2
P_3 = int(eta * A_3 * G)

G_g1 = 150 * 2
P_g1 = int(eta * A * G_g1)

G_g2 = 8 * 50
P_g2 = int(eta * A * G_g2)

day = 6 * 2
percent = 2 * 10

out = {
    "eta": eta,
    "A_m2": int(A),
    "G_W_m2": int(G),
    "P": P,
    "P_W": P,
    "eta_2": eta_2,
    "A_2": int(A_2),
    "P_2": P_2,
    "A_3": int(A_3),
    "P_3": P_3,
    "G_g1": int(G_g1),
    "P_g1": P_g1,
    "G_g2": int(G_g2),
    "P_g2": P_g2,
    "day": day,
    "percent": percent
}
print(json.dumps(out))
