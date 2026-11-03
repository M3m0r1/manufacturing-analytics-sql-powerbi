import numpy as np
import pandas as pd
from config import RAW_DIR, SEED

rng = np.random.default_rng(SEED + 4)

units = pd.read_csv(RAW_DIR / "units.csv")
batches = pd.read_csv(RAW_DIR / "batches.csv")
wo = pd.read_csv(RAW_DIR / "work_orders.csv")

# Додаємо дату до кожного виробу
u = units.merge(batches[["batch_id", "work_order_id"]], on="batch_id")
u = u.merge(wo[["work_order_id", "date_id"]], on="work_order_id")

# Які дефекти можливі на кожному етапі
DEFECTS = {1: [3], 2: [1, 2], 3: [4], 4: [5], 6: [5, 8], 7: [8]}

# 1. Інспекції для списаних виробів (крім етапу 5)
scrapped = u[u["scrapped_at_stage_id"].isin(DEFECTS.keys())].copy()
scrapped["stage_id"] = scrapped["scrapped_at_stage_id"].astype(int)
scrapped["defect_type_id"] = [int(rng.choice(DEFECTS[s])) for s in scrapped["stage_id"]]
scrapped["result"] = "Fail"

# 2. Інспекції для придатних виробів з дрібним дефектом (2%)
good = u[u["final_status"] == "Good"]
reworked = good[rng.random(len(good)) < 0.02].copy()
reworked["stage_id"] = rng.choice([2, 4, 7], size=len(reworked))
reworked["defect_type_id"] = [int(rng.choice(DEFECTS[s])) for s in reworked["stage_id"]]
reworked["result"] = "Reworked"

# 3. Об'єднуємо
cols = ["unit_id", "date_id", "stage_id", "defect_type_id", "result"]
insp = pd.concat([scrapped[cols], reworked[cols]], ignore_index=True)
insp = insp.sort_values("unit_id").reset_index(drop=True)
insp.insert(0, "inspection_id", range(1, len(insp) + 1))
insp.to_csv(RAW_DIR / "quality_inspections.csv", index=False)

# Перевірки
assert insp["inspection_id"].is_unique
assert insp["unit_id"].is_unique                      # одна інспекція на виріб
assert (u.loc[u["unit_id"].isin(insp.loc[insp["result"] == "Fail", "unit_id"]), "final_status"] == "Rejected").all()
assert (u.loc[u["unit_id"].isin(insp.loc[insp["result"] == "Reworked", "unit_id"]), "final_status"] == "Good").all()
print("All checks passed")

# Підсумки
print("Inspections:", len(insp))
print(insp["result"].value_counts())
print("\nДефекти по етапах:")
print(insp.groupby(["stage_id", "defect_type_id"]).size())