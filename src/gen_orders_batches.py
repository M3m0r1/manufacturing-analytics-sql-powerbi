import numpy as np
import pandas as pd
from config import RAW_DIR

plan = pd.read_csv(RAW_DIR / "production_plan.csv")
downtime = pd.read_csv(RAW_DIR / "downtime_records.csv")

BATCH_SIZE = 50
EXPECTED_YIELD = 0.93
RUN_MIN = 660            # робочих хвилин на зміну

# Скільки хвилин простою було: (дата, лінія, зміна) -> хвилини
lost = downtime.groupby(["date_id", "line_id", "shift_id"])["duration_min"].sum().to_dict()

# Замовлення (як раніше)
work_orders = plan.copy()
work_orders["qty_ordered"] = np.ceil(work_orders["planned_good_units"] / EXPECTED_YIELD).astype(int)
work_orders.insert(0, "work_order_id", range(1, len(work_orders) + 1))
work_orders = work_orders[["work_order_id", "plan_id", "date_id", "line_id", "product_id", "qty_ordered"]]

# Партії
rows = []
batch_id = 1
for order in work_orders.itertuples():
    left = order.qty_ordered
    n_batches = int(np.ceil(left / BATCH_SIZE))
    for i in range(n_batches):
        qty = min(BATCH_SIZE, left)
        left -= qty
        shift_id = 1 if i < n_batches / 2 else 2

        # Частка часу, яку зміна простояла (не більше 90%)
        minutes = lost.get((order.date_id, order.line_id, shift_id), 0)
        lost_share = min(minutes / RUN_MIN, 0.9)

        # Фактично запущено менше
        started = int(round(qty * (1 - lost_share)))
        if started == 0:
            continue

        rows.append({"batch_id": batch_id, "work_order_id": order.work_order_id,
                     "shift_id": shift_id, "qty_planned": qty, "qty_started": started})
        batch_id += 1
batches = pd.DataFrame(rows)

work_orders.to_csv(RAW_DIR / "work_orders.csv", index=False)
batches.to_csv(RAW_DIR / "batches.csv", index=False)
print("work_orders:", len(work_orders))
print("batches:", len(batches))

# Перевірки
assert batches["batch_id"].is_unique
assert batches["qty_started"].sum() <= work_orders["qty_ordered"].sum()
print("All checks passed")
print("Total qty_ordered:", work_orders["qty_ordered"].sum())
print("Total qty_started:", batches["qty_started"].sum())
print("Started / Ordered:", round(batches["qty_started"].sum() / work_orders["qty_ordered"].sum(), 4))