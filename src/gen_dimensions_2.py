import numpy as np
import pandas as pd
from config import RAW_DIR, SEED

rng = np.random.default_rng(SEED)

# Типи дефектів
defect_types = pd.DataFrame([
    {"defect_type_id": 1, "defect_name": "Solder Bridge",        "typical_stage_id": 2, "severity": "Major"},
    {"defect_type_id": 2, "defect_name": "Cold Solder Joint",    "typical_stage_id": 2, "severity": "Major"},
    {"defect_type_id": 3, "defect_name": "Missing Component",    "typical_stage_id": 1, "severity": "Critical"},
    {"defect_type_id": 4, "defect_name": "Firmware Flash Error", "typical_stage_id": 3, "severity": "Major"},
    {"defect_type_id": 5, "defect_name": "Housing Misalignment", "typical_stage_id": 4, "severity": "Minor"},
    {"defect_type_id": 6, "defect_name": "Sensor Calibration",   "typical_stage_id": 5, "severity": "Major"},
    {"defect_type_id": 7, "defect_name": "Radio Link Failure",   "typical_stage_id": 5, "severity": "Critical"},
    {"defect_type_id": 8, "defect_name": "Cosmetic Damage",      "typical_stage_id": 7, "severity": "Minor"},
])

# Причини простоїв (is_planned: 1 = плановий)
downtime_reasons = pd.DataFrame([
    {"reason_id": 1, "reason_name": "Component Shortage",     "category": "Material",       "is_planned": 0},
    {"reason_id": 2, "reason_name": "Machine Breakdown",      "category": "Technical",      "is_planned": 0},
    {"reason_id": 3, "reason_name": "Test Fixture Fault",     "category": "Technical",      "is_planned": 0},
    {"reason_id": 4, "reason_name": "Changeover",             "category": "Organizational", "is_planned": 1},
    {"reason_id": 5, "reason_name": "Operator Absence",       "category": "Organizational", "is_planned": 0},
    {"reason_id": 6, "reason_name": "Preventive Maintenance", "category": "Technical",      "is_planned": 1},
])

# Співробітники: 16 вдень, 14 вночі
roles = ["Operator", "Tester", "Inspector"]
rows = []
emp_id = 1
for shift_id, count in [(1, 16), (2, 14)]:
    for _ in range(count):
        rows.append({
            "employee_id": emp_id,
            "full_name": f"Employee {emp_id:03d}",
            "role": rng.choice(roles, p=[0.6, 0.25, 0.15]),
            "shift_id": shift_id,
            "line_id": int(rng.integers(1, 5)),
            "experience_years": round(float(rng.uniform(0.5, 10)), 1),
        })
        emp_id += 1
employees = pd.DataFrame(rows)

# Зберігаємо
tables = {"defect_types": defect_types, "downtime_reasons": downtime_reasons, "employees": employees}
for name, df in tables.items():
    df.to_csv(RAW_DIR / f"{name}.csv", index=False)
    print(name, len(df))

# Перевірки
assert employees["employee_id"].is_unique
assert set(employees["shift_id"]) == {1, 2}
print("All checks passed")