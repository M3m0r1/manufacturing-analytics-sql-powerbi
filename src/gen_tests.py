import numpy as np
import pandas as pd
from config import RAW_DIR, SEED

rng = np.random.default_rng(SEED + 2)

units = pd.read_csv(RAW_DIR / "units.csv")
batches = pd.read_csv(RAW_DIR / "batches.csv")
wo = pd.read_csv(RAW_DIR / "work_orders.csv")
dim_date = pd.read_csv(RAW_DIR / "dim_date.csv")

# 1. Одна таблиця з усім потрібним про виріб
u = units.merge(batches[["batch_id", "work_order_id"]], on="batch_id")
u = u.merge(wo[["work_order_id", "date_id", "line_id", "product_id"]], on="work_order_id")
u = u.merge(dim_date[["date_id", "month"]], on="date_id")
u["month_idx"] = u["month"] - 3

# 2. Тестуємо тих, хто дійшов до етапу 5: придатних і списаних на етапах 5, 6, 7
stage = u["scrapped_at_stage_id"]
tested = u[stage.isna() | (stage >= 5)].copy()
tested["is_s5"] = tested["scrapped_at_stage_id"] == 5

# 3. Шанс провалити першу спробу
f = pd.Series(0.06, index=tested.index)
f[tested["product_id"] == 4] *= 2.0                                # G3: FS-300
f[(tested["line_id"] == 3) & (tested["month_idx"] <= 4)] *= 1.5    # G4: лінія C до ремонту

fail1 = rng.random(len(tested)) < f.to_numpy()    # перша спроба невдала?
fail2 = rng.random(len(tested)) < 0.30            # друга теж невдала?

# 4. Скільки спроб у виробу
tested["n_attempts"] = np.select(
    [tested["is_s5"].to_numpy(), fail1 & fail2, fail1],
    [3, 3, 2],
    default=1,
)

# 5. Кожна спроба - окремий рядок
t = tested.loc[tested.index.repeat(tested["n_attempts"]),
               ["unit_id", "date_id", "product_id", "n_attempts", "is_s5"]].reset_index(drop=True)

row_number_in_unit = t.groupby("unit_id").cumcount()
t["attempt_no"] = row_number_in_unit + 1

# 6. Остання спроба = Pass (крім виробів, списаних на етапі 5)
is_last = t["attempt_no"] == t["n_attempts"]
t["result"] = np.where(is_last & ~t["is_s5"], "Pass", "Fail")

# 7. Тип дефекту тільки для Fail
chance_6 = np.where(t["product_id"] == 4, 0.7, 0.4)
defect = pd.Series(np.where(rng.random(len(t)) < chance_6, 6, 7))
t["defect_type_id"] = defect.where(t["result"] == "Fail").astype("Int64")

t["test_id"] = range(1, len(t) + 1)
out = t[["test_id", "unit_id", "attempt_no", "date_id", "result", "defect_type_id"]]
out.to_csv(RAW_DIR / "test_results.csv", index=False)

# Перевірки
assert out["test_id"].is_unique
assert not out.duplicated(["unit_id", "attempt_no"]).any()
assert out["attempt_no"].max() <= 3
assert out["unit_id"].nunique() == len(tested)
print("All checks passed")

# Підсумки
print("Test rows (attempts):", len(out))
print("Unique tested units:", out["unit_id"].nunique())
print("FPY:", round((tested["n_attempts"] == 1).mean(), 4))
print("Retest Rate:", round((tested["n_attempts"] >= 2).mean(), 4))

print("\nG3: по продуктах")
print(tested.groupby("product_id")["n_attempts"]
      .agg(FPY=lambda s: (s == 1).mean(), Retest=lambda s: (s >= 2).mean()).round(4))

print("\nG4: Retest лінії C по місяцях")
c = tested[tested["line_id"] == 3]
print(c.groupby("month_idx")["n_attempts"].apply(lambda s: (s >= 2).mean()).round(4))