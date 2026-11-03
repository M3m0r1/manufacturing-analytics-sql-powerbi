import pandas as pd
from config import RAW_DIR, ROOT

# ---------------------------------------------------------
# КРОК 1. Читаємо всі таблиці з папки data/raw
# ---------------------------------------------------------
# Ця функція відкриває файл за назвою, наприклад load("units")
def load(name):
    return pd.read_csv(RAW_DIR / f"{name}.csv")

dim_date = load("dim_date")             # календар
products = load("products")             # продукти
lines = load("production_lines")        # лінії
stages = load("production_stages")      # етапи
shifts = load("shifts")                 # зміни
defects = load("defect_types")          # типи дефектів
reasons = load("downtime_reasons")      # причини простоїв
plan = load("production_plan")          # план
orders = load("work_orders")            # замовлення
batches = load("batches")               # партії
units = load("units")                   # вироби
tests = load("test_results")            # спроби тестування
insp = load("quality_inspections")      # інспекції
downtime = load("downtime_records")     # простої
costs = load("production_costs")        # витрати

# ---------------------------------------------------------
# КРОК 2. Функція check: ставить питання і друкує OK або FAIL
# ---------------------------------------------------------
results = []   # тут запам'ятовуємо всі відповіді

def check(name, condition):
    ok = bool(condition)               # True або False
    results.append((name, ok))         # зберігаємо відповідь
    print(("OK   " if ok else "FAIL ") + name)

# ---------------------------------------------------------
# КРОК 3. Немає дублів
# is_unique = "усі значення різні"
# ---------------------------------------------------------
check("plan_id без дублів", plan["plan_id"].is_unique)
check("work_order_id без дублів", orders["work_order_id"].is_unique)
check("batch_id без дублів", batches["batch_id"].is_unique)
check("unit_id без дублів", units["unit_id"].is_unique)
check("test_id без дублів", tests["test_id"].is_unique)
check("inspection_id без дублів", insp["inspection_id"].is_unique)
check("downtime_id без дублів", downtime["downtime_id"].is_unique)
check("cost_id без дублів", costs["cost_id"].is_unique)

# ---------------------------------------------------------
# КРОК 4. Зв'язки між таблицями
# isin(...).all() = "кожне значення з цієї таблиці є в довіднику"
# Наприклад: кожен unit_id у тестах існує в таблиці units
# ---------------------------------------------------------

# План
check("plan: дата є в календарі", plan["date_id"].isin(dim_date["date_id"]).all())
check("plan: лінія є в довіднику", plan["line_id"].isin(lines["line_id"]).all())
check("plan: продукт є в довіднику", plan["product_id"].isin(products["product_id"]).all())

# Замовлення, партії, вироби
check("orders: plan_id є в плані", orders["plan_id"].isin(plan["plan_id"]).all())
check("batches: замовлення існує", batches["work_order_id"].isin(orders["work_order_id"]).all())
check("batches: зміна існує", batches["shift_id"].isin(shifts["shift_id"]).all())
check("units: партія існує", units["batch_id"].isin(batches["batch_id"]).all())

# Тести
check("tests: виріб існує", tests["unit_id"].isin(units["unit_id"]).all())
check("tests: дата є в календарі", tests["date_id"].isin(dim_date["date_id"]).all())
# dropna() прибирає пусті дефекти (у Pass дефекту немає)
check("tests: дефект існує", tests["defect_type_id"].dropna().isin(defects["defect_type_id"]).all())

# Інспекції
check("insp: виріб існує", insp["unit_id"].isin(units["unit_id"]).all())
check("insp: етап існує", insp["stage_id"].isin(stages["stage_id"]).all())
check("insp: дефект існує", insp["defect_type_id"].isin(defects["defect_type_id"]).all())

# Простої
check("downtime: дата є в календарі", downtime["date_id"].isin(dim_date["date_id"]).all())
check("downtime: лінія існує", downtime["line_id"].isin(lines["line_id"]).all())
check("downtime: зміна існує", downtime["shift_id"].isin(shifts["shift_id"]).all())
check("downtime: причина існує", downtime["reason_id"].isin(reasons["reason_id"]).all())

# Витрати
check("costs: дата є в календарі", costs["date_id"].isin(dim_date["date_id"]).all())
check("costs: лінія існує", costs["line_id"].isin(lines["line_id"]).all())
check("costs: продукт існує", costs["product_id"].isin(products["product_id"]).all())

# ---------------------------------------------------------
# КРОК 5. Статуси виробів
# ---------------------------------------------------------
# Окремо беремо придатні й забраковані
good = units[units["final_status"] == "Good"]
rejected = units[units["final_status"] == "Rejected"]

# Кожен виріб або Good, або Rejected, третього немає
check("Good + Rejected = усі вироби", len(good) + len(rejected) == len(units))
# Придатний виріб не має етапу списання (там пусто)
check("Good: етапу списання немає", good["scrapped_at_stage_id"].isna().all())
# Забракований виріб має етап списання (там число)
check("Rejected: етап списання є", rejected["scrapped_at_stage_id"].notna().all())

# ---------------------------------------------------------
# КРОК 6. Тестування
# ---------------------------------------------------------
# Не більше 3 спроб
check("Максимум 3 спроби", tests["attempt_no"].max() <= 3)

# duplicated = "є повтор". not = "повторів немає"
# Не може бути двох спроб №1 для одного виробу
check("Немає двох однакових спроб одного виробу",
      not tests.duplicated(["unit_id", "attempt_no"]).any())

# Хто мав дійти до тесту: придатні і списані на етапах 5, 6, 7
stage = units["scrapped_at_stage_id"]
expected_tested = set(units.loc[stage.isna() | (stage >= 5), "unit_id"])
check("Тестувалися саме ті вироби, що дійшли до етапу 5",
      set(tests["unit_id"]) == expected_tested)

# Беремо останню спробу кожного виробу
last = tests.sort_values("attempt_no").groupby("unit_id").tail(1)
last = last.merge(units[["unit_id", "final_status"]], on="unit_id")

# У придатного виробу остання спроба має бути успішною
check("У Good остання спроба = Pass",
      (last.loc[last["final_status"] == "Good", "result"] == "Pass").all())

# Вироби, списані на етапі 5, провалили всі спроби
s5_ids = set(units.loc[stage == 5, "unit_id"])
s5_tests = tests[tests["unit_id"].isin(s5_ids)]
check("Списані на етапі 5: усі спроби Fail", (s5_tests["result"] == "Fail").all())

# ---------------------------------------------------------
# КРОК 7. Інспекції
# ---------------------------------------------------------
# Один виріб = одна інспекція
check("Інспекції: один виріб = один рядок", insp["unit_id"].is_unique)

# Id виробів з Fail і з Reworked
fail_ids = set(insp.loc[insp["result"] == "Fail", "unit_id"])
rework_ids = set(insp.loc[insp["result"] == "Reworked", "unit_id"])

# <= для множин означає "усі входять у"
check("Fail-інспекції лише в Rejected", fail_ids <= set(rejected["unit_id"]))
check("Reworked-інспекції лише в Good", rework_ids <= set(good["unit_id"]))

# ---------------------------------------------------------
# КРОК 8. Простої і витрати
# ---------------------------------------------------------
check("Простої: тривалість більше 0", (downtime["duration_min"] > 0).all())
check("Витрати: усі суми більше 0", (costs["total_cost"] > 0).all())
# Усі вироби враховані у витратах
check("Витрати: запущено = кількість виробів", costs["units_started"].sum() == len(units))

# ---------------------------------------------------------
# КРОК 9. Контрольні суми
# Це числа з наших запусків. Якщо щось змінимо в даних, вони не збіжаться
# Формат: назва -> (що в даних зараз, що очікуємо)
# ---------------------------------------------------------
expected = {
    "Planned Units": (plan["planned_good_units"].sum(), 164684),
    "Units": (len(units), 165885),
    "Good": (len(good), 153881),
    "Rejected": (len(rejected), 12004),
    "Tested units": (tests["unit_id"].nunique(), 158026),
    "Test attempts": (len(tests), 177558),
    "Inspections": (len(insp), 12608),
    "Downtime events": (len(downtime), 1428),
    "Cost rows": (len(costs), 1099),
}
for name, (actual, exp) in expected.items():
    check(f"{name}: {actual} (очікувано {exp})", actual == exp)

# ---------------------------------------------------------
# КРОК 10. Підсумок і звіт у файл
# ---------------------------------------------------------
# Збираємо назви перевірок, які впали
failed = [name for name, ok in results if not ok]
print(f"\nПеревірок: {len(results)} | Помилок: {len(failed)}")

# Створюємо папку docs, якщо її ще немає
report_dir = ROOT / "docs"
report_dir.mkdir(exist_ok=True)

# Записуємо всі результати у текстовий файл
with open(report_dir / "validation_report.txt", "w", encoding="utf-8") as f:
    for name, ok in results:
        f.write(("OK   " if ok else "FAIL ") + name + "\n")
    f.write(f"\nTotal: {len(results)} | Failed: {len(failed)}\n")

print("Звіт збережено: docs/validation_report.txt")