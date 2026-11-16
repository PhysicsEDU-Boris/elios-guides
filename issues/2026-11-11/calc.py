import json

volume_m3 = 100
mass_clean = 1
mass_hazy = 5
mass_smog = 15

c_clean = (mass_clean * 1000) / volume_m3
c_hazy = (mass_hazy * 1000) / volume_m3
c_smog = (mass_smog * 1000) / volume_m3

out = {
    "volume_m3": volume_m3,
    "mass_clean": mass_clean,
    "mass_hazy": mass_hazy,
    "mass_smog": mass_smog,
    "c_clean": c_clean,
    "c_hazy": c_hazy,
    "c_smog": c_smog,
    "read_min": 12,
    "grade_start": 7,
    "grade_end": 9,
    "xp_total": 60,
    "issue_num": 6,
    "day": 11,
    "year": 2026,
    "particle_size": 2.5,
}
print(json.dumps(out))
