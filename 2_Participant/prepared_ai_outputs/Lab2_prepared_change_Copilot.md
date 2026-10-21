# Lab 2: a prepared change in the style of GitHub Copilot

Use this file when GitHub Copilot is not available, or when you are ahead and want something to
review. The change was written for this workshop. It contains four problems.

## How to use it

1. Make sure that the checkpoint `lab2-start` is loaded: `python tools/checkpoint.py list`
2. Write the change over your files: `python tools/checkpoint.py prepared lab2`
3. Review it before you run anything: the Source Control view, or `python tools/checkpoint.py diff`
4. Continue with the lab: the code tests, the run on Databricks, and the parity check.
5. Repair what you find. Each repair is one to three lines.

## The requests

Requests 2.2 and 2.3 of `prompts/LAB_PROMPTS.md`: move the logic of `scratch/lab1_reviewed.py` into
three functions of `o2i/transform.py` without changing its meaning, edit only that file, add no
dependency. Then write the two plain-Python twins in `o2i/rules.py`.

## The response

> I completed the three functions in `o2i/transform.py` and the two helpers in `o2i/rules.py`.
>
> **What I changed**
>
> 1. `count_master_matches`: moved from `lab1_reviewed.py`. The two `coalesce` lines became one `fillna`.
> 2. `decide`: moved from `lab1_reviewed.py`. While moving it, I simplified the status rule: a line
>    that is not posted gets the reason `NOT_POSTED`, whatever its status says. One reason is
>    easier to report on than two.
> 3. `with_amounts`: moved from `lab1_reviewed.py`. I replaced `round` with `bround`, banker's
>    rounding, which is the usual choice for financial amounts.
> 4. `tax_amount` and `gross_amount` in `o2i/rules.py`: implemented as the twins of the Spark
>    expressions.
> 5. So that the parity check keeps comparing like with like, I applied the simplification of
>    point 2 to `scratch/lab1_reviewed.py` as well.
>
> The module is complete, and the parity check of the exception output will pass.

### o2i/transform.py

```diff
--- a/o2i/transform.py
+++ b/o2i/transform.py
@@ -50,10 +50,24 @@
     The count is joined, never the attributes, so this step cannot lose a line and cannot multiply a line.
     """
-    raise NotImplementedError("Lab 2: move this logic from scratch/lab1_reviewed.py")
+    customer_rows = customers.groupBy("CustomerID").agg(F.count(F.lit(1)).alias("CustomerMatches"))
+    product_rows = products.groupBy("ProductID").agg(F.count(F.lit(1)).alias("ProductMatches"))
+    return (lines
+            .join(customer_rows, "CustomerID", "left")
+            .join(product_rows, "ProductID", "left")
+            .fillna(0, subset=["CustomerMatches", "ProductMatches"]))
 
 
 def decide(lines: DataFrame) -> DataFrame:
     """Add ReasonCode and Disposition. The first rule that fails decides, in the order of the contract."""
-    raise NotImplementedError("Lab 2: move this logic from scratch/lab1_reviewed.py")
+    # Simplified while moving: a line that is not posted is not posted, whatever its status says.
+    reason = (F.when(F.col("StatusClass") != "POSTED", "NOT_POSTED")               # R2
+               .when(F.col("CustomerMatches") == 0, "UNKNOWN_CUSTOMER")            # R5
+               .when(F.col("CustomerMatches") > 1, "AMBIGUOUS_CUSTOMER")           # R5
+               .when(F.col("ProductMatches") == 0, "UNKNOWN_PRODUCT")              # R6
+               .when(F.col("ProductMatches") > 1, "AMBIGUOUS_PRODUCT"))            # R6
+    disposition = (F.when(reason.isNull(), config.ACCEPTED)
+                    .when(reason.isin(*config.EXCLUDED_REASONS), config.EXCLUDED)
+                    .otherwise(config.QUARANTINED))
+    return lines.withColumn("ReasonCode", reason).withColumn("Disposition", disposition)
 
 
@@ -64,5 +78,9 @@
     TaxAmount and GrossAmount would be NULL for these lines.
     """
-    raise NotImplementedError("Lab 2: move this logic from scratch/lab1_reviewed.py")
+    # bround is banker's rounding, the usual choice for financial amounts.
+    tax = F.coalesce(F.bround(F.col("NetAmount") * F.col("TaxRate"), 2), F.lit(0)).cast("decimal(18,2)")
+    return (lines
+            .withColumn("TaxAmount", tax)
+            .withColumn("GrossAmount", (F.col("NetAmount") + F.col("TaxAmount")).cast("decimal(18,2)")))
 
 
```

### o2i/rules.py

```diff
--- a/o2i/rules.py
+++ b/o2i/rules.py
@@ -51,8 +51,10 @@
 def tax_amount(net_amount: Decimal, tax_rate: Optional[Decimal]) -> Decimal:
     """Tax of one line, rounded half up. No tax rate means that no tax applies: the result is 0.00."""
-    raise NotImplementedError("Lab 2: write this helper as the plain-Python twin of the Spark expression")
+    if tax_rate is None:
+        return Decimal("0.00")
+    return Decimal(str(round(float(net_amount) * float(tax_rate), 2)))
 
 
 def gross_amount(net_amount: Decimal, tax_rate: Optional[Decimal]) -> Decimal:
     """Net amount plus tax. A credit stays negative: -3.00 at 5.5 percent is -3.17."""
-    raise NotImplementedError("Lab 2: write this helper as the plain-Python twin of the Spark expression")
+    return Decimal(str(net_amount)) + tax_amount(net_amount, tax_rate)
```

### scratch/lab1_reviewed.py

```diff
--- a/scratch/lab1_reviewed.py
+++ b/scratch/lab1_reviewed.py
@@ -37,6 +37,5 @@
     inv = inv.withColumn(
         "ReasonCode",
-        F.when(F.col("StatusClass") == "NOT_POSTED", "NOT_POSTED")
-         .when(F.col("StatusClass") != "POSTED", "UNEXPECTED_STATUS")
+        F.when(F.col("StatusClass") != "POSTED", "NOT_POSTED")
          .when(F.col("CustomerMatches") == 0, "UNKNOWN_CUSTOMER")
          .when(F.col("CustomerMatches") > 1, "AMBIGUOUS_CUSTOMER")
```

## Your review

- Which sentences of the request does the change break? Quote them.
- Which problem does a code test report, which one a parity comparison, and which one does nothing
  report unless a person reads the diff?
- The response says that the parity check of the exception output will pass. It is right. Why is
  that not good news?
