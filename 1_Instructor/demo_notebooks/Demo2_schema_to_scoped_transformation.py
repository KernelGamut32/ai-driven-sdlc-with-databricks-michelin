# Databricks notebook source
# MAGIC %md
# MAGIC # Demo 2: From schema to a scoped transformation
# MAGIC
# MAGIC **Instructor notebook. 12 minutes, slides 20 and 21, with slide 10 for the reveal.** The Demo Runbook has the
# MAGIC talk track, the timing, and the cut line.
# MAGIC
# MAGIC | Beat | Minutes | Cells | What the room sees |
# MAGIC |---|---|---|---|
# MAGIC | 1 Inspect | 2 | A | Three facts that no prompt contained |
# MAGIC | 2 The inherited draft | 3 | B, C, D | Rows in equal rows out, and the result is wrong |
# MAGIC | 3 Generate | 4 | E, F | One scoped SQL step from Genie Code, reviewed before it runs, then proven |
# MAGIC | 4 Translate | 2 | G, H, I | One expression in PySpark. Same syntax family, different meaning, found by comparison |
# MAGIC | 5 Review | 1 | | Joins, types, signed amounts, output grain. Then Lab 1. |
# MAGIC
# MAGIC Cells marked **prepared** hold what you would otherwise generate live. Use them when the assistant is
# MAGIC slow or not available, and say that you are doing so.

# COMMAND ----------

# SETUP. Run before the session.
from pyspark.sql import functions as F

DEFAULT_CATALOG = "o2iworkshop"  # written by tools/prepare_cohort.py

dbutils.widgets.text("catalog", DEFAULT_CATALOG, "Catalog")
CATALOG = dbutils.widgets.get("catalog").strip()
spark.catalog.setCurrentCatalog(CATALOG)       # the cells below say o2i.<table>
print(f"Catalog {CATALOG}: {spark.table('o2i.invoice_lines').count():,} delivered invoice lines")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Beat 1. Inspect: facts first
# MAGIC
# MAGIC Before this cell, open **Catalog** > `o2i` > `invoice_lines` and read the table comment aloud: it states
# MAGIC the grain. Then run cell A. It answers the two questions that you asked the room at slide 20.

# COMMAND ----------

# CELL A. Three facts
lines = spark.table("o2i.invoice_lines")

print("1. Status, as delivered")
status_rows = lines.groupBy("Status").count().orderBy(F.desc("count"), "Status").collect()
for r in status_rows:
    print(f"     {('NULL' if r['Status'] is None else repr(r['Status'])):14} {r['count']:>7,}")
posted_spellings = [r for r in status_rows if r["Status"] is not None and r["Status"].strip().upper() == "POSTED"]
print(f"   {len(status_rows)} values. {len(posted_spellings)} of them mean 'posted'.")

print("\n2. Master keys with more than one row")
for master, key in (("customers", "CustomerID"), ("products", "ProductID")):
    repeated = spark.table(f"o2i.{master}").groupBy(key).count().filter("count > 1").count()
    print(f"     {master:10} {repeated:>3} keys")

print("\n3. Signs and missing values")
print(f"     {lines.filter('Quantity < 0').count():>6,} rows with a negative Quantity")
print(f"     {lines.filter('TaxRate IS NULL').count():>6,} rows without a TaxRate")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Beat 2. The inherited draft
# MAGIC
# MAGIC This is the transformation that the squad inherited. It is plausible, it is short, and it runs.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- CELL B. The inherited draft
# MAGIC CREATE OR REPLACE TEMP VIEW inherited_draft AS
# MAGIC SELECT i.RawRowID, i.InvoiceID, i.LineNumber, i.InvoiceDate,
# MAGIC        i.CustomerID, c.CustomerName, c.Segment, c.Country,
# MAGIC        i.ProductID, p.ProductName, p.ProductLine,
# MAGIC        i.Quantity, i.UnitPrice, i.NetAmount, i.TaxRate,
# MAGIC        i.NetAmount * (1 + i.TaxRate) AS GrossAmount,
# MAGIC        i.Currency
# MAGIC FROM o2i.invoice_lines i
# MAGIC JOIN o2i.customers c ON i.CustomerID = c.CustomerID
# MAGIC JOIN o2i.products  p ON i.ProductID  = p.ProductID
# MAGIC WHERE i.Status = 'POSTED'

# COMMAND ----------

# MAGIC %sql
# MAGIC -- CELL C. The check that most teams run: rows in, rows out
# MAGIC SELECT (SELECT count(*) FROM o2i.invoice_lines WHERE Status = 'POSTED') AS posted_rows_in,
# MAGIC        (SELECT count(*) FROM inherited_draft)                           AS rows_out

# COMMAND ----------

# MAGIC %md
# MAGIC **Pause here.** Ask: "Rows in equal rows out. Who signs off?" Then run cell D, and show slide 10.

# COMMAND ----------

# CELL D. The proof: compare keys, not counts
posted = spark.table("o2i.invoice_lines").filter("Status = 'POSTED'")
draft = spark.table("inherited_draft")

vanished = posted.join(draft.select("RawRowID").distinct(), "RawRowID", "left_anti")
copies = draft.groupBy("RawRowID").count().filter("count > 1")
invented_rows = draft.count() - draft.select("RawRowID").distinct().count()
variants = spark.table("o2i.invoice_lines").filter("Status <> 'POSTED' AND upper(trim(Status)) = 'POSTED'")

DRAFT = {
    "posted_rows_in": posted.count(),
    "rows_out": draft.count(),
    "lines_that_vanished": vanished.count(),
    "rows_that_nobody_delivered": invented_rows,
    "lines_with_copies": copies.count(),
    "gross_amount_is_null": draft.filter("GrossAmount IS NULL").count(),
    "posted_lines_never_considered": variants.count(),
    "gross_amount_type": dict(draft.dtypes)["GrossAmount"],
}
print(f"Posted rows in:   {DRAFT['posted_rows_in']:>7,}")
print(f"Rows out:         {DRAFT['rows_out']:>7,}     the count agrees")
print()
print(f"{DRAFT['lines_that_vanished']:>6,} delivered lines are not in the result. The inner joins dropped every line")
print("       whose customer or product has no master row. No report says so.")
print(f"{DRAFT['rows_that_nobody_delivered']:>6,} rows of the result were never delivered. {DRAFT['lines_with_copies']:,} lines met a master key with more")
print("       than one row, and each of them is in the result once for every master row.")
print(f"{DRAFT['gross_amount_is_null']:>6,} rows have no GrossAmount: NULL TaxRate, and NULL x anything is NULL.")
print(f"{DRAFT['posted_lines_never_considered']:>6,} posted lines never entered: 'Posted ', ' POSTED', 'posted' are not = 'POSTED'.")
print(f"       GrossAmount has the type {DRAFT['gross_amount_type']}: nobody rounded it.")
print()
print("Two errors of the same size hid each other. The code ran. That is not evidence.")

# Evidence 1: delivered lines that vanished.
display(vanished.select("RawRowID", "InvoiceID", "LineNumber", "CustomerID", "ProductID", "NetAmount", "Currency").orderBy("RawRowID").limit(5))

# Evidence 2: delivered lines that are in the result twice, once in each of two customer segments.
two_segments = (spark.table("o2i.customers").groupBy("CustomerID").agg(F.countDistinct("Segment").alias("segments"))
                .filter("segments > 1"))
display(draft.join(two_segments, "CustomerID", "left_semi")
        .select("RawRowID", "InvoiceID", "LineNumber", "CustomerID", "CustomerName", "Segment", "NetAmount", "Currency")
        .orderBy("RawRowID", "Segment").limit(4))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Beat 3. Generate one scoped step, and review it before it runs
# MAGIC
# MAGIC The draft fails at the joins. Ask Genie Code for the one step that makes a join safe, and nothing else.
# MAGIC Paste this request. In the approval prompt, read aloud what the assistant wants to do before you select
# MAGIC **Allow**.
# MAGIC
# MAGIC ```text
# MAGIC Write one SQL statement in a new cell, and do not run it.
# MAGIC Create a temporary view named guarded: every row of o2i.invoice_lines, unchanged, plus two columns.
# MAGIC CustomerMatches is the number of rows in o2i.customers with exactly this CustomerID, 0 when there is
# MAGIC none. ProductMatches is the same for o2i.products and ProductID.
# MAGIC The view must have exactly one row for each row of o2i.invoice_lines. Aggregate each master table to
# MAGIC one row for each key before you join it. Do not filter, and do not trim or change a key.
# MAGIC Before the statement, list the assumptions that you made.
# MAGIC ```
# MAGIC
# MAGIC **Review with the room, before anything runs:** which join type, what is joined, what a key without a
# MAGIC master row gets, and what the grain of the result is.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- CELL E (prepared). The scoped step: count the master rows, join the counts
# MAGIC CREATE OR REPLACE TEMP VIEW guarded AS
# MAGIC WITH customer_rows AS (
# MAGIC   SELECT CustomerID, count(*) AS CustomerMatches FROM o2i.customers GROUP BY CustomerID
# MAGIC ),
# MAGIC product_rows AS (
# MAGIC   SELECT ProductID, count(*) AS ProductMatches FROM o2i.products GROUP BY ProductID
# MAGIC )
# MAGIC SELECT i.*,
# MAGIC        coalesce(c.CustomerMatches, 0) AS CustomerMatches,
# MAGIC        coalesce(p.ProductMatches, 0)  AS ProductMatches
# MAGIC FROM o2i.invoice_lines i
# MAGIC LEFT JOIN customer_rows c ON i.CustomerID = c.CustomerID
# MAGIC LEFT JOIN product_rows  p ON i.ProductID  = p.ProductID

# COMMAND ----------

# MAGIC %sql
# MAGIC -- CELL F. Prove the step: no line lost, no line multiplied, and the problem keys are now visible
# MAGIC SELECT (SELECT count(*) FROM o2i.invoice_lines)             AS rows_in,
# MAGIC        count(*)                                             AS rows_out,
# MAGIC        count(DISTINCT RawRowID)                             AS distinct_rows_out,
# MAGIC        sum(CASE WHEN CustomerMatches = 0 THEN 1 ELSE 0 END) AS customer_unknown,
# MAGIC        sum(CASE WHEN CustomerMatches > 1 THEN 1 ELSE 0 END) AS customer_ambiguous,
# MAGIC        sum(CASE WHEN ProductMatches = 0 THEN 1 ELSE 0 END)  AS product_unknown,
# MAGIC        sum(CASE WHEN ProductMatches > 1 THEN 1 ELSE 0 END)  AS product_ambiguous
# MAGIC FROM guarded

# COMMAND ----------

# MAGIC %md
# MAGIC ## Beat 4. Translate one expression, and compare the meaning
# MAGIC
# MAGIC Cell G is the status rule in SQL. Ask Genie Code to translate only the `CASE` expression:
# MAGIC
# MAGIC ```text
# MAGIC Translate only the CASE expression of the cell "CELL G" into one PySpark column expression named
# MAGIC status_class. Do not change its meaning. Tell me what your expression returns for NULL, for a
# MAGIC status of three spaces, and for 'Posted '. Do not run anything.
# MAGIC ```
# MAGIC
# MAGIC Paste the answer into cell H in place of the prepared translation, or keep the prepared one. Then run
# MAGIC cell I. **The prepared translation has one planted difference.** Let the comparison find it.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- CELL G. The status rule in SQL (rule R2 of the business contract)
# MAGIC CREATE OR REPLACE TEMP VIEW status_sql AS
# MAGIC SELECT RawRowID, Status,
# MAGIC        CASE WHEN upper(trim(Status)) = 'POSTED' THEN 'POSTED'
# MAGIC             WHEN upper(trim(Status)) IN ('DRAFT', 'CANCELLED') THEN 'NOT_POSTED'
# MAGIC             ELSE 'UNEXPECTED' END AS StatusClass
# MAGIC FROM o2i.invoice_lines

# COMMAND ----------

# CELL H (prepared, with one planted difference). The same rule in PySpark?
status = F.upper(F.trim(F.col("Status")))
status_class = (F.when(status == "POSTED", "POSTED")
                 .when(status.isin("DRAFT", "CANCELLED"), "NOT_POSTED"))

# COMMAND ----------

# CELL I. Compare the meaning: the same rows, both results, side by side
in_sql = spark.table("status_sql").select("RawRowID", "Status", F.col("StatusClass").alias("FromSql"))
in_pyspark = spark.table("o2i.invoice_lines").select("RawRowID", status_class.alias("FromPySpark"))
differs = in_sql.join(in_pyspark, "RawRowID").filter(~F.col("FromSql").eqNullSafe(F.col("FromPySpark")))

TRANSLATION_DIFFERS = differs.count()
print(f"Rows where SQL and PySpark disagree: {TRANSLATION_DIFFERS:,}")
display(differs.groupBy("Status", "FromSql", "FromPySpark").count().orderBy(F.desc("count"), "Status"))

# COMMAND ----------

# MAGIC %md
# MAGIC **Say:** both versions read like the same rule. The SQL has an `ELSE`. The translation has no
# MAGIC `.otherwise(...)`, so every unexpected status becomes NULL, and a NULL class would later slip past a
# MAGIC condition such as `StatusClass != 'POSTED'`. Nobody finds that by reading. The comparison finds it in
# MAGIC one line.
# MAGIC
# MAGIC Fix cell H by adding `.otherwise("UNEXPECTED")`, run cells H and I again, and show zero.
# MAGIC
# MAGIC ## Beat 5. Review, then Lab 1
# MAGIC
# MAGIC | Review before execution | In this demo |
# MAGIC |---|---|
# MAGIC | Joins | Inner joins dropped lines. Joins to a non-unique key multiplied lines. Counts made both visible. |
# MAGIC | Types | `NetAmount * (1 + TaxRate)` changed the type and was never rounded |
# MAGIC | Signed amounts | Nothing removed the credits here. The typical answer of Demo 1 did. |
# MAGIC | Output grain | One row for each delivered row, proven by `count(DISTINCT RawRowID)` |
# MAGIC
# MAGIC Slide 22: the room builds the same three ideas in PySpark, in three steps, with a check after each step.
