import json

volume_m3 = 3
mass_clean_ug = 45
mass_moderate_ug = 165
mass_unhealthy_ug = 450

conc_clean = round(mass_clean_ug / volume_m3, 1)
conc_moderate = round(mass_moderate_ug / volume_m3, 1)
conc_unhealthy = round(mass_unhealthy_ug / volume_m3, 1)

life_loss_months = 8
news_day = 12
air_inhaled_kg = 14
water_drunk_kg = 2
food_eaten_kg = 1.5

out = {
    "volume_m3": volume_m3,
    "mass_clean_ug": mass_clean_ug,
    "mass_moderate_ug": mass_moderate_ug,
    "mass_unhealthy_ug": mass_unhealthy_ug,
    "conc_clean": conc_clean,
    "conc_moderate": conc_moderate,
    "conc_unhealthy": conc_unhealthy,
    "example_mass": mass_unhealthy_ug,
    "example_volume": volume_m3,
    "example_result": conc_unhealthy,
    "life_loss_months": life_loss_months,
    "news_day": news_day,
    "air_inhaled_kg": air_inhaled_kg,
    "water_drunk_kg": water_drunk_kg,
    "food_eaten_kg": food_eaten_kg
}
print(json.dumps(out))
