# Calculation script for ELIOS Guide 11 (Stefan-Boltzmann law)
import json

sigma = 5.67e-8  # W/m²·K⁴
A = 1  # m²
temps = [300, 310, 320]  # K
out = {"sigma": sigma, "A": A}

for i, T in enumerate(temps, start=1):
    P = sigma * A * (T ** 4)
    out[f"T_{i}"] = T
    out[f"P_{i}"] = round(P, 1)

out["example_T"] = 300
out["example_P"] = round(sigma * A * (300 ** 4), 1)

print(json.dumps(out))
