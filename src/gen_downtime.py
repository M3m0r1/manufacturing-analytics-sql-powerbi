import numpy as np
import pandas as pd
from config import RAW_DIR, SEED

rng = np.random.default_rng(SEED + 3)

dim_date = pd.read_csv(RAW_DIR / "dim_date.csv")

# Працюємо лише в дні, коли є виробництво (без неділі)
work_days = dim_date[dim_date["day_of_week"] != 7]["date_id"]

# Скільки простоїв у середньому за зміну
AVG_EVENTS = {1: 1.0,    # 1 = Day
              2: 1.3}    # 2 = Night (вночі більше)

# Ймовірності причин (6 причин, сума = 1)
REASON_WEIGHTS_NORMAL = [0.15, 0.25, 0.15, 0.20, 0.10, 0.15]
REASON_WEIGHTS_LINE_C = [0.35, 0.20, 0.10, 0.15, 0.10, 0.10]   # на лінії C більше нестачі деталей

rows = []
for date_id in work_days:
    for line_id in [1, 2, 3, 4]:
        for shift_id in [1, 2]:
            # Скільки простоїв було в цю зміну
            n_events = rng.poisson(AVG_EVENTS[shift_id])
            for _ in range(n_events):
                if line_id == 3:
                    weights = REASON_WEIGHTS_LINE_C
                else:
                    weights = REASON_WEIGHTS_NORMAL
                rows.append({
                    "date_id": date_id,
                    "line_id": line_id,
                    "shift_id": shift_id,
                    "reason_id": int(rng.choice([1, 2, 3, 4, 5, 6], p=weights)),
                    "duration_min": int(rng.integers(10, 71)),   # від 10 до 70 хвилин
                })

downtime = pd.DataFrame(rows)
downtime.insert(0, "downtime_id", range(1, len(downtime) + 1))
downtime.to_csv(RAW_DIR / "downtime_records.csv", index=False)

# --- Перевірки ---
assert downtime["downtime_id"].is_unique
assert (downtime["duration_min"] > 0).all()
assert downtime["reason_id"].between(1, 6).all()
print("All checks passed")

# --- Підсумки ---
print("Downtime events:", len(downtime))
print("Downtime hours:", round(downtime["duration_min"].sum() / 60, 1))

# Простій у % від робочого часу (660 хв на зміну)
shift_count = len(work_days) * 4      # днів × 4 лінії (на одну зміну)
print("\nDowntime % по змінах:")
by_shift = downtime.groupby("shift_id")["duration_min"].sum()
print((by_shift / (shift_count * 660) * 100).round(2))

print("\nПростої через Component Shortage (хв) по лініях:")
shortage = downtime[downtime["reason_id"] == 1]
print(shortage.groupby("line_id")["duration_min"].sum())