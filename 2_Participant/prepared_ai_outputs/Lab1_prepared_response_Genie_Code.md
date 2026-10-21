# Lab 1: prepared responses in the style of Genie Code

Use this file when Genie Code is not available, or when you are ahead and want something to review.
The three responses were written for this workshop. They are plausible, they run, and together they
contain five problems.

For each task:

1. Read the response and answer the three review questions of the notebook.
2. Paste the code into the task cell, in place of the line that says `TODO`.
3. Run the cell, then the check cell below it.
4. Repair what the check reports, and run both cells again.

## Task 1

**The request** is the one in the notebook: keep every delivered row, add `StatusClass`,
`TaxAmount`, and `GrossAmount`.

**The response**

> I added the three columns and kept all rows. The status is compared in upper case, so `Posted`
> and `posted` count as posted. The delivered `Status` column is not changed. The tax is rounded
> to two decimals with `round`, which rounds half up in Spark, and both amounts are cast to
> `DECIMAL(18,2)`.

```python
# TASK 1. Every delivered row, plus three facts. Nothing is filtered here.
status = F.upper(F.col("Status"))

prepared = (lines
            .withColumn("StatusClass",
                        F.when(status == "POSTED", "POSTED")
                         .when(status.isin("DRAFT", "CANCELLED"), "NOT_POSTED")
                         .otherwise("UNEXPECTED"))
            .withColumn("TaxAmount", F.round(F.col("NetAmount") * F.col("TaxRate"), 2).cast("decimal(18,2)"))
            .withColumn("GrossAmount", (F.col("NetAmount") + F.col("TaxAmount")).cast("decimal(18,2)")))
```

## Task 2

**The request** is the reference request of the workbook: count the master rows of every key, one
row out for each row in.

**The response**

> I aggregate each master table to one row for each key and join the counts with left joins, so
> no invoice line is lost or multiplied. A key without a master row gets 0. To make the match
> robust, I compare the keys without surrounding spaces and without regard to case.

```python
# TASK 2. How many master rows has each key? One row out for each row in.
customer_rows = (customers.groupBy(F.upper(F.trim(F.col("CustomerID"))).alias("customer_key"))
                 .agg(F.count(F.lit(1)).alias("CustomerMatches")))
product_rows = (products.groupBy(F.upper(F.trim(F.col("ProductID"))).alias("product_key"))
                .agg(F.count(F.lit(1)).alias("ProductMatches")))

matched = (prepared
           .join(customer_rows, F.upper(F.trim(prepared["CustomerID"])) == customer_rows["customer_key"], "left")
           .join(product_rows, F.upper(F.trim(prepared["ProductID"])) == product_rows["product_key"], "left")
           .drop("customer_key", "product_key")
           .fillna(0, subset=["CustomerMatches", "ProductMatches"]))
```

## Task 3

**The request** is the one in the notebook: one reason for each row in the order of the rules, a
disposition, then `accepted` and `exceptions`.

**The response**

> `decided` has one reason for each row that cannot be accepted. Master data problems are the most
> serious ones, so I check them first. `accepted` holds the accepted lines with their customer and
> product attributes. `exceptions` holds the rows that somebody has to look at: lines that are
> excluded because they are not posted are correct as they are, so they are not exceptions.

```python
# TASK 3. Decide once, then split.
reason = (F.when(F.col("CustomerMatches") == 0, "UNKNOWN_CUSTOMER")
           .when(F.col("CustomerMatches") > 1, "AMBIGUOUS_CUSTOMER")
           .when(F.col("ProductMatches") == 0, "UNKNOWN_PRODUCT")
           .when(F.col("ProductMatches") > 1, "AMBIGUOUS_PRODUCT")
           .when(F.col("StatusClass") == "NOT_POSTED", "NOT_POSTED")
           .when(F.col("StatusClass") == "UNEXPECTED", "UNEXPECTED_STATUS"))

decided = (matched
           .withColumn("ReasonCode", reason)
           .withColumn("Disposition",
                       F.when(F.col("ReasonCode").isNull(), "ACCEPTED")
                        .when(F.col("ReasonCode") == "NOT_POSTED", "EXCLUDED")
                        .otherwise("QUARANTINED")))

accepted = (decided.filter(F.col("Disposition") == "ACCEPTED")
            .join(customers.select("CustomerID", "CustomerName", "Segment", "Country", "Region"), "CustomerID", "left")
            .join(products.select("ProductID", "ProductName", "ProductLine"), "ProductID", "left"))
exceptions = decided.filter(F.col("Disposition") == "QUARANTINED")
```

## When you have found the five problems

For each one, say which sentence of the rule sheet it breaks, and which check reported it. Then
ask yourself which of the five you would have found by reading alone.
