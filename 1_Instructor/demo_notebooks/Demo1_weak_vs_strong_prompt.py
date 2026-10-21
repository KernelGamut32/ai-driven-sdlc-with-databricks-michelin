# Databricks notebook source
# MAGIC %md
# MAGIC # Demo 1: Weak prompt versus strong prompt
# MAGIC
# MAGIC **Instructor notebook. 5 minutes, slide 14.** The Demo Runbook has the talk track and the timing.
# MAGIC
# MAGIC | Beat | Cell | What the room sees |
# MAGIC |---|---|---|
# MAGIC | 1 | A | A typical answer to four words. It runs without an error. |
# MAGIC | 2 | B, C | The answer is wrong by a number with seven digits, and every cause is a silent decision |
# MAGIC | 3 | | The strong prompt, in the text under "Beat 3". The assistant now lists assumptions before it writes code. |
# MAGIC
# MAGIC Cell A is a prepared response, written for this course in the style of an assistant. It is here so that
# MAGIC the numbers of the demo are the same in every delivery. Say that it is prepared when you show it.

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
# MAGIC ## Beat 1. The prompt: "Clean this invoice data"
# MAGIC
# MAGIC Type the four words into Genie Code, with `@invoice_lines` as context. While it answers, run cell A.

# COMMAND ----------

# CELL A. A typical answer to "Clean this invoice data" (prepared response)

df = spark.table("o2i.invoice_lines")

cleaned = (
    df
    # remove duplicate rows
    .dropDuplicates()
    # remove rows with missing values
    .dropna(subset=["InvoiceID", "CustomerID", "ProductID", "NetAmount"])
    # standardize the status
    .withColumn("Status", F.upper(F.trim(F.col("Status"))))
    # make the amount numeric
    .withColumn("NetAmount", F.col("NetAmount").cast("double"))
    # remove invalid negative amounts
    .filter(F.col("NetAmount") > 0)
    # fill missing tax rates
    .fillna({"TaxRate": 0.0})
)

revenue = (cleaned.groupBy("Currency")
           .agg(F.count(F.lit(1)).alias("Rows"), F.round(F.sum("NetAmount"), 2).alias("Revenue"))
           .orderBy("Currency"))
print(f"Cleaned rows: {cleaned.count():,}")
display(revenue)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Beat 2. It ran. Is it right?
# MAGIC
# MAGIC Cell B compares the answer with the validated totals of the accepted lines (business contract 1.0).
# MAGIC Cell C counts the decisions that the answer made without telling anybody.

# COMMAND ----------

# CELL B. The typical answer against the validated answer set

validated = spark.table("o2i.reference_totals").filter("Scope = 'CONTRACT_1.0'")
compared = (revenue.join(validated.select("Currency", F.col("AcceptedRows").alias("ValidatedRows"),
                                          F.col("NetAmount").alias("ValidatedRevenue")), "Currency", "left")
            .withColumn("Revenue", F.col("Revenue").cast("decimal(18,2)"))
            .withColumn("Difference", (F.col("Revenue") - F.col("ValidatedRevenue")).cast("decimal(18,2)"))
            .orderBy("Currency"))
display(compared)

eur = compared.filter("Currency = 'EUR'").first()
EUR_TYPICAL, EUR_VALIDATED, EUR_DIFFERENCE = eur["Revenue"], eur["ValidatedRevenue"], eur["Difference"]
print(f"EUR revenue, typical answer:   {EUR_TYPICAL:>16,.2f}")
print(f"EUR revenue, validated:        {EUR_VALIDATED:>16,.2f}")
print(f"Overstated by:                 {EUR_DIFFERENCE:>16,.2f}  ({EUR_DIFFERENCE / EUR_VALIDATED:.1%})")

# COMMAND ----------

# CELL C. Six decisions that nobody asked for, each with its count

raw = spark.table("o2i.invoice_lines")
status = F.upper(F.trim(F.col("Status")))
DECISIONS = {
    "duplicates_removed": raw.count() - raw.dropDuplicates().count(),
    "repeated_keys": cleaned.groupBy("InvoiceID", "LineNumber").count().filter("count > 1").count(),
    "rows_dropped_for_a_null": raw.count() - raw.dropna(subset=["InvoiceID", "CustomerID", "ProductID", "NetAmount"]).count(),
    "status_values_rewritten": raw.filter(F.col("Status").isNotNull() & (F.col("Status") != status)).count(),
    "not_posted_rows_kept": cleaned.filter(F.col("Status").isNull() | (F.col("Status") != "POSTED")).count(),
    "credit_lines_removed": raw.filter("NetAmount < 0").count(),
    "tax_rates_invented": cleaned.join(raw.filter("TaxRate IS NULL").select("RawRowID"), "RawRowID", "left_semi").count(),
}
print(f"1. dropDuplicates() removed {DECISIONS['duplicates_removed']:,} rows. Every delivered row has its own RawRowID,")
print(f"   so {DECISIONS['repeated_keys']:,} invoice lines are still in the result more than once, and count more than once.")
print(f"2. dropna() removed {DECISIONS['rows_dropped_for_a_null']:,} rows. No report says which rows, or why.")
print(f"3. The delivered Status was overwritten in {DECISIONS['status_values_rewritten']:,} rows. The evidence is gone.")
print(f"4. Nobody said 'posted lines only': {DECISIONS['not_posted_rows_kept']:,} rows that are not posted count as revenue.")
print(f"5. 'Invalid negative amounts': {DECISIONS['credit_lines_removed']:,} credit lines were removed. Credits reduce revenue.")
print(f"6. {DECISIONS['tax_rates_invented']:,} rows of the result had no tax rate. They now claim a rate of 0.0, and money became a double.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Beat 3. The strong prompt
# MAGIC
# MAGIC Start a **New chat** in Genie Code and paste the prompt below. It is the prompt of slide 14, written out.
# MAGIC Do not let it write code: the point of this beat is the list of assumptions that comes back.
# MAGIC
# MAGIC ```text
# MAGIC I need the accepted invoice lines for a revenue report, from the table @invoice_lines.
# MAGIC Do not write code yet.
# MAGIC
# MAGIC Facts about the input:
# MAGIC - One row is one delivery of an invoice line. RawRowID identifies the delivered row.
# MAGIC   InvoiceID + LineNumber identifies the invoice line, and a line can be delivered more than once.
# MAGIC - Quantity carries the sign: a credit line has a negative Quantity and a negative NetAmount.
# MAGIC - Amounts are DECIMAL. Currencies are never added together.
# MAGIC
# MAGIC Rules:
# MAGIC - Keep only posted lines. Compare Status trimmed and in upper case, and keep the delivered value.
# MAGIC - Keep the sign and the decimal precision of every amount.
# MAGIC - A line whose customer or product does not match exactly one master row is not accepted.
# MAGIC   It goes to an exception output with a reason code. No row is dropped, and no value is filled in.
# MAGIC
# MAGIC Constraints: PySpark DataFrame API or SQL only. No new libraries, no pandas, no UDFs.
# MAGIC
# MAGIC Acceptance tests that I will run:
# MAGIC - delivered rows = accepted rows + exception rows, counted by RawRowID
# MAGIC - the accepted output has one row for each InvoiceID + LineNumber
# MAGIC - the total NetAmount of each currency equals the validated total, to the cent
# MAGIC
# MAGIC First list the assumptions that you would have to make, and the questions that you have for me.
# MAGIC ```
# MAGIC
# MAGIC **Read two of its assumptions aloud. Answer one of them from the rule sheet.** Typical ones:
# MAGIC what to do with deliveries of the same line that differ, which status values exist besides POSTED,
# MAGIC whether a NULL tax rate means zero tax, and what an invalid date should become.
# MAGIC
# MAGIC Then slide 15, for one minute, and slide 16: the room repairs the weak prompt.
