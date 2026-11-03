import pandas as pd
from config import RAW_DIR

# --- Читаємо готові таблиці ---
products = pd.read_csv(RAW_DIR / "products.csv")
batches = pd.read_csv(RAW_DIR / "batches.csv")
wo = pd.read_csv(RAW_DIR / "work_orders.csv")
units = pd.read_csv(RAW_DIR / "units.csv")

# --- Припущення про витрати (це не реальні дані) ---
RATES = {"Operator": 150,
         "Tester": 200,         # грн/год на людину
         "Inspector": 250}

CREW = {"Operator": 5,
        "Tester": 2,            # людей на лінії в одну зміну
        "Inspector": 1}

# Вартість усієї бригади за 1 годину: 5*150 + 2*200 + 1*250 = 1400
CREW_RATE = sum(RATES[role] * CREW[role] for role in RATES)

SHIFT_HOURS = 12
NIGHT_BONUS = 0.20       # вночі платимо на 20% більше
OVERHEAD_DAY = 8000      # накладні: грн на день на лінію

# Праця за день на лінію: Day (1.0) + Night (1.2) = 2.2 "ставки"
LABOR_DAY = CREW_RATE * SHIFT_HOURS * (1 + 1 + NIGHT_BONUS)   # 36960

# --- 1. Скільки виробів запущено: день, лінія, продукт ---
b = batches.merge(wo[["work_order_id", "date_id", "line_id", "product_id"]], on="work_order_id")
costs = b.groupby(["date_id", "line_id", "product_id"], as_index=False)["qty_started"].sum()
costs = costs.rename(columns={"qty_started": "units_started"})

# --- 2. Матеріали: вартість на виріб * запущено (брак теж з'їв матеріали) ---
costs = costs.merge(products[["product_id", "material_cost_uah"]], on="product_id")
costs["material_cost"] = costs["units_started"] * costs["material_cost_uah"]

# --- 3. Праця й накладні ---
# Їх рахуємо на всю лінію за день, тому ділимо між продуктами цієї лінії
# за часткою запущених виробів
total_on_line = costs.groupby(["date_id", "line_id"])["units_started"].transform("sum")
share = costs["units_started"] / total_on_line

costs["labor_cost"] = LABOR_DAY * share
costs["overhead_cost"] = OVERHEAD_DAY * share
costs["total_cost"] = costs["material_cost"] + costs["labor_cost"] + costs["overhead_cost"]

# --- 4. Зберігаємо ---
costs = costs.drop(columns="material_cost_uah").round(2)
costs.insert(0, "cost_id", range(1, len(costs) + 1))
costs.to_csv(RAW_DIR / "production_costs.csv", index=False)

# --- Перевірки ---
assert costs["cost_id"].is_unique
assert not costs.duplicated(["date_id", "line_id", "product_id"]).any()
assert (costs["total_cost"] > 0).all()
assert costs["units_started"].sum() == len(units)      # усі вироби враховані

# Сума праці й накладних = (кількість днів-ліній) * ставка за день
line_days = costs[["date_id", "line_id"]].drop_duplicates().shape[0]
assert abs(costs["labor_cost"].sum() - line_days * LABOR_DAY) < 1
assert abs(costs["overhead_cost"].sum() - line_days * OVERHEAD_DAY) < 1
print("All checks passed")

# --- Підсумки ---
print("Rows:", len(costs))
print("Material:", round(costs["material_cost"].sum()))
print("Labor:", round(costs["labor_cost"].sum()))
print("Overhead:", round(costs["overhead_cost"].sum()))
print("Total:", round(costs["total_cost"].sum()))

# --- Cost per Good Unit (K12): усі витрати / ПРИДАТНІ вироби ---
u = units.merge(batches[["batch_id", "work_order_id"]], on="batch_id")
u = u.merge(wo[["work_order_id", "product_id"]], on="work_order_id")
good = u[u["final_status"] == "Good"].groupby("product_id").size()

cost_by_product = costs.groupby("product_id")["total_cost"].sum()
print("\nCost per Good Unit, грн:")
print((cost_by_product / good).round(2))
print("Усього:", round(costs["total_cost"].sum() / good.sum(), 2))