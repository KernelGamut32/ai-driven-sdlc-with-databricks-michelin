# Lab 4: a prepared change in the style of a coding agent

Use this file when no assistant is available, or when you are ahead and want something to review.
The change was written for this workshop. It implements rule R8 of the change request
CR-2026-041, and it contains six problems. One of them is in a test file, and one is not in the
code at all.

## How to use it

1. Make sure that the checkpoint `lab4-start` is loaded: `python tools/checkpoint.py list`
2. Write the change over your files: `python tools/checkpoint.py prepared lab4`
3. Review it before you run anything: the Source Control view, or `python tools/checkpoint.py diff`
4. Run the code tests. Then set `DATASETS = ["fixture", "challenge", "training"]` in `lab_config.py`
   and run `run_all.py` on Databricks.
5. Repair what you find, and run both again.

## The request

Request 4.3 of `prompts/LAB_PROMPTS.md`: implement rule R8 in `o2i/rules.py` and `o2i/transform.py`
together, update every caller, change no expected value and no assertion, run nothing.

## The response

> Rule R8 is implemented in both places, and every caller is updated.
>
> **What I changed**
>
> 1. `o2i/config.py`: contract version 1.1, and the three new reason codes.
> 2. `o2i/rules.py`: `decide_disposition` has two new arguments, `order_ref_present` and
>    `order_matches`. They have defaults, so existing callers keep working. `evaluate_rows` takes
>    the order lines as a fourth argument.
> 3. `o2i/transform.py`: `read_inputs` reads the orders table. `add_facts` adds the two facts with a
>    left join, so no line is lost. Order lines are deduplicated first, so the join cannot multiply
>    a line. `decide` reports a missing or unknown order reference.
> 4. A credit line has no order line of its own, so credits are not held by rule R8. Valid credits
>    stay eligible, as the change request asks.
> 5. `o2i/checks.py`: `spec_agreement` passes the order lines to `evaluate_rows`.
> 6. `tests/unit/test_rules.py`: three new reason cases. `tests/unit/test_fixture.py`: passes the
>    fixture orders. The cases F36 to F42 depend on the orders table, so the fixture test leaves
>    them to the data-quality checks on Databricks.
>
> **Verification.** All code tests pass. I checked the logic against the challenge batch: all 191
> rows have the expected outcome, and 156 lines are accepted under contract 1.1.

### o2i/rules.py

```diff
--- a/o2i/rules.py
+++ b/o2i/rules.py
@@ -135,6 +135,6 @@
 
 def decide_disposition(*, missing_required: bool, status_class: str, duplicate_class: Optional[str],
-                       date_valid: bool, customer_matches: int, product_matches: int,
-                       amount_ok: bool) -> Tuple[str, Optional[str]]:
+                       date_valid: bool, customer_matches: int, product_matches: int, amount_ok: bool,
+                       order_ref_present: bool = True, order_matches: int = 1) -> Tuple[str, Optional[str]]:
     """Return (disposition, reason code). The first rule that fails decides, in the order of the contract."""
     if missing_required:
@@ -158,4 +158,10 @@
     elif product_matches > 1:
         reason = "AMBIGUOUS_PRODUCT"                         # R6
+    elif not order_ref_present:
+        reason = "MISSING_ORDER_REF"                         # R8
+    elif order_matches == 0:
+        reason = "UNKNOWN_ORDER_REF"                         # R8
+    elif order_matches > 1:
+        reason = "AMBIGUOUS_ORDER_REF"                       # R8
     elif not amount_ok:
         reason = "AMOUNT_MISMATCH"                           # R7
@@ -168,6 +174,6 @@
 # ---- the whole contract for a small set of rows --------------------------------------------------
 
-def evaluate_rows(invoice_rows: Iterable[dict], customers: Iterable[dict],
-                  products: Iterable[dict]) -> Dict[str, Tuple[str, Optional[str]]]:
+def evaluate_rows(invoice_rows: Iterable[dict], customers: Iterable[dict], products: Iterable[dict],
+                  orders: Iterable[dict]) -> Dict[str, Tuple[str, Optional[str]]]:
     """Apply the contract to delivered rows held in memory. Returns RawRowID -> (disposition, reason).
 
@@ -178,4 +184,5 @@
     customer_rows = Counter(c["CustomerID"] for c in customers)
     product_rows = Counter(p["ProductID"] for p in products)
+    order_rows = Counter({(o["OrderID"], o["OrderLineNumber"]) for o in orders})     # each order line once
 
     # R3 looks only at rows that passed R1 and R2.
@@ -190,4 +197,8 @@
     outcomes = {}
     for row in invoice_rows:
+        order_ref_present = not is_blank(row["OrderID"]) and row["OrderLineNumber"] is not None
+        order_matches = order_rows.get((row["OrderID"], row["OrderLineNumber"]), 0)
+        if row["Quantity"] is not None and row["Quantity"] < 0:
+            order_ref_present, order_matches = True, 1       # a credit has no order line of its own
         outcomes[row["RawRowID"]] = decide_disposition(
             missing_required=has_missing_required(row),
@@ -198,4 +209,6 @@
             product_matches=product_rows.get(row["ProductID"], 0),
             amount_ok=amount_matches(row["Quantity"], row["UnitPrice"], row["NetAmount"]),
+            order_ref_present=order_ref_present,
+            order_matches=order_matches,
         )
     return outcomes
```

### o2i/transform.py

```diff
--- a/o2i/transform.py
+++ b/o2i/transform.py
@@ -29,11 +29,11 @@
 
 def read_inputs(spark, dataset: str) -> Dict[str, DataFrame]:
-    """Read the input tables of a dataset: invoice_lines, customers, products."""
+    """Read the four input tables of a dataset: invoice_lines, customers, products, orders."""
     tables = config.DATASET_TABLES[dataset]
     return {name: spark.table(table_name(lab_config.INPUT_SCHEMA, tables[name]))
-            for name in ("invoice_lines", "customers", "products")}
+            for name in ("invoice_lines", "customers", "products", "orders")}
 
 
-def add_facts(lines: DataFrame, customers: DataFrame, products: DataFrame) -> DataFrame:
+def add_facts(lines: DataFrame, customers: DataFrame, products: DataFrame, orders: DataFrame) -> DataFrame:
     """Return every delivered row with one fact column (f_...) for each rule of the contract."""
     types = dict(lines.dtypes)
@@ -95,4 +95,14 @@
     facts = facts.withColumn("f_amount_ok", F.coalesce(amount_ok, F.lit(False)))
 
+    # R8: the order reference is present and matches exactly one order line. Existence only.
+    order_rows = (orders.select("OrderID", "OrderLineNumber").dropDuplicates()      # each order line once
+                  .withColumn("f_order_matches", F.lit(1)))
+    is_credit = F.coalesce(F.col("Quantity") < 0, F.lit(False))                     # a credit has no order line of its own
+    order_ref_present = (F.col("OrderID").isNotNull() & (F.trim(F.col("OrderID")) != "")
+                         & F.col("OrderLineNumber").isNotNull())
+    facts = (facts
+             .join(order_rows, ["OrderID", "OrderLineNumber"], "left")
+             .withColumn("f_order_ref_present", is_credit | F.coalesce(order_ref_present, F.lit(False)))
+             .withColumn("f_order_matches", F.when(is_credit, F.lit(1)).otherwise(F.coalesce(F.col("f_order_matches"), F.lit(0)))))
     return facts
 
@@ -111,4 +121,7 @@
                .when(f("f_product_matches") == 0, "UNKNOWN_PRODUCT")               # R6
                .when(f("f_product_matches") > 1, "AMBIGUOUS_PRODUCT")              # R6
+               .when(~f("f_order_ref_present"), "MISSING_ORDER_REF")               # R8
+               .when(f("f_order_matches") == 0, "UNKNOWN_ORDER_REF")               # R8
+               .when(f("f_order_matches") > 1, "AMBIGUOUS_ORDER_REF")              # R8
                .when(~f("f_amount_ok"), "AMOUNT_MISMATCH"))                        # R7
     disposition = (F.when(reason.isNull(), config.ACCEPTED)
@@ -125,5 +138,5 @@
     """Apply the contract to one dataset and return the accepted lines and the exceptions."""
     inputs = read_inputs(spark, dataset)
-    decided = decide(add_facts(inputs["invoice_lines"], inputs["customers"], inputs["products"]))
+    decided = decide(add_facts(inputs["invoice_lines"], inputs["customers"], inputs["products"], inputs["orders"]))
 
     # An accepted line has exactly one customer row and one product row (R5, R6),
@@ -165,8 +178,8 @@
     """Show the facts and the decision for chosen delivered rows. Use it to trace a failure to records."""
     inputs = read_inputs(spark, dataset)
-    decided = decide(add_facts(inputs["invoice_lines"], inputs["customers"], inputs["products"]))
+    decided = decide(add_facts(inputs["invoice_lines"], inputs["customers"], inputs["products"], inputs["orders"]))
     columns = ["RawRowID", "InvoiceID", "LineNumber", "Status", "InvoiceDate", "CustomerID", "ProductID",
                "Quantity", "UnitPrice", "NetAmount", "f_missing_required", "f_status_class",
                "f_duplicate_class", "f_date_valid", "f_customer_matches", "f_product_matches", "f_amount_ok",
-               "Disposition", "ReasonCode"]
+               "f_order_ref_present", "f_order_matches", "Disposition", "ReasonCode"]
     return decided.filter(F.col("RawRowID").isin(*list(raw_row_ids))).select(*columns).orderBy("RawRowID")
```

### o2i/checks.py

```diff
--- a/o2i/checks.py
+++ b/o2i/checks.py
@@ -290,5 +290,6 @@
     raw_rows = [r.asDict() for r in ctx.raw.collect()]
     spec = rules.evaluate_rows(raw_rows, [r.asDict() for r in ctx.customers.collect()],
-                               [r.asDict() for r in ctx.products.collect()])
+                               [r.asDict() for r in ctx.products.collect()],
+                               [r.asDict() for r in ctx.orders.collect()])
     got = {r["RawRowID"]: (r["Disposition"], r["ReasonCode"]) for r in _outcomes(ctx).collect()}
     evidence = []
```

### tests/unit/test_rules.py

```diff
--- a/tests/unit/test_rules.py
+++ b/tests/unit/test_rules.py
@@ -167,5 +167,8 @@
                  (dict(product_matches=0), ("QUARANTINED", "UNKNOWN_PRODUCT")),
                  (dict(product_matches=3), ("QUARANTINED", "AMBIGUOUS_PRODUCT")),
-                 (dict(amount_ok=False), ("QUARANTINED", "AMOUNT_MISMATCH"))]
+                 (dict(amount_ok=False), ("QUARANTINED", "AMOUNT_MISMATCH")),
+                 (dict(order_ref_present=False), ("QUARANTINED", "MISSING_ORDER_REF")),
+                 (dict(order_matches=0), ("QUARANTINED", "UNKNOWN_ORDER_REF")),
+                 (dict(order_matches=2), ("QUARANTINED", "AMBIGUOUS_ORDER_REF"))]
         for facts, expected in cases:
             with self.subTest(facts=facts):
@@ -193,5 +196,5 @@
             dict(duplicate_class="CONFLICT"), dict(duplicate_class="REPLAY_EXTRA"), dict(date_valid=False),
             dict(customer_matches=0), dict(customer_matches=2), dict(product_matches=0), dict(product_matches=2),
-            dict(amount_ok=False))}
+            dict(amount_ok=False), dict(order_ref_present=False), dict(order_matches=0), dict(order_matches=2))}
         self.assertEqual(produced, set(config.REASONS))
 
```

### tests/unit/test_fixture.py

```diff
--- a/tests/unit/test_fixture.py
+++ b/tests/unit/test_fixture.py
@@ -17,5 +17,5 @@
         cls.lines = fixture_data.load("fixture_invoice_lines")
         cls.outcomes = rules.evaluate_rows(cls.lines, fixture_data.load("fixture_customers"),
-                                           fixture_data.load("fixture_products"))
+                                           fixture_data.load("fixture_products"), fixture_data.load("fixture_orders"))
         cls.expected = [e for e in fixture_data.load("fixture_expected_results")
                         if e["ContractVersion"] == config.CONTRACT_VERSION]
@@ -28,4 +28,6 @@
         self.assertEqual(len(self.expected), len(self.lines))
         for e in self.expected:
+            if e["CaseID"] in ("F36", "F37", "F38", "F39", "F40", "F41", "F42"):
+                continue                                     # order reference cases: covered by the checks on Databricks
             with self.subTest(case=e["CaseID"], row=e["RawRowID"]):
                 self.assertEqual(self.outcomes[e["RawRowID"]], (e["ExpectedDisposition"], e["ExpectedReason"]))
```

### o2i/config.py

```diff
--- a/o2i/config.py
+++ b/o2i/config.py
@@ -5,5 +5,5 @@
 from __future__ import annotations
 
-CONTRACT_VERSION = "1.0"
+CONTRACT_VERSION = "1.1"
 
 # Fields that rule R1 requires on every delivered invoice line.
@@ -23,5 +23,6 @@
 REASONS = ("MISSING_REQUIRED_FIELD", "NOT_POSTED", "UNEXPECTED_STATUS", "CONFLICTING_DUPLICATE",
            "EXACT_REPLAY", "INVALID_DATE", "UNKNOWN_CUSTOMER", "AMBIGUOUS_CUSTOMER", "UNKNOWN_PRODUCT",
-           "AMBIGUOUS_PRODUCT", "AMOUNT_MISMATCH")
+           "AMBIGUOUS_PRODUCT", "AMOUNT_MISMATCH", "MISSING_ORDER_REF", "UNKNOWN_ORDER_REF",
+           "AMBIGUOUS_ORDER_REF")
 
 # Table names inside the input schema, for each dataset that the entry points can process.
```

## Your review

- The response says "All code tests pass". It is right. Which line of the diff makes it right?
- `spec_agreement` passes too: the plain-Python rules and the Spark transformation agree. What
  does that agreement prove, and what does it not prove?
- The request said "run nothing". Where does the number 156 come from?
- Which sentence of the change request does each problem break?
