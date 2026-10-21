# Databricks notebook source
# MAGIC %md
# MAGIC # 02 Smoke test: is my Databricks setup ready for the workshop?
# MAGIC
# MAGIC **Participant notebook. Run it before the workshop: attach compute, then select Run all.**
# MAGIC It takes about one minute and changes nothing except one small test table in your own schema,
# MAGIC which it removes again.
# MAGIC
# MAGIC | Test | What it proves |
# MAGIC |---|---|
# MAGIC | 1 | You are signed in, and the notebook is attached to compute |
# MAGIC | 2 | You can read all 13 training tables, and they are complete |
# MAGIC | 3 | You have an output schema of your own, and you can create, read, and drop a table in it |
# MAGIC | 4 | The compute rounds and casts the way the labs expect |
# MAGIC
# MAGIC The last line must be `READY`. If it is not, send the output of the last cell to the instructor.

# COMMAND ----------

import re

DEFAULT_CATALOG = "o2iworkshop"  # written by tools/prepare_cohort.py

dbutils.widgets.text("catalog", DEFAULT_CATALOG, "Catalog")
CATALOG = dbutils.widgets.get("catalog").strip()

EXPECTED_ROWS = {
    'invoice_lines': 49700,
    'customers': 1180,
    'products': 601,
    'orders': 55448,
    'fixture_invoice_lines': 56,
    'fixture_customers': 11,
    'fixture_products': 9,
    'fixture_orders': 42,
    'fixture_expected_results': 112,
    'fixture_expected_amounts': 22,
    'challenge_invoice_lines': 191,
    'challenge_expected_results': 382,
    'reference_totals': 16,
}

problems = []


def result(ok: bool, text: str, hint: str = "") -> None:
    print(f"{'OK   ' if ok else 'CHECK'} {text}")
    if not ok:
        problems.append(text)
        if hint:
            print(f"      {hint}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 1. Who and where

# COMMAND ----------

user = spark.sql("SELECT current_user() AS u").first()["u"]
MY_SCHEMA = "o2i_" + re.sub(r"[^a-z0-9]+", "_", user.split("@")[0].lower()).strip("_")
result(True, f"Signed in as {user}")
result(True, f"Spark {spark.version} answered")
try:
    ansi = spark.conf.get("spark.sql.ansi.enabled")
    print(f"      ANSI mode: {ansi}")
except Exception:
    print("      ANSI mode: not readable on this compute")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 2. The training tables

# COMMAND ----------

for table, expected in EXPECTED_ROWS.items():
    try:
        rows = spark.table(f"`{CATALOG}`.o2i.{table}").count()
        result(rows == expected, f"{table:28s} {rows:>7,} rows" + ("" if rows == expected else f", expected {expected:,}"),
               "Ask the instructor to run the setup notebook again.")
    except Exception as error:
        result(False, f"{table:28s} cannot be read: {(str(error).splitlines() or [''])[0][:110]}",
               "You need USE CATALOG on the catalog, and USE SCHEMA and SELECT on the schema o2i.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 3. Your output schema
# MAGIC
# MAGIC Labs 2 to 4 write their output tables to a schema of your own. Its name comes from your sign-in name.

# COMMAND ----------

target = f"`{CATALOG}`.`{MY_SCHEMA}`"
try:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {target}")
    result(True, f"Output schema {CATALOG}.{MY_SCHEMA} exists")
except Exception as error:
    result(False, f"Output schema {CATALOG}.{MY_SCHEMA} is missing and you cannot create it: {(str(error).splitlines() or [''])[0][:100]}",
           "Ask the instructor to provision your schema.")

try:
    spark.sql("SELECT 'F0001' AS RawRowID, CAST(367.15 AS DECIMAL(18,2)) AS NetAmount").write.mode("overwrite").saveAsTable(f"{target}.smoke_test")
    back = spark.table(f"{target}.smoke_test").first()
    spark.sql(f"DROP TABLE {target}.smoke_test")
    result(str(back["NetAmount"]) == "367.15", "Created, read, and dropped a table in your schema")
except Exception as error:
    result(False, f"Cannot write to your schema: {(str(error).splitlines() or [''])[0][:110]}",
           "You need USE SCHEMA and CREATE TABLE on your output schema.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 4. Rounding and casting
# MAGIC
# MAGIC The business contract rounds half up, and it holds an invalid date instead of failing. These three
# MAGIC values show that the compute behaves the same way.

# COMMAND ----------

row = spark.sql("""
    SELECT CAST(round(CAST(3.00 AS DECIMAL(18,2)) * CAST(0.0550 AS DECIMAL(6,4)), 2) AS STRING) AS tie_up,
           CAST(round(CAST(-3.00 AS DECIMAL(18,2)) * CAST(0.0550 AS DECIMAL(6,4)), 2) AS STRING) AS tie_down,
           try_cast('2026-02-30' AS DATE) IS NULL AS invalid_date_is_null
""").first()
result(row["tie_up"].startswith("0.17") and row["tie_down"].startswith("-0.17"),
       f"round() rounds half up: 3.00 x 0.0550 gives {row['tie_up']}, and -3.00 x 0.0550 gives {row['tie_down']}")
result(bool(row["invalid_date_is_null"]), "try_cast returns NULL for the invalid date 2026-02-30")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Result

# COMMAND ----------

print(f"User:           {user}")
print(f"Catalog:        {CATALOG}")
print(f"Output schema:  {CATALOG}.{MY_SCHEMA}")
print(f"Spark:          {spark.version}")
print()
print("READY" if not problems else f"NOT READY: {len(problems)} line(s) say CHECK")
