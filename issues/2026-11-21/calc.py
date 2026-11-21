import json

energy_1_J = 15000000  # 15 MJ
time_s = 10
power_1_W = energy_1_J / time_s  # 1,500,000 W (1.5 MW)

energy_2_J = 50000000  # 50 MJ
power_2_W = energy_2_J / time_s  # 5,000,000 W (5.0 MW)

energy_3_J = 168000000  # 168 MJ
power_3_W = energy_3_J / time_s  # 16,800,000 W (16.8 MW)

out = {
    "energy_J": energy_1_J,
    "time_s": time_s,
    "power_W": power_1_W,
    "power_MW": power_1_W / 1000000,
    "energy_1_MJ": 15,
    "power_1_MW": 1.5,
    "energy_2_MJ": 50,
    "power_2_MW": 5.0,
    "energy_3_MJ": 168,
    "power_3_MW": 16.8
}
print(json.dumps(out))
