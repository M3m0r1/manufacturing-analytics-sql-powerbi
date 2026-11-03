import numpy as np
import pandas as pd
from config import RAW_DIR, START_DATE, END_DATE

# Календар: 1 рядок = 1 день
dates = pd.date_range(START_DATE, END_DATE, freq="D")
dim_date = pd.DataFrame({
    "date_id": dates.strftime("%Y%m%d").astype(int),
    "date": dates.date,
    "year": dates.year,
    "month": dates.month,
    "month_name": dates.strftime("%B"),
    "week": dates.isocalendar().week.values,
    "day_of_week": dates.dayofweek + 1,      # 1 = Пн, 7 = Нд
    "day_name": dates.strftime("%A"),
    "is_weekend": (dates.dayofweek >= 5).astype(int),
})

# Скільки хвилин іде на 1 виріб (сума по всіх етапах)
routing = pd.read_csv(RAW_DIR / "product_routing.csv")
total_min = routing.groupby("product_id")["std_minutes_per_unit"].sum()

RUN_MIN = 660        # робочих хвилин на зміну
SHIFTS = 2
LOAD = 0.85
WORKSTATIONS = 2

# (лінія, продукт): яку частку потужності лінії займає продукт
share = {(1, 1): 0.5, (1, 2): 0.5,
         (2, 1): 0.5, (2, 2): 0.5,
         (3, 3): 1.0,
         (4, 4): 0.7, (4, 1): 0.3}

rows = []
for d in dim_date.itertuples():
    if d.day_of_week == 7:                 # неділя - не працюємо
        continue
    factor = 0.5 if d.day_of_week == 6 else 1.0    # субота - половина
    for (line_id, product_id), s in share.items():
        capacity = RUN_MIN * SHIFTS * LOAD * WORKSTATIONS * s
        planned = int(np.floor(capacity / total_min[product_id] * factor))
        rows.append({"date_id": d.date_id, "line_id": line_id,
                     "product_id": product_id, "planned_good_units": planned})

plan = pd.DataFrame(rows)
plan.insert(0, "plan_id", range(1, len(plan) + 1))

dim_date.to_csv(RAW_DIR / "dim_date.csv", index=False)
plan.to_csv(RAW_DIR / "production_plan.csv", index=False)
print("dim_date:", len(dim_date))
print("production_plan:", len(plan))

# Перевірки
assert dim_date["date_id"].is_unique
assert not plan.duplicated(["date_id", "line_id", "product_id"]).any()
assert (plan["planned_good_units"] > 0).all()
print("All checks passed")
print("Total planned good units:", plan["planned_good_units"].sum())   # 164684