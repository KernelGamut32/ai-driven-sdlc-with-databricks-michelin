# Databricks notebook source
# MAGIC %md
# MAGIC # 01 Provision: one output schema for each participant
# MAGIC
# MAGIC **Instructor notebook. Run it once for each cohort, after `00_setup_training_data`.**
# MAGIC
# MAGIC Every participant writes the output tables of Labs 2 to 4 to a schema of their own, named `o2i_` followed
# MAGIC by the part of the sign-in name before the @, in lower case, with every other character replaced by `_`.
# MAGIC Example: `Marie.Dupont@example.com` writes to `o2i_marie_dupont`. The project derives the same name
# MAGIC (`o2i/session.py`), so nobody has to type it.
# MAGIC
# MAGIC | Action (widget 3) | What it does |
# MAGIC |---|---|
# MAGIC | `preview` | Shows the schema name of every participant. Changes nothing. Start here. |
# MAGIC | `provision` | Creates the schemas, grants each participant the right to create and change tables in their own schema, and grants read access to the training tables and to the landing volume |
# MAGIC | `grant create schema` | Alternative when you do not have the list of sign-in names: lets a group create schemas in the catalog. Each participant then creates the schema with the smoke test notebook. |
# MAGIC | `drop` | Removes the output schemas of the listed participants with everything in them. For the reset between two cohorts. Needs the word `DROP` in widget 5. |
# MAGIC
# MAGIC You need to own the catalog or to have `CREATE SCHEMA` on it, and you must be allowed to grant on the
# MAGIC training schema: you are, when you ran notebook 00 yourself.

# COMMAND ----------

DEFAULT_CATALOG = "o2iworkshop"  # written by tools/prepare_cohort.py

dbutils.widgets.text("catalog", DEFAULT_CATALOG, "1. Catalog")
dbutils.widgets.text("participants", "", "2. Sign-in names, separated by commas or spaces")
dbutils.widgets.dropdown("action", "preview", ["preview", "provision", "grant create schema", "drop"], "3. Action")
dbutils.widgets.text("group", "", "4. Group (for 'grant create schema', optional for 'provision')")
dbutils.widgets.text("confirm", "", "5. Type DROP to confirm the action 'drop'")

import re

CATALOG = dbutils.widgets.get("catalog").strip()
ACTION = dbutils.widgets.get("action")
GROUP = dbutils.widgets.get("group").strip()
CONFIRM = dbutils.widgets.get("confirm").strip()
INPUT_SCHEMA = "o2i"
PARTICIPANTS = []
for name in re.split(r"[,;\s]+", dbutils.widgets.get("participants").strip()):
    if name and name.lower() not in [p.lower() for p in PARTICIPANTS]:      # a name that is listed twice counts once
        PARTICIPANTS.append(name)


def schema_for(sign_in_name: str) -> str:
    """The same rule as o2i/session.py in the project."""
    return "o2i_" + re.sub(r"[^a-z0-9]+", "_", sign_in_name.split("@")[0].lower()).strip("_")


plan = [(p, schema_for(p)) for p in PARTICIPANTS]
print(f"Catalog: {CATALOG}    Action: {ACTION}    Participants: {len(plan)}")
for sign_in_name, schema in plan:
    print(f"  {sign_in_name:45s} -> {CATALOG}.{schema}")

names = [schema for _, schema in plan]
clashes = sorted({s for s in names if names.count(s) > 1})
if clashes:
    raise Exception(f"Two sign-in names lead to the same schema: {', '.join(clashes)}. "
                    "Give one of these participants the name of their schema, and set OUTPUT_SCHEMA in their lab_config.py.")
if INPUT_SCHEMA in names:
    raise Exception("A participant schema would be named like the training schema. Check the list.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run the action

# COMMAND ----------

def run(statement: str) -> None:
    spark.sql(statement)
    print("  " + statement)


if ACTION == "preview":
    print("Preview only. Nothing was changed. Set widget 3 to 'provision' and run the notebook again.")

elif ACTION == "provision":
    if not plan:
        raise Exception("Enter the sign-in names of the participants in widget 2.")
    for sign_in_name, schema in plan:
        print(sign_in_name)
        run(f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{schema}` COMMENT 'O2I workshop: output tables of one participant'")
        run(f"GRANT USE CATALOG ON CATALOG `{CATALOG}` TO `{sign_in_name}`")
        run(f"GRANT USE SCHEMA, CREATE TABLE, SELECT, MODIFY ON SCHEMA `{CATALOG}`.`{schema}` TO `{sign_in_name}`")
        run(f"GRANT USE SCHEMA, SELECT, READ VOLUME ON SCHEMA `{CATALOG}`.`{INPUT_SCHEMA}` TO `{sign_in_name}`")
    if GROUP:
        print(GROUP)
        run(f"GRANT USE CATALOG ON CATALOG `{CATALOG}` TO `{GROUP}`")
        run(f"GRANT USE SCHEMA, SELECT, READ VOLUME ON SCHEMA `{CATALOG}`.`{INPUT_SCHEMA}` TO `{GROUP}`")
    print(f"\nPROVISIONED: {len(plan)} schemas")

elif ACTION == "grant create schema":
    if not GROUP:
        raise Exception("Enter the group of the participants in widget 4.")
    run(f"GRANT USE CATALOG, CREATE SCHEMA ON CATALOG `{CATALOG}` TO `{GROUP}`")
    run(f"GRANT USE SCHEMA, SELECT, READ VOLUME ON SCHEMA `{CATALOG}`.`{INPUT_SCHEMA}` TO `{GROUP}`")
    print(f"\nGRANTED: members of {GROUP} can create their own schema. The smoke test notebook creates it.")

elif ACTION == "drop":
    if CONFIRM != "DROP":
        raise Exception("The action 'drop' removes schemas and tables. Type DROP in widget 5 to confirm.")
    if not plan:
        raise Exception("Enter the sign-in names of the participants in widget 2.")
    for sign_in_name, schema in plan:
        run(f"DROP SCHEMA IF EXISTS `{CATALOG}`.`{schema}` CASCADE")
    print(f"\nDROPPED: {len(plan)} schemas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## What exists now
# MAGIC
# MAGIC The output schemas of the workshop in this catalog. Run this cell at any time.

# COMMAND ----------

existing = [r[0] for r in spark.sql(f"SHOW SCHEMAS IN `{CATALOG}` LIKE 'o2i_*'").collect()]
print(f"{len(existing)} output schemas in {CATALOG}:")
for schema in sorted(existing):
    tables = spark.sql(f"SHOW TABLES IN `{CATALOG}`.`{schema}`").filter("NOT isTemporary").count()
    print(f"  {schema:40s} {tables} tables")
