import pandas as pd
from config import RAW_DIR

# Зміни
shifts = pd.DataFrame([
    {"shift_id": 1, "shift_name": "Day",   "start_time": "08:00", "end_time": "20:00", "crosses_midnight": 0, "planned_break_min": 60},
    {"shift_id": 2, "shift_name": "Night", "start_time": "20:00", "end_time": "08:00", "crosses_midnight": 1, "planned_break_min": 60},
])
shifts["planned_run_min"] = 720 - shifts["planned_break_min"]   # 660 хв

# Продукти
products = pd.DataFrame([
    {"product_id": 1, "product_code": "MS-100", "product_name": "Motion Sensor",       "category": "Motion & Opening", "material_cost_uah": 420},
    {"product_id": 2, "product_code": "DS-100", "product_name": "Door/Opening Sensor", "category": "Motion & Opening", "material_cost_uah": 260},
    {"product_id": 3, "product_code": "HB-200", "product_name": "Control Hub",         "category": "Control Unit",     "material_cost_uah": 1350},
    {"product_id": 4, "product_code": "FS-300", "product_name": "Fire Sensor",         "category": "Fire Detection",   "material_cost_uah": 580},
])

# Лінії
lines = pd.DataFrame([
    {"line_id": 1, "line_name": "Line A", "line_type": "Sensors"},
    {"line_id": 2, "line_name": "Line B", "line_type": "Sensors"},
    {"line_id": 3, "line_name": "Line C", "line_type": "Hubs"},
    {"line_id": 4, "line_name": "Line D", "line_type": "Flexible"},
])

# Етапи (cost_accumulated_pct - частка вартості, вже вкладена у виріб, від 0 до 1)
stages = pd.DataFrame([
    {"stage_id": 1, "stage_name": "SMT Assembly",      "stage_order": 1, "cost_accumulated_pct": 0.35},
    {"stage_id": 2, "stage_name": "Soldering & Board", "stage_order": 2, "cost_accumulated_pct": 0.50},
    {"stage_id": 3, "stage_name": "Firmware/Config",   "stage_order": 3, "cost_accumulated_pct": 0.58},
    {"stage_id": 4, "stage_name": "Final Assembly",    "stage_order": 4, "cost_accumulated_pct": 0.75},
    {"stage_id": 5, "stage_name": "Functional Test",   "stage_order": 5, "cost_accumulated_pct": 0.85},
    {"stage_id": 6, "stage_name": "Quality Control",   "stage_order": 6, "cost_accumulated_pct": 0.90},
    {"stage_id": 7, "stage_name": "Packaging",         "stage_order": 7, "cost_accumulated_pct": 1.00},
])

# Хвилини на 1 виріб по етапах 1..7 для кожного продукту
minutes = {
    1: [1.2, 1.5, 0.8, 1.4, 1.6, 0.6, 0.5],
    2: [0.9, 1.0, 0.5, 0.8, 1.0, 0.4, 0.4],
    3: [2.0, 2.6, 2.2, 2.8, 3.4, 0.9, 0.7],
    4: [1.4, 1.8, 1.0, 1.6, 2.4, 1.0, 0.5],
}
rows = []
for product_id, mins in minutes.items():
    for i, m in enumerate(mins):
        rows.append({"product_id": product_id, "stage_id": i + 1, "std_minutes_per_unit": m})
routing = pd.DataFrame(rows)

# Зберігаємо
tables = {"shifts": shifts, "products": products, "production_lines": lines,
          "production_stages": stages, "product_routing": routing}
for name, df in tables.items():
    df.to_csv(RAW_DIR / f"{name}.csv", index=False)
    print(name, len(df))

# Перевірки
assert (routing.groupby("product_id")["stage_id"].nunique() == 7).all()
assert stages["cost_accumulated_pct"].is_monotonic_increasing
assert stages["cost_accumulated_pct"].iloc[-1] == 1.0
print("All checks passed")