# Lab 3, step 5: prepared fix proposals

Use this file when GitHub Copilot is not available, or to compare with the fix that you got.
For each of the three causes there are three candidate fixes, written for this workshop in the
style of an assistant. Each candidate comes with a plausible argument. **One candidate for each
cause corrects the cause.** The other two hide the symptom, change the judge, or change nothing
that matters.

**Your task:** choose one candidate for each cause before you apply anything, and say in one
sentence why each of the other two is wrong. Then apply your choice by hand, run the affected
tests and checks, and run the full regression suite.

A fix is not judged by what turns green. It is judged against the contract, and against the three
rules of this lab: never delete, skip, or weaken a failing assertion. Never let the code define the
expected result. Compare with the fixture.

## Cause 1. The tax of a line is rounded half even, not half up

Evidence: the code tests `test_tax_rounds_half_up_on_a_tie` and
`test_tax_of_a_credit_rounds_away_from_zero_on_a_tie` fail. `tax_amount` returns 0.16 where the
contract says 0.17, and -0.16 where it says -0.17.

### Candidate 1A: Use Python's round()

> quantize without a rounding mode is easy to get wrong. The built-in round() is clearer.

`o2i/rules.py`

```diff
--- a/o2i/rules.py
+++ b/o2i/rules.py
@@ -129,3 +129,3 @@
         return Decimal("0.00")
-    return round_money(net * _as_decimal(tax_rate, "tax_rate"))
+    return round(net * _as_decimal(tax_rate, "tax_rate"), 2)
 
```

### Candidate 1B: Use the half-up helper that the module already has

> tax_amount calls round_money, which rounds with the default mode of Decimal. The contract says half up, and round_half_up does exactly that.

`o2i/rules.py`

```diff
--- a/o2i/rules.py
+++ b/o2i/rules.py
@@ -129,3 +129,3 @@
         return Decimal("0.00")
-    return round_money(net * _as_decimal(tax_rate, "tax_rate"))
+    return round_half_up(net * _as_decimal(tax_rate, "tax_rate"))
 
```

### Candidate 1C: Align the tests with the code

> The function is deterministic and has been in use. The new tests expect a rounding that the code never had. Update the expected values.

`tests/unit/test_rules.py`

```diff
--- a/tests/unit/test_rules.py
+++ b/tests/unit/test_rules.py
@@ -89,9 +89,9 @@
     def test_tax_rounds_half_up_on_a_tie(self):
-        self.assertEqual(rules.tax_amount(D("3.00"), D("0.0550")), D("0.17"))            # 0.165
-        self.assertEqual(rules.tax_amount(D("0.50"), D("0.2100")), D("0.11"))            # 0.105
-        self.assertEqual(rules.gross_amount(D("3.00"), D("0.0550")), D("3.17"))
+        self.assertEqual(rules.tax_amount(D("3.00"), D("0.0550")), D("0.16"))            # 0.165
+        self.assertEqual(rules.tax_amount(D("0.50"), D("0.2100")), D("0.10"))            # 0.105
+        self.assertEqual(rules.gross_amount(D("3.00"), D("0.0550")), D("3.16"))
 
     def test_tax_of_a_credit_rounds_away_from_zero_on_a_tie(self):
-        self.assertEqual(rules.tax_amount(D("-3.00"), D("0.0550")), D("-0.17"))          # -0.165
-        self.assertEqual(rules.gross_amount(D("-3.00"), D("0.0550")), D("-3.17"))
+        self.assertEqual(rules.tax_amount(D("-3.00"), D("0.0550")), D("-0.16"))          # -0.165
+        self.assertEqual(rules.gross_amount(D("-3.00"), D("0.0550")), D("-3.16"))
 
```

## Cause 2. Only the latest delivery of an invoice line reaches the rules

Evidence: the check `reconciliation` fails. Delivered rows are in no output, for example the
fixture rows F0017 and F0019. The check `conflicts_held` fails as well.

### Candidate 2A: Let every delivery reach the rules

> Three lines at the top of add_facts keep one delivery for each key before any rule runs. Rule R3 already decides replays and conflicts, and it needs to see every delivery. Remove the three lines.

`o2i/transform.py`

```diff
--- a/o2i/transform.py
+++ b/o2i/transform.py
@@ -53,6 +53,2 @@
                     .otherwise("UNEXPECTED"))
-
-    # A line can be delivered more than once: keep the latest delivery of each invoice line.
-    latest_first = Window.partitionBy("InvoiceID", "LineNumber").orderBy(F.col("IngestedAt").desc(), F.col("RawRowID").desc())
-    lines = lines.withColumn("delivery", F.row_number().over(latest_first)).filter("delivery = 1").drop("delivery")
 
```

### Candidate 2B: Count every invoice line once in the check

> A line that is delivered twice is still one line. The check compares delivered rows with written rows, so it reports replays as losses. Compare invoice lines instead.

`o2i/checks.py`

```diff
--- a/o2i/checks.py
+++ b/o2i/checks.py
@@ -13,3 +13,3 @@
 
-from pyspark.sql import DataFrame
+from pyspark.sql import DataFrame, Window
 from pyspark.sql import functions as F
@@ -113,5 +113,7 @@
     """Every delivered row is in exactly one output: raw = accepted + exceptions, by RawRowID."""
-    raw_n, accepted_n, exceptions_n = ctx.raw.count(), ctx.accepted.count(), ctx.exceptions.count()
+    latest_first = Window.partitionBy(*config.GRAIN).orderBy(F.col("IngestedAt").desc(), F.col("RawRowID").desc())
+    raw = ctx.raw.withColumn("delivery", F.row_number().over(latest_first)).filter("delivery = 1")
+    raw_n, accepted_n, exceptions_n = raw.count(), ctx.accepted.count(), ctx.exceptions.count()
     written = ctx.accepted.select("RawRowID").unionByName(ctx.exceptions.select("RawRowID"))
-    lost = ctx.raw.select("RawRowID").join(written, "RawRowID", "left_anti")
+    lost = raw.select("RawRowID").join(written, "RawRowID", "left_anti")
     twice = written.groupBy("RawRowID").count().filter(F.col("count") > 1)
```

### Candidate 2C: Report the older deliveries as replays

> Keep the rule that the latest delivery wins, and stop losing rows: every older delivery goes to the exception output as EXACT_REPLAY.

`o2i/transform.py`

```diff
--- a/o2i/transform.py
+++ b/o2i/transform.py
@@ -54,5 +54,5 @@
 
-    # A line can be delivered more than once: keep the latest delivery of each invoice line.
+    # A line can be delivered more than once: the latest delivery wins, older deliveries are reported as replays.
     latest_first = Window.partitionBy("InvoiceID", "LineNumber").orderBy(F.col("IngestedAt").desc(), F.col("RawRowID").desc())
-    lines = lines.withColumn("delivery", F.row_number().over(latest_first)).filter("delivery = 1").drop("delivery")
+    lines = lines.withColumn("f_older_delivery", F.row_number().over(latest_first) > 1)
 
@@ -109,2 +109,3 @@
                .when(f("f_status_class") != "POSTED", "UNEXPECTED_STATUS")         # R2
+               .when(f("f_older_delivery"), "EXACT_REPLAY")                        # R3
                .when(f("f_duplicate_class") == "CONFLICT", "CONFLICTING_DUPLICATE")  # R3
```

## Cause 3. The amount rule compares the absolute quantity

Evidence: the check `signed_amounts` fails. Valid credit lines are held as `AMOUNT_MISMATCH`, for
example the fixture row F0005, and a credit with a positive amount is accepted: F0033.

### Candidate 3A: Compare absolute values on both sides

> The right side uses the absolute quantity, the left side does not. Make both sides absolute, and credits pass.

`o2i/transform.py`

```diff
--- a/o2i/transform.py
+++ b/o2i/transform.py
@@ -97,3 +97,3 @@
     # R7: the delivered NetAmount equals Quantity x UnitPrice, rounded half up.
-    amount_ok = F.col("NetAmount") == F.round(F.abs(F.col("Quantity")) * F.col("UnitPrice"), 2)
+    amount_ok = F.abs(F.col("NetAmount")) == F.round(F.abs(F.col("Quantity")) * F.col("UnitPrice"), 2)
     facts = facts.withColumn("f_amount_ok", F.coalesce(amount_ok, F.lit(False)))
```

### Candidate 3B: Exempt credit notes from the amount rule

> The amount rule was written for invoices. Credit notes have negative values by nature, so they should not be checked by it.

`o2i/transform.py`

```diff
--- a/o2i/transform.py
+++ b/o2i/transform.py
@@ -97,3 +97,4 @@
     # R7: the delivered NetAmount equals Quantity x UnitPrice, rounded half up.
-    amount_ok = F.col("NetAmount") == F.round(F.abs(F.col("Quantity")) * F.col("UnitPrice"), 2)
+    amount_ok = ((F.col("DocumentType") == "CREDIT_NOTE")
+                 | (F.col("NetAmount") == F.round(F.abs(F.col("Quantity")) * F.col("UnitPrice"), 2)))
     facts = facts.withColumn("f_amount_ok", F.coalesce(amount_ok, F.lit(False)))
```

### Candidate 3C: Remove abs()

> Quantity carries the sign, and NetAmount has the sign of the quantity. Without abs(), a valid credit matches and a credit with a lost sign does not.

`o2i/transform.py`

```diff
--- a/o2i/transform.py
+++ b/o2i/transform.py
@@ -97,3 +97,3 @@
     # R7: the delivered NetAmount equals Quantity x UnitPrice, rounded half up.
-    amount_ok = F.col("NetAmount") == F.round(F.abs(F.col("Quantity")) * F.col("UnitPrice"), 2)
+    amount_ok = F.col("NetAmount") == F.round(F.col("Quantity") * F.col("UnitPrice"), 2)
     facts = facts.withColumn("f_amount_ok", F.coalesce(amount_ok, F.lit(False)))
```

## After you have chosen

| Cause | My choice | Why the other two are wrong |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
