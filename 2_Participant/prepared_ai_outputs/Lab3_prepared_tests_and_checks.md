# Lab 3, steps 2 and 3: prepared tests and checks in the style of GitHub Copilot

Use this file when GitHub Copilot is not available, or when you are ahead and want something to
review. The change was written for this workshop: two code tests and three data-quality checks.
It contains three problems. One test and one check are correct.

## How to use it

1. Make sure that the checkpoint `lab3-start` is loaded: `python tools/checkpoint.py list`
2. Write the change over your files: `python tools/checkpoint.py prepared lab3`
3. Review it before you run anything: the Source Control view, or `python tools/checkpoint.py diff`
4. Run the code tests, then `run_checks.py` on Databricks.
5. Compare what the tests and the checks say with what the fixture says. Where they disagree, the
   fixture was written by hand from the contract. Decide which side is wrong.

## The requests

Requests 3.2 and 3.3 of `prompts/LAB_PROMPTS.md`: write the two rounding tests with literal expected
values, and implement the three checks from their docstrings.

## The response

> **Tests.** `test_tax_rounds_half_up_on_a_tie` multiplies 3.00 by 0.0550 and rounds the product
> to two decimals, so the expected value can never drift from the input values.
> `test_tax_of_a_credit_rounds_away_from_zero_on_a_tie` asserts -0.17 and -3.17.
>
> **Checks.**
> `reconciliation` compares the delivered invoice lines with the written rows. A line can be
> delivered more than once, so I count every invoice line once.
> `conflicts_held` finds the keys that were delivered with more than one business content and
> reports accepted rows of these keys.
> `signed_amounts` counts the three kinds of rows that the docstring names.
>
> All three checks follow the style of the existing checks.

### tests/unit/test_rules.py

```diff
--- a/tests/unit/test_rules.py
+++ b/tests/unit/test_rules.py
@@ -94,5 +94,8 @@
         Take the numbers from the contract or from the fixture workbook, not from the code.
         """
-        self.skipTest("Lab 3, test 1 is not written yet")
+        net, rate = D("3.00"), D("0.0550")                    # 3.00 x 5.5 percent is exactly 0.165
+        expected_tax = round(net * rate, 2)
+        self.assertEqual(rules.tax_amount(net, rate), expected_tax)
+        self.assertEqual(rules.gross_amount(net, rate), net + expected_tax)
 
     def test_tax_of_a_credit_rounds_away_from_zero_on_a_tie(self):
@@ -102,5 +105,6 @@
         Assert the tax and the gross amount.
         """
-        self.skipTest("Lab 3, test 2 is not written yet")
+        self.assertEqual(rules.tax_amount(D("-3.00"), D("0.0550")), D("-0.17"))          # -0.165
+        self.assertEqual(rules.gross_amount(D("-3.00"), D("0.0550")), D("-3.17"))
 
     def test_amounts_have_two_decimals(self):
```

### o2i/checks.py

```diff
--- a/o2i/checks.py
+++ b/o2i/checks.py
@@ -121,5 +121,12 @@
     returns up to five keys of a DataFrame as text.
     """
-    raise NotImplementedError("reconciliation is not written yet (Lab 3, check 1)")
+    # A line can be delivered more than once, so every invoice line is counted once.
+    raw_n = ctx.raw.select(*config.GRAIN).distinct().count()
+    accepted_n, exceptions_n = ctx.accepted.count(), ctx.exceptions.count()
+    passed = raw_n == accepted_n + exceptions_n
+    summary = f"raw {raw_n:,} = accepted {accepted_n:,} + exceptions {exceptions_n:,}"
+    if not passed:
+        summary = f"raw {raw_n:,}, accepted {accepted_n:,} + exceptions {exceptions_n:,} = {accepted_n + exceptions_n:,}"
+    return CheckResult("reconciliation", passed, summary, [])
 
 
@@ -158,5 +165,15 @@
     Return CheckResult("conflicts_held", passed, summary, evidence).
     """
-    raise NotImplementedError("conflicts_held is not written yet (Lab 3, check 2)")
+    content_columns = [c for c in ctx.raw.columns if c not in config.TECHNICAL_COLUMNS]
+    content = F.sha2(F.concat_ws("|", *[F.coalesce(F.col(c).cast("string"), F.lit("")) for c in content_columns]), 256)
+    conflict_keys = (ctx.raw.withColumn("content", content)
+                     .groupBy(*config.GRAIN).agg(F.countDistinct("content").alias("versions"))
+                     .filter(F.col("versions") > 1).select(*config.GRAIN))
+    accepted_conflicts = ctx.accepted.join(conflict_keys, list(config.GRAIN), "left_semi")
+    n_keys, n = conflict_keys.count(), accepted_conflicts.count()
+    return CheckResult("conflicts_held", n == 0,
+                       f"conflicting keys delivered: {n_keys:,}; none of them accepted" if n == 0
+                       else f"conflicting keys delivered: {n_keys:,}; accepted rows of these keys: {n:,}",
+                       _keys(accepted_conflicts, ["RawRowID", *config.GRAIN]) if n else [])
 
 
@@ -215,5 +232,26 @@
     Return CheckResult("signed_amounts", passed, summary, evidence).
     """
-    raise NotImplementedError("signed_amounts is not written yet (Lab 3, check 3)")
+    sign_differs = ctx.accepted.filter((F.signum("Quantity") != F.signum("NetAmount"))
+                                       | (F.signum("NetAmount") != F.signum("GrossAmount")))
+    changed = (ctx.accepted.select("RawRowID", F.col("NetAmount").alias("written"))
+               .join(ctx.raw.select("RawRowID", F.col("NetAmount").alias("delivered")), "RawRowID")
+               .filter(F.col("written") != F.col("delivered")))
+    matches = F.col("NetAmount") == F.round(F.col("Quantity") * F.col("UnitPrice"), 2)
+    wrongly_held = ctx.exceptions.filter((F.col("ReasonCode") == "AMOUNT_MISMATCH") & matches)
+    a, b, c = sign_differs.count(), changed.count(), wrongly_held.count()
+    credits = ctx.accepted.filter(F.col("NetAmount") < 0).count()
+    evidence = []
+    if a:
+        evidence += [f"accepted with mixed signs: {k}" for k in _keys(sign_differs, ["RawRowID", "Quantity", "NetAmount"], 3)]
+    if b:
+        evidence += [f"NetAmount changed: {k}" for k in _keys(changed, ["RawRowID", "delivered", "written"], 3)]
+    if c:
+        evidence += [f"held as AMOUNT_MISMATCH although the amount matches: {k}"
+                     for k in _keys(wrongly_held, ["RawRowID", "Quantity", "UnitPrice", "NetAmount"], 3)]
+    return CheckResult("signed_amounts", a + b + c == 0,
+                       f"signs and amounts intact; accepted credit lines: {credits:,}" if a + b + c == 0
+                       else f"accepted rows with mixed signs: {a:,}; changed amounts: {b:,}; "
+                            f"matching amounts held as AMOUNT_MISMATCH: {c:,}; accepted credit lines: {credits:,}",
+                       evidence)
 
 
```

## Your review

- One test passes at once, against code that you have not repaired. What does that tell you?
- One check reports a number of delivered rows that is not the number of delivered rows. Which one?
- One check reports an accepted fixture row that the fixture expects to be accepted. Which rule
  of the contract did it leave out?
