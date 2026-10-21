# Databricks notebook source
# MAGIC %md
# MAGIC # 09 Reset: empty my output schema
# MAGIC
# MAGIC **Participant notebook. Use it when your output tables are in a state that nobody understands.**
# MAGIC It drops the tables in your own output schema, and nothing else. The training tables are not touched.
# MAGIC After the reset, run the current lab step again: every run of the project writes its tables again.
# MAGIC
# MAGIC 1. Run the first cell. It lists the tables that would be dropped.
# MAGIC 2. Set the widget **Confirm** to `yes`.
# MAGIC 3. Run the second cell.

# COMMAND ----------

import re

DEFAULT_CATALOG = "o2iworkshop"  # written by tools/prepare_cohort.py

dbutils.widgets.text("catalog", DEFAULT_CATALOG, "1. Catalog")
dbutils.widgets.dropdown("confirm", "no", ["no", "yes"], "2. Confirm")

CATALOG = dbutils.widgets.get("catalog").strip()
user = spark.sql("SELECT current_user() AS u").first()["u"]
MY_SCHEMA = "o2i_" + re.sub(r"[^a-z0-9]+", "_", user.split("@")[0].lower()).strip("_")
target = f"`{CATALOG}`.`{MY_SCHEMA}`"

tables = [r["tableName"] for r in spark.sql(f"SHOW TABLES IN {target}").collect() if not r["isTemporary"]]
print(f"Your output schema: {CATALOG}.{MY_SCHEMA}")
print(f"{len(tables)} tables:")
for name in sorted(tables):
    print(f"  {name}")

# COMMAND ----------

if dbutils.widgets.get("confirm") != "yes":
    print("Nothing was dropped. Set the widget Confirm to yes and run this cell again.")
else:
    for name in sorted(tables):
        spark.sql(f"DROP TABLE IF EXISTS {target}.`{name}`")
        print(f"dropped {name}")
    print(f"\nRESET DONE: {len(tables)} tables dropped from {CATALOG}.{MY_SCHEMA}")
