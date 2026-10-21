"""The reviewed logic of Lab 1, copied from the notebook into one function.

It is correct for the scope of Lab 1: rules R2, R5, and R6 of the business contract, and the
derived amounts. It is also hard to maintain: one long function, expressions repeated inline, and
nothing that a local test can call.

Lab 2 turns this logic into a module. This file stays as it is: it is the reference of the parity
check (run_parity.py). Do not edit it.
"""
from pyspark.sql import functions as F

import lab_config


def lab1_outputs(spark, dataset):
    prefix = "fixture_" if dataset == "fixture" else ""
    source = f"`{lab_config.CATALOG}`.{lab_config.INPUT_SCHEMA}"
    inv = spark.table(f"{source}.{prefix}invoice_lines")
    cust = spark.table(f"{source}.{prefix}customers")
    prod = spark.table(f"{source}.{prefix}products")

    # Posted lines only. Compare the status trimmed and in upper case, keep the delivered value.
    inv = inv.withColumn(
        "StatusClass",
        F.when(F.upper(F.trim(F.col("Status"))) == "POSTED", "POSTED")
         .when(F.upper(F.trim(F.col("Status"))).isin("DRAFT", "CANCELLED"), "NOT_POSTED")
         .otherwise("UNEXPECTED"))

    # How many master rows has each key? Join the counts first, not the attributes.
    cust_n = cust.groupBy("CustomerID").agg(F.count(F.lit(1)).alias("CustomerMatches"))
    prod_n = prod.groupBy("ProductID").agg(F.count(F.lit(1)).alias("ProductMatches"))
    inv = inv.join(cust_n, "CustomerID", "left").join(prod_n, "ProductID", "left")
    inv = inv.withColumn("CustomerMatches", F.coalesce(F.col("CustomerMatches"), F.lit(0)))
    inv = inv.withColumn("ProductMatches", F.coalesce(F.col("ProductMatches"), F.lit(0)))

    # One reason for each row that cannot be accepted.
    inv = inv.withColumn(
        "ReasonCode",
        F.when(F.col("StatusClass") == "NOT_POSTED", "NOT_POSTED")
         .when(F.col("StatusClass") != "POSTED", "UNEXPECTED_STATUS")
         .when(F.col("CustomerMatches") == 0, "UNKNOWN_CUSTOMER")
         .when(F.col("CustomerMatches") > 1, "AMBIGUOUS_CUSTOMER")
         .when(F.col("ProductMatches") == 0, "UNKNOWN_PRODUCT")
         .when(F.col("ProductMatches") > 1, "AMBIGUOUS_PRODUCT"))
    inv = inv.withColumn(
        "Disposition",
        F.when(F.col("ReasonCode").isNull(), "ACCEPTED")
         .when(F.col("ReasonCode") == "NOT_POSTED", "EXCLUDED")
         .otherwise("QUARANTINED"))

    # Accepted lines: exactly one customer row and one product row, so these joins are safe.
    acc = inv.filter(F.col("Disposition") == "ACCEPTED")
    acc = acc.join(cust.select("CustomerID", "CustomerName", "Segment", "Country", "Region"), "CustomerID", "left")
    acc = acc.join(prod.select("ProductID", "ProductName", "ProductLine"), "ProductID", "left")
    # Tax rounded half up. No tax rate means no tax: without coalesce the amounts would be NULL.
    acc = acc.withColumn("TaxAmount", F.coalesce(F.round(F.col("NetAmount") * F.col("TaxRate"), 2), F.lit(0)).cast("decimal(18,2)"))
    acc = acc.withColumn("GrossAmount", (F.col("NetAmount") + F.col("TaxAmount")).cast("decimal(18,2)"))
    acc = acc.select("RawRowID", "InvoiceID", "LineNumber", "InvoiceDate", "DocumentType", "CustomerID",
                     "CustomerName", "Segment", "Country", "Region", "ProductID", "ProductName", "ProductLine",
                     "OrderID", "OrderLineNumber", "Quantity", "UnitPrice", "NetAmount", "TaxRate", "TaxAmount",
                     "GrossAmount", "Currency", "LoadBatchID")

    exc = inv.filter(F.col("Disposition") != "ACCEPTED")
    exc = exc.select("RawRowID", "InvoiceID", "LineNumber", "Disposition", "ReasonCode", "Status", "InvoiceDate",
                     "DocumentType", "CustomerID", "ProductID", "OrderID", "OrderLineNumber", "Quantity",
                     "UnitPrice", "NetAmount", "TaxRate", "Currency", "LoadBatchID")
    return acc, exc
