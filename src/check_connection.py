import os
import pyodbc

SERVER = os.getenv("SQL_SERVER", "localhost")
print("Сервер:", SERVER)

drivers = sorted(d for d in pyodbc.drivers() if d.startswith("ODBC Driver"))
print("Знайдені драйвери:", drivers)
driver = drivers[-1]
print("Використовуємо:", driver)

conn_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER={SERVER};"
    "DATABASE=Mfg_Analytics;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("SELECT DB_NAME()")
print("Підключено до бази:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES")
print("Таблиць у базі:", cursor.fetchone()[0])

conn.close()
