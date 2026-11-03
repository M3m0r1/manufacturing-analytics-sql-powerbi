import pyodbc
import os
SERVER = os.getenv("SQL_SERVER", "localhost")

# 1. Показуємо, які драйвери для SQL Server є на комп'ютері
drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
print("Знайдені драйвери:", drivers)

# 2. Беремо найновіший драйвер зі списку
driver = sorted(drivers)[-1]
print("Використовуємо:", driver)

# 3. Рядок підключення
# Trusted_Connection=yes означає вхід через Windows, пароль не потрібен
# TrustServerCertificate=yes потрібен для драйвера 18, інакше буде помилка сертифіката
conn_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER={SERVER};"
    "DATABASE=Ajax_Mfg_Analytics;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

# 4. Підключаємось і ставимо простий запит
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("SELECT DB_NAME()")
print("Підключено до бази:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES")
print("Таблиць у базі:", cursor.fetchone()[0])

conn.close()