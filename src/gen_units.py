import numpy as np
import pandas as pd
from config import RAW_DIR, SEED

rng = np.random.default_rng(SEED + 1)

batches = pd.read_csv(RAW_DIR / "batches.csv")
wo = pd.read_csv(RAW_DIR / "work_orders.csv")
dim_date = pd.read_csv(RAW_DIR / "dim_date.csv")

# 1. З кожної партії робимо окремі вироби
units = batches.loc[batches.index.repeat(batches["qty_started"])].reset_index(drop=True)

# 2. Додаємо лінію, продукт і місяць
units = units.merge(wo[["work_order_id", "date_id", "line_id", "product_id"]], on="work_order_id")
units = units.merge(dim_date[["date_id", "month"]], on="date_id")
units["month_idx"] = units["month"] - 3          # квітень = 1, ..., вересень = 6
units["unit_id"] = range(1, len(units) + 1)

# 3. Шанс браку на кожному етапі
BASE_P = {1: 0.010, 2: 0.015, 3: 0.006, 4: 0.012, 5: 0.016, 6: 0.007, 7: 0.004}
G1_MULT = {1: 1.0, 2: 1.0, 3: 1.5, 4: 2.0, 5: 2.5, 6: 3.0}   # лінія C, пайка
G2_MULT = 1.8                                                # нічна зміна, збірка

units["scrap_stage"] = 0
units["alive"] = True

# 4. Йдемо по етапах
for stage, p0 in BASE_P.items():
    p = pd.Series(p0, index=units.index)

    if stage == 2:
        mask = units["line_id"] == 3
        p[mask] = p0 * units.loc[mask, "month_idx"].map(G1_MULT)
    if stage == 4:
        mask = units["shift_id"] == 2
        p[mask] = p0 * G2_MULT

    # Ламається тільки той, хто ще живий
    broken = units["alive"] & (rng.random(len(units)) < p.to_numpy())
    units.loc[broken, "scrap_stage"] = stage
    units.loc[broken, "alive"] = False

# 5. Підсумок
units["scrapped_at_stage_id"] = units["scrap_stage"].where(units["scrap_stage"] > 0).astype("Int64")
units["final_status"] = np.where(units["scrap_stage"] == 0, "Good", "Rejected")

out = units[["unit_id", "batch_id", "scrapped_at_stage_id", "final_status"]]
out.to_csv(RAW_DIR / "units.csv", index=False)

# Перевірки
assert out["unit_id"].is_unique
assert len(out) == batches["qty_started"].sum()
print("All checks passed")

# Підсумки
good = (out["final_status"] == "Good").sum()
print("Units:", len(out))
print("Good:", good, "| Rejected:", len(out) - good)
print("Scrap by stage:")
print(out["scrapped_at_stage_id"].value_counts().sort_index())

print("\nG2: брак на етапі 4 по змінах")
print((units["scrap_stage"] == 4).groupby(units["shift_id"]).mean().round(4))

print("\nG1: брак на етапі 2, лінія C, по місяцях")
c = units[units["line_id"] == 3]
print((c["scrap_stage"] == 2).groupby(c["month_idx"]).mean().round(4))