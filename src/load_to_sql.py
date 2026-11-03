import pandas as pd
import pyodbc
from config import RAW_DIR

# ---------------------------------------------------------
# 1. Підключення до SQL Server
# ---------------------------------------------------------
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER={SERVER};"
    "DATABASE=Ajax_Mfg_Analytics;"
    "Trusted_Connection=yes;"          # вхід через Windows, пароль не потрібен
    "TrustServerCertificate=yes;"
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
cursor.fast_executemany = True         # швидка вставка великих таблиць

# ---------------------------------------------------------
# 2. Порядок таблиць: спершу батьківські, потім дочірні
# (FOREIGN KEY не дозволяє вставити рядок без батька)
# ---------------------------------------------------------
TABLES = [
    "dim_date", "shifts", "products", "production_lines", "production_stages",
    "product_routing", "defect_types", "downtime_reasons", "employees",
    "production_plan", "work_orders", "batches", "units",
    "test_results", "quality_inspections", "downtime_records", "production_costs",
]

# ---------------------------------------------------------
# 3. Очищаємо таблиці у ЗВОРОТНОМУ порядку
# Спершу видаляємо дочірні, потім батьківські. Так повторний запуск не дає дублів
# ---------------------------------------------------------
for table in reversed(TABLES):
    cursor.execute(f"DELETE FROM {table}")
conn.commit()
print("Таблиці очищено\n")

# ---------------------------------------------------------
# 4. Функція завантаження однієї таблиці
# ---------------------------------------------------------
def load_table(table):
    df = pd.read_csv(RAW_DIR / f"{table}.csv")

    # Порожні числові стовпці (наприклад, scrapped_at_stage_id) pandas читає як 2.0, 5.0.
    # Перетворюємо їх назад на цілі числа, щоб у SQL потрапили 2 і 5
    for col in df.columns:
        if df[col].dtype == "float64":
            not_null = df[col].dropna()
            if len(not_null) > 0 and (not_null % 1 == 0).all():
                df[col] = df[col].astype("Int64")

    # Порожні значення (NaN) замінюємо на None, у SQL це буде NULL
    rows = df.astype(object).where(df.notna(), None).values.tolist()

    # Назви стовпців у квадратних дужках, бо [date], [year] зарезервовані слова
    cols = ", ".join(f"[{c}]" for c in df.columns)
    placeholders = ", ".join("?" for _ in df.columns)
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"

    # Вставляємо порціями по 10 000 рядків
    for start in range(0, len(rows), 10000):
        cursor.executemany(sql, rows[start:start + 10000])
    conn.commit()
    return len(df)

# ---------------------------------------------------------
# 5. Завантажуємо всі таблиці по черзі
# ---------------------------------------------------------
csv_counts = {}
for table in TABLES:
    csv_counts[table] = load_table(table)
    print(f"{table}: завантажено {csv_counts[table]}")

# ---------------------------------------------------------
# 6. Перевірка: кількість рядків у SQL = кількість рядків у CSV
# ---------------------------------------------------------
print("\nПеревірка:")
all_ok = True
for table in TABLES:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    in_sql = cursor.fetchone()[0]
    ok = in_sql == csv_counts[table]
    all_ok = all_ok and ok
    print(("OK   " if ok else "FAIL ") + f"{table}: CSV {csv_counts[table]} | SQL {in_sql}")

print("\nУсе збіглося" if all_ok else "\nЄ розбіжності")
conn.close()