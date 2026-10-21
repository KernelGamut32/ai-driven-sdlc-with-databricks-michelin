# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 1: Build the first reviewed transformation
# MAGIC
# MAGIC **20 minutes, in pairs. One drives, one reviews. Switch after Task 2.**
# MAGIC
# MAGIC You build the first version of the accepted invoice dataset with Genie Code, in three small steps.
# MAGIC After each step you review the proposal, run it, and let a supplied acceptance check judge the result.
# MAGIC
# MAGIC | Part | You do | Checks |
# MAGIC |---|---|---|
# MAGIC | Get ready | Run three supplied cells, read the facts, set Genie Code to **Ask first**, give it your context | |
# MAGIC | Task 1 | Keep every delivered row and add three facts: status class, tax, gross amount | C1, C2, C3 |
# MAGIC | Task 2 | Count the master rows of every customer key and product key | C4 |
# MAGIC | Task 3 | Decide one outcome for every row, then split accepted lines and exceptions | C5, C6, C7 |
# MAGIC | Prove it | Run everything on the training data | 7 of 7 |
# MAGIC | Record | Three assumptions, one expression you can explain, the open test targets | |
# MAGIC
# MAGIC **Scope of this lab:** rules R2 (status), R5 (customer), and R6 (product) of the business contract, and
# MAGIC the derived amounts. The other rules stay open on purpose. Check C6 lists what is still open.
# MAGIC
# MAGIC **The pattern you build:** facts first, one decision, split last. No step before the split filters,
# MAGIC drops, or multiplies a delivered row. That is why every check can ask: is every row still there?
# MAGIC
# MAGIC The Participant Workbook has the steps, the rule sheet, and the requests for Genie Code.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get ready
# MAGIC
# MAGIC Run the next two cells. They are supplied and you do not change them.
# MAGIC
# MAGIC 1. **Setup** reads the widgets and the input tables. The widget **Dataset** starts with `fixture`:
# MAGIC    56 delivered rows in 48 named cases, small enough to verify by hand.
# MAGIC 2. **Acceptance checks** defines the checks C1 to C7. Read it after the lab: it is a test scaffold that
# MAGIC    you can reuse.

# COMMAND ----------

# SETUP (supplied). Run this cell first, and again whenever you change the widget Dataset.
from pyspark.sql import functions as F

DEFAULT_CATALOG = "o2iworkshop"  # written by tools/prepare_cohort.py

dbutils.widgets.text("catalog", DEFAULT_CATALOG, "1. Catalog")
dbutils.widgets.dropdown("dataset", "fixture", ["fixture", "training"], "2. Dataset")

CATALOG = dbutils.widgets.get("catalog").strip()
DATASET = dbutils.widgets.get("dataset")
SOURCE = f"`{CATALOG}`.o2i"
PREFIX = "fixture_" if DATASET == "fixture" else ""

lines = spark.table(f"{SOURCE}.{PREFIX}invoice_lines")       # delivered invoice lines: one row for each RawRowID
customers = spark.table(f"{SOURCE}.{PREFIX}customers")      # customer master data
products = spark.table(f"{SOURCE}.{PREFIX}products")        # product master data

# The output columns of the business contract, in order. In this lab InvoiceDate stays text (rule R4 is open).
ACCEPTED_COLUMNS = ["RawRowID", "InvoiceID", "LineNumber", "InvoiceDate", "DocumentType", "CustomerID",
                    "CustomerName", "Segment", "Country", "Region", "ProductID", "ProductName", "ProductLine",
                    "OrderID", "OrderLineNumber", "Quantity", "UnitPrice", "NetAmount", "TaxRate", "TaxAmount",
                    "GrossAmount", "Currency", "LoadBatchID"]
EXCEPTION_COLUMNS = ["RawRowID", "InvoiceID", "LineNumber", "Disposition", "ReasonCode", "Status", "InvoiceDate",
                     "DocumentType", "CustomerID", "ProductID", "OrderID", "OrderLineNumber", "Quantity",
                     "UnitPrice", "NetAmount", "TaxRate", "Currency", "LoadBatchID"]

DELIVERED = lines.count()
print(f"Dataset '{DATASET}' from {CATALOG}.o2i")
print(f"  lines      {DELIVERED:>7,} delivered rows")
print(f"  customers  {customers.count():>7,} rows")
print(f"  products   {products.count():>7,} rows")

# COMMAND ----------

# ACCEPTANCE CHECKS (supplied). Run this cell once. Do not edit it during the lab.
#
# Each check compares your result with the business contract. The rule is written a second time here,
# in SQL, independently of your PySpark code: two implementations that agree are evidence, one is not.
# On the fixture, the checks also use the expected results that were written by hand.

RESULTS = {}


def _report(code, title, problems, info=()):
    RESULTS[code] = not problems
    print(f"{'PASS' if not problems else 'FAIL'}  {code}  {title}")
    for line in info:
        print(f"          {line}")
    for line in problems[:6]:
        print(f"       -> {line}")
    if len(problems) > 6:
        print(f"       -> and {len(problems) - 6} more")


def _guard(code, title, check, needs=()):
    """Run one check. A result that the check cannot read is a failed check, not a stack trace.

    needs: (DataFrame, name, columns) triples. A missing column fails the check with a plain message.
    """
    missing = [f"`{name}` has no column {column} yet" for df, name, columns in needs
               for column in columns if df is None or column not in df.columns]
    if missing:
        return _report(code, title, missing + ["Complete the task cell above, run it, then run this check again."])
    try:
        problems, info = check()
    except Exception as error:
        problems, info = [f"The check could not read your result: {(str(error).splitlines() or [type(error).__name__])[0][:150]}"], []
    _report(code, title, problems, info)


def _views(**frames):
    for name, df in frames.items():
        df.createOrReplaceTempView(f"lab1_{name}")


def _show(value):
    return "NULL" if value is None else f"'{value}'" if isinstance(value, str) else str(value)


RULE_STATUS = """CASE WHEN upper(trim(d.Status)) = 'POSTED' THEN 'POSTED'
                      WHEN upper(trim(d.Status)) IN ('DRAFT', 'CANCELLED') THEN 'NOT_POSTED'
                      ELSE 'UNEXPECTED' END"""
RULE_TAX = "CAST(coalesce(round(d.NetAmount * d.TaxRate, 2), 0) AS DECIMAL(18,2))"
RULE_MATCHES = """
    SELECT d.RawRowID, d.Status, d.CustomerID, d.ProductID,
           coalesce(c.n, 0) AS CustomerRule, coalesce(p.n, 0) AS ProductRule
    FROM lab1_lines d
    LEFT JOIN (SELECT CustomerID, count(*) AS n FROM lab1_customers GROUP BY CustomerID) c ON d.CustomerID = c.CustomerID
    LEFT JOIN (SELECT ProductID, count(*) AS n FROM lab1_products GROUP BY ProductID) p ON d.ProductID = p.ProductID"""
RULE_REASON = f"""
    SELECT m.RawRowID,
           CASE WHEN s.StatusRule = 'NOT_POSTED' THEN 'NOT_POSTED'
                WHEN s.StatusRule <> 'POSTED' THEN 'UNEXPECTED_STATUS'
                WHEN m.CustomerRule = 0 THEN 'UNKNOWN_CUSTOMER'
                WHEN m.CustomerRule > 1 THEN 'AMBIGUOUS_CUSTOMER'
                WHEN m.ProductRule = 0 THEN 'UNKNOWN_PRODUCT'
                WHEN m.ProductRule > 1 THEN 'AMBIGUOUS_PRODUCT' END AS ReasonRule
    FROM ({RULE_MATCHES}) m
    JOIN (SELECT d.RawRowID, {RULE_STATUS} AS StatusRule FROM lab1_lines d) s ON m.RawRowID = s.RawRowID"""
LAB1_REASONS = ("NOT_POSTED", "UNEXPECTED_STATUS", "UNKNOWN_CUSTOMER", "AMBIGUOUS_CUSTOMER", "UNKNOWN_PRODUCT",
                "AMBIGUOUS_PRODUCT")
OPEN_RULES = {"MISSING_REQUIRED_FIELD": "R1 required fields", "EXACT_REPLAY": "R3 line identity",
              "CONFLICTING_DUPLICATE": "R3 line identity", "INVALID_DATE": "R4 invoice date",
              "AMOUNT_MISMATCH": "R7 amount"}


def _same_rows(result, what):
    """Problems when a result does not have exactly one row for each delivered row."""
    shape = result.agg(F.count(F.lit(1)).alias("n"), F.countDistinct("RawRowID").alias("k")).first()
    rows, keys = shape["n"], shape["k"]
    problems = []
    if keys < DELIVERED:
        lost = lines.select("RawRowID").join(result.select("RawRowID"), "RawRowID", "left_anti").orderBy("RawRowID")
        ids = ", ".join(r[0] for r in lost.limit(4).collect())
        problems.append(f"delivered rows that are missing in {what}: {DELIVERED - keys:,}, for example {ids}")
    if rows > keys:
        twice = result.groupBy("RawRowID").count().filter("count > 1").orderBy("RawRowID")
        ids = ", ".join(r[0] for r in twice.limit(4).collect())
        problems.append(f"delivered rows that appear more than once in {what}: {twice.count():,}, for example {ids}")
    return problems, f"{DELIVERED:,} delivered rows, {rows:,} rows in {what}"


def check_task_1(prepared):
    _views(lines=lines, prepared=prepared)

    def c1():
        problems, summary = _same_rows(prepared, "prepared")
        changed = []
        names = [name for name in lines.columns if name != "RawRowID"]
        gone = [name for name in names if name not in prepared.columns]
        changed += [f"the delivered column {name} is missing in prepared" for name in gone]
        names = [name for name in names if name not in gone]
        counts = spark.sql("SELECT " + ", ".join(f"sum(CASE WHEN d.`{n}` <=> p.`{n}` THEN 0 ELSE 1 END) AS `{n}`" for n in names)
                           + " FROM lab1_lines d JOIN lab1_prepared p ON d.RawRowID = p.RawRowID").first()
        for name in names:
            if counts[name]:
                sample = spark.sql(f"SELECT d.RawRowID, d.`{name}` AS delivered, p.`{name}` AS yours FROM lab1_lines d "
                                   f"JOIN lab1_prepared p ON d.RawRowID = p.RawRowID WHERE NOT (d.`{name}` <=> p.`{name}`) "
                                   f"ORDER BY d.RawRowID LIMIT 1").first()
                changed.append(f"{name} was changed in {counts[name]:,} rows, for example {sample['RawRowID']}: delivered "
                               f"{_show(sample['delivered'])}, yours {_show(sample['yours'])}")
        return problems + changed, [summary, "delivered values are unchanged" if not changed else "a delivered value was rewritten"]

    def c2():
        rows = spark.sql(f"""SELECT d.RawRowID, d.Status, p.StatusClass AS yours, {RULE_STATUS} AS rule
                             FROM lab1_lines d JOIN lab1_prepared p ON d.RawRowID = p.RawRowID""")
        differs = rows.filter("NOT (yours <=> rule)").orderBy("RawRowID")
        problems = [f"{r['RawRowID']}: delivered status {_show(r['Status'])} is {r['rule']} by rule R2, yours says {_show(r['yours'])}"
                    for r in differs.limit(5).collect()]
        n = differs.count()
        if n > 5:
            problems.append(f"rows with a wrong StatusClass, in total: {n:,}")
        counts = {r["yours"]: r["count"] for r in rows.groupBy("yours").count().collect()}
        info = ["StatusClass: " + ", ".join(f"{k} {counts.get(k, 0):,}" for k in ("POSTED", "NOT_POSTED", "UNEXPECTED"))]
        return problems, info

    def c3():
        problems = []
        types = dict(prepared.dtypes)
        for name in ("TaxAmount", "GrossAmount"):
            if types.get(name) != "decimal(18,2)":
                problems.append(f"{name} has the type {types.get(name, 'missing')}: the contract says decimal(18,2)")
        # A row without NetAmount has no amount to judge. Rule R1 will hold such rows: an open test target.
        rows = spark.sql(f"""SELECT d.RawRowID, d.NetAmount, d.TaxRate, p.TaxAmount, p.GrossAmount,
                                    {RULE_TAX} AS TaxRule, d.NetAmount + {RULE_TAX} AS GrossRule
                             FROM lab1_lines d JOIN lab1_prepared p ON d.RawRowID = p.RawRowID
                             WHERE d.NetAmount IS NOT NULL""")
        differs = rows.filter("NOT (CAST(TaxAmount AS DECIMAL(18,2)) <=> TaxRule AND CAST(GrossAmount AS DECIMAL(18,2)) <=> GrossRule)")
        n = differs.count()
        for r in differs.orderBy("RawRowID").limit(3).collect():
            problems.append(f"{r['RawRowID']}: net {r['NetAmount']}, tax rate {_show(r['TaxRate'])}: the contract gives tax "
                            f"{r['TaxRule']} and gross {r['GrossRule']}, yours {_show(r['TaxAmount'])} and {_show(r['GrossAmount'])}")
        if n > 3:
            problems.append(f"rows with a wrong amount, in total: {n:,}")
        credits = rows.filter("NetAmount < 0")
        flipped = credits.filter("GrossAmount >= 0 OR TaxAmount > 0").count()
        if flipped:
            problems.append(f"credit lines that lost their sign: {flipped:,}")
        info = [f"{credits.count():,} credit lines keep negative amounts" if not flipped else "credit lines must stay negative"]
        if DATASET == "fixture":
            hand = spark.sql(f"""SELECT e.RawRowID, e.CaseID, e.ExpectedTaxAmount, e.ExpectedGrossAmount, p.TaxAmount, p.GrossAmount
                                 FROM {SOURCE}.fixture_expected_amounts e LEFT JOIN lab1_prepared p ON e.RawRowID = p.RawRowID""")
            wrong = hand.filter("NOT (CAST(TaxAmount AS DECIMAL(18,2)) <=> ExpectedTaxAmount AND CAST(GrossAmount AS DECIMAL(18,2)) <=> ExpectedGrossAmount)")
            cases = [r["CaseID"] for r in wrong.orderBy("RawRowID").collect()]
            info.append(f"{hand.count() - len(cases)} of {hand.count()} hand calculations of the fixture match"
                        + (f". Look up the cases in the fixture workbook: {', '.join(cases[:8])}" if cases else ""))
            if cases and not n:
                problems.append(f"hand calculations of the fixture that differ from your amounts: {len(cases)}")
        return problems, info

    _guard("C1", "Every delivered row is still there, once, with its delivered values", c1,
           needs=[(prepared, "prepared", ["RawRowID"])])
    _guard("C2", "StatusClass follows rule R2, compared with the rule in SQL", c2,
           needs=[(prepared, "prepared", ["RawRowID", "StatusClass"])])
    _guard("C3", "TaxAmount and GrossAmount: decimal, rounded half up, signs kept", c3,
           needs=[(prepared, "prepared", ["RawRowID", "TaxAmount", "GrossAmount"])])


def check_task_2(matched):
    _views(lines=lines, customers=customers, products=products, matched=matched)

    def c4():
        problems, summary = _same_rows(matched, "matched")
        rows = spark.sql(f"""SELECT r.*, m.CustomerMatches, m.ProductMatches
                             FROM ({RULE_MATCHES}) r JOIN lab1_matched m ON r.RawRowID = m.RawRowID""")
        differs = rows.filter("NOT (CustomerMatches <=> CustomerRule AND ProductMatches <=> ProductRule)").dropDuplicates(["RawRowID"])
        n = differs.count()
        for r in differs.orderBy("RawRowID").limit(4).collect():
            if r["CustomerMatches"] != r["CustomerRule"]:
                problems.append(f"{r['RawRowID']}: CustomerID {_show(r['CustomerID'])} has {r['CustomerRule']} master rows "
                                f"(exact key, rule R5), yours says {_show(r['CustomerMatches'])}")
            else:
                problems.append(f"{r['RawRowID']}: ProductID {_show(r['ProductID'])} has {r['ProductRule']} master rows "
                                f"(exact key, rule R6), yours says {_show(r['ProductMatches'])}")
        if n > 4:
            problems.append(f"rows with a wrong match count, in total: {n:,}")
        rule = spark.sql(RULE_MATCHES)
        info = [summary]
        for label, column, key in (("customer", "CustomerRule", "CustomerID"), ("product", "ProductRule", "ProductID")):
            none, many = rule.filter(f"{column} = 0"), rule.filter(f"{column} > 1")
            keys = ", ".join(_show(r[0]) for r in none.select(key).distinct().orderBy(key).limit(3).collect())
            info.append(f"{label} keys: rows without a master row {none.count():,}, rows with more than one master row {many.count():,}"
                        + (f". Unmatched keys, for example: {keys}" if keys else ""))
        return problems, info

    _guard("C4", "Master matches: no row lost, no row multiplied, exact keys", c4,
           needs=[(matched, "matched", ["RawRowID", "CustomerMatches", "ProductMatches"])])


def contract_columns(accepted, exceptions):
    """Both outputs with the columns of the business contract, in order. A column that does not exist yet is left out."""
    return (accepted.select(*[c for c in ACCEPTED_COLUMNS if c in accepted.columns]),
            exceptions.select(*[c for c in EXCEPTION_COLUMNS if c in exceptions.columns]))


def check_task_3(accepted, exceptions):
    needs = [(accepted, "accepted", ["RawRowID"]), (exceptions, "exceptions", ["RawRowID", "Disposition", "ReasonCode"])]
    titles = {"C5": "Every delivered row is in exactly one output",
              "C6": "One outcome for each row, in the order of the rules",
              "C7": "The accepted output: contract columns, one master row, validated totals"}
    if any(c not in df.columns for df, _, columns in needs for c in columns):
        for code, title in titles.items():
            _guard(code, title, None, needs=needs)
        return
    _views(lines=lines, customers=customers, products=products, accepted=accepted, exceptions=exceptions)
    outcomes = (accepted.select("RawRowID", F.lit("ACCEPTED").alias("Disposition"), F.lit(None).cast("string").alias("ReasonCode"))
                .unionByName(exceptions.select("RawRowID", "Disposition", "ReasonCode")))
    outcomes.createOrReplaceTempView("lab1_outcomes")

    def c5():
        problems, summary = _same_rows(outcomes, "accepted + exceptions")
        return problems, [f"{summary}: accepted {accepted.count():,} + exceptions {exceptions.count():,}"]

    def c6():
        # If a delivered row is in the outputs more than once, C5 reports it. Here one of its outcomes is judged.
        yours = "(SELECT RawRowID, min(Disposition) AS Disposition, min(ReasonCode) AS ReasonCode FROM lab1_outcomes GROUP BY RawRowID)"
        rows = spark.sql(f"""SELECT r.RawRowID, r.ReasonRule, o.Disposition, o.ReasonCode
                             FROM ({RULE_REASON}) r JOIN {yours} o ON r.RawRowID = o.RawRowID""")
        wanted = "CASE WHEN ReasonRule IS NULL THEN 'ACCEPTED' WHEN ReasonRule = 'NOT_POSTED' THEN 'EXCLUDED' ELSE 'QUARANTINED' END"
        differs = rows.filter(f"NOT (ReasonCode <=> ReasonRule AND Disposition <=> {wanted})")
        n = differs.count()
        problems = [f"{r['RawRowID']}: the rules of this lab give {r['ReasonRule'] or 'ACCEPTED'}, "
                    f"yours gives {r['Disposition']} {r['ReasonCode'] or ''}".rstrip()
                    for r in differs.orderBy("RawRowID").limit(4).collect()]
        if n > 4:
            problems.append(f"rows with a wrong outcome, in total: {n:,}")
        counts = spark.sql("SELECT coalesce(ReasonCode, '(accepted)') AS reason, count(*) AS n FROM lab1_outcomes GROUP BY 1 ORDER BY 1").collect()
        info = ["rows by outcome: " + ", ".join(f"{r['reason']} {r['n']:,}" for r in counts)]
        if DATASET == "fixture":
            expected = spark.sql(f"""SELECT e.RawRowID, e.CaseID, e.ExpectedDisposition, e.ExpectedReason, o.Disposition, o.ReasonCode
                                     FROM {SOURCE}.fixture_expected_results e LEFT JOIN {yours} o ON e.RawRowID = o.RawRowID
                                     WHERE e.ContractVersion = '1.0' ORDER BY e.RawRowID""").collect()
            in_scope = [e for e in expected if e["ExpectedReason"] is None or e["ExpectedReason"] in LAB1_REASONS]
            wrong = [e for e in in_scope if (e["Disposition"], e["ReasonCode"]) != (e["ExpectedDisposition"], e["ExpectedReason"])]
            info.append(f"fixture, contract 1.0: {len(in_scope) - len(wrong)} of {len(in_scope)} rows that this lab can decide "
                        "have the expected outcome" + (f". Cases to look up: {', '.join(sorted({e['CaseID'] for e in wrong})[:8])}" if wrong else ""))
            if wrong and not n:
                problems.append(f"fixture rows without the expected outcome: {len(wrong)}")
            open_rows = [e for e in expected if e["ExpectedReason"] in OPEN_RULES]
            by_rule = {}
            for e in open_rows:
                by_rule[OPEN_RULES[e["ExpectedReason"]]] = by_rule.get(OPEN_RULES[e["ExpectedReason"]], 0) + 1
            still_accepted = sum(1 for e in open_rows if e["Disposition"] == "ACCEPTED")
            info.append(f"OPEN TEST TARGETS: {len(open_rows)} fixture rows need a rule that this lab does not implement: "
                        + ", ".join(f"{rule} {count}" for rule, count in sorted(by_rule.items())))
            info.append(f"                   {still_accepted} of them are accepted by your code today. They are the test targets of Lab 3.")
        return problems, info

    def c7():
        problems = []
        if accepted.columns != ACCEPTED_COLUMNS:
            missing = [c for c in ACCEPTED_COLUMNS if c not in accepted.columns]
            extra = [c for c in accepted.columns if c not in ACCEPTED_COLUMNS]
            problems.append("accepted does not have the columns of the contract"
                            + (f"; missing: {', '.join(missing)}" if missing else "")
                            + (f"; not in the contract: {', '.join(extra)}" if extra else "")
                            + ("; the order differs" if not missing and not extra else ""))
        if exceptions.columns != EXCEPTION_COLUMNS:
            missing = [c for c in EXCEPTION_COLUMNS if c not in exceptions.columns]
            problems.append("exceptions does not have the columns of the contract" + (f"; missing: {', '.join(missing)}" if missing else ""))
        if problems:
            return problems, []
        attributes = spark.sql("""
            SELECT a.RawRowID, a.CustomerID, a.ProductID
            FROM lab1_accepted a
            LEFT JOIN lab1_customers c ON a.CustomerID = c.CustomerID
            LEFT JOIN lab1_products p ON a.ProductID = p.ProductID
            WHERE NOT (a.CustomerName <=> c.CustomerName AND a.Segment <=> c.Segment AND a.Country <=> c.Country
                       AND a.Region <=> c.Region AND a.ProductName <=> p.ProductName AND a.ProductLine <=> p.ProductLine)
               OR c.CustomerID IS NULL OR p.ProductID IS NULL""")
        n = attributes.select("RawRowID").distinct().count()
        if n:
            r = attributes.orderBy("RawRowID").first()
            problems.append(f"accepted rows whose attributes are not the attributes of exactly one master row: {n:,}, "
                            f"for example {r['RawRowID']} ({_show(r['CustomerID'])}, {_show(r['ProductID'])})")
        info = [f"{accepted.count():,} accepted lines, {accepted.filter('NetAmount < 0').count():,} of them credit lines"]
        if DATASET == "training":
            totals = spark.sql(f"""
                SELECT coalesce(r.Currency, y.Currency) AS Currency, r.AcceptedRows, y.AcceptedRows AS YourRows,
                       r.NetAmount, y.NetAmount AS YourNet, r.GrossAmount, y.GrossAmount AS YourGross
                FROM (SELECT * FROM {SOURCE}.reference_totals WHERE Scope = 'LAB1') r
                FULL JOIN (SELECT coalesce(Currency, '(no currency)') AS Currency, count(*) AS AcceptedRows,
                                  coalesce(sum(NetAmount), 0) AS NetAmount, coalesce(sum(GrossAmount), 0) AS GrossAmount
                           FROM lab1_accepted GROUP BY 1) y ON r.Currency = y.Currency
                ORDER BY 1""").collect()
            bad = [t for t in totals if (t["AcceptedRows"], t["NetAmount"], t["GrossAmount"]) != (t["YourRows"], t["YourNet"], t["YourGross"])]
            info.append(f"validated totals of the Lab 1 scope: {len(totals) - len(bad)} of {len(totals)} currencies match in rows, net, and gross")
            for t in bad[:4]:
                problems.append(f"{t['Currency']}: validated {t['AcceptedRows']} rows, net {t['NetAmount']}, gross {t['GrossAmount']}; "
                                f"yours {t['YourRows']} rows, net {t['YourNet']}, gross {t['YourGross']}")
        else:
            info.append("on the training data this check also compares your totals with the validated totals, for each currency")
        return problems, info

    _guard("C5", titles["C5"], c5)
    _guard("C6", titles["C6"], c6)
    _guard("C7", titles["C7"], c7)


def exception_report(exceptions):
    """What the exception report would tell the business today: rows and invoices by reason."""
    if any(c not in exceptions.columns for c in ("Disposition", "ReasonCode")):
        print("The exception report needs the outputs of Task 3.")
        return
    display(exceptions.groupBy("Disposition", "ReasonCode")
            .agg(F.count(F.lit(1)).alias("Rows"), F.countDistinct("InvoiceID").alias("Invoices"))
            .orderBy("Disposition", "ReasonCode"))


def summary():
    done = sum(1 for ok in RESULTS.values() if ok)
    missing = [c for c in ("C1", "C2", "C3", "C4", "C5", "C6", "C7") if c not in RESULTS]
    print(f"LAB 1 CHECKS on dataset '{DATASET}': {done} of 7 passed"
          + (f". Not run yet: {', '.join(missing)}" if missing else ""))


print("Acceptance checks C1 to C7 are defined.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Look at the facts before you prompt
# MAGIC
# MAGIC An assistant fills every gap in your request with an assumption. These three facts close three gaps.
# MAGIC Run the cell and read the output with your partner: 30 seconds.

# COMMAND ----------

# FACTS (supplied)
print("1. The status values as delivered. How many spellings mean 'posted'?")
for r in lines.groupBy("Status").count().orderBy(F.desc("count"), "Status").collect():
    print(f"     {str(r['Status'])!r:14} {r['count']:>7,}" if r["Status"] is not None else f"     {'NULL':14} {r['count']:>7,}")

print("\n2. Master keys with more than one row. What does a join do with them?")
for label, master, key in (("customers", customers, "CustomerID"), ("products", products, "ProductID")):
    repeated = master.groupBy(key).count().filter("count > 1")
    print(f"     {label}: {repeated.count():,} keys have more than one row")

print("\n3. Signs. Is a negative amount an error?")
print(f"     {lines.filter('Quantity < 0').count():,} delivered rows have a negative Quantity: credit lines")
print(f"     {lines.filter('TaxRate IS NULL').count():,} delivered rows have no TaxRate: no tax applies to them")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Give Genie Code its context
# MAGIC
# MAGIC 1. Open the Genie Code pane: the sparkle icon in the upper-right corner of the page.
# MAGIC 2. In the pane, open **More** > **Settings**, and set **Actions** to **Ask first**.
# MAGIC 3. Start a **New chat**. Paste the prompt that you repaired in Exercise 1, and end it with these lines:
# MAGIC
# MAGIC ```text
# MAGIC In this notebook I will ask for one small step at a time. Change only the cell that I name.
# MAGIC Do not run anything unless I ask. Do not write code yet.
# MAGIC First list the assumptions that you would have to make about this data, and wait for my answer.
# MAGIC ```
# MAGIC
# MAGIC 4. Read the assumptions. Answer two of them from the rule sheet or from the facts above.
# MAGIC    Write the three most important ones into the last cell of this notebook.
# MAGIC
# MAGIC No Genie Code today? Use the prepared responses in `prepared_ai_outputs/Lab1_prepared_response_Genie_Code.md`.
# MAGIC They contain problems on purpose. Review them like any proposal.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 1. Three facts for every delivered row
# MAGIC
# MAGIC **Request for Genie Code** (also in the workbook):
# MAGIC
# MAGIC ```text
# MAGIC Complete only the cell that starts with "# TASK 1". Keep every row of `lines` and every delivered
# MAGIC column unchanged, and add three columns:
# MAGIC - StatusClass: 'POSTED' when Status, trimmed and in upper case, is POSTED. 'NOT_POSTED' when it is
# MAGIC   DRAFT or CANCELLED. 'UNEXPECTED' for any other value, including NULL.
# MAGIC - TaxAmount: NetAmount x TaxRate, rounded half up to 2 decimals, as DECIMAL(18,2).
# MAGIC   When TaxRate is NULL, no tax applies: 0.00.
# MAGIC - GrossAmount: NetAmount + TaxAmount, as DECIMAL(18,2).
# MAGIC Do not filter. Do not overwrite Status. Do not run the cell: I review it first.
# MAGIC ```
# MAGIC
# MAGIC **Review before you run.** The reviewer answers aloud:
# MAGIC
# MAGIC 1. Does any line filter, drop, or deduplicate rows?
# MAGIC 2. Is a delivered column overwritten, for example `Status`?
# MAGIC 3. Is any amount cast to `double` or `float`? What happens when `TaxRate` is NULL?

# COMMAND ----------

# TASK 1. Every delivered row, plus three facts. Nothing is filtered here.
#   StatusClass   POSTED, NOT_POSTED (draft or cancelled), or UNEXPECTED, by rule R2
#   TaxAmount     NetAmount x TaxRate, rounded half up to 2 decimals. 0.00 when TaxRate is NULL
#   GrossAmount   NetAmount + TaxAmount
prepared = lines   # TODO: replace this line with the code that you reviewed

# COMMAND ----------

check_task_1(prepared)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 2. Count the master rows of every key
# MAGIC
# MAGIC **Write this request yourselves.** The result is a DataFrame `matched`: every row of `prepared`, plus
# MAGIC `CustomerMatches` and `ProductMatches`, the number of master rows that have exactly this key.
# MAGIC
# MAGIC Your request should say:
# MAGIC
# MAGIC - which cell to change, and that nothing else changes
# MAGIC - the two new columns, and what they hold when no master row matches
# MAGIC - the output grain: exactly one row for each row of `prepared`
# MAGIC - what the assistant must not do: join the master attributes now, or trim or change the case of a key
# MAGIC - that you review before anything runs
# MAGIC
# MAGIC **Review before you run.**
# MAGIC
# MAGIC 1. Which join type is used, and what is joined: the master table, or one row for each key?
# MAGIC 2. Can a key with two master rows produce two output rows?
# MAGIC 3. What does a key without a master row get: 0, NULL, or no row at all?
# MAGIC
# MAGIC Stuck for more than two minutes? The workbook has a reference request for this task.

# COMMAND ----------

# TASK 2. How many master rows has each key? One row out for each row in.
#   CustomerMatches   number of rows in `customers` with exactly this CustomerID. 0 when there is none
#   ProductMatches    number of rows in `products` with exactly this ProductID. 0 when there is none
matched = prepared   # TODO: replace this line with the code that you reviewed

# COMMAND ----------

check_task_2(matched)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task 3. One outcome for every row, then two outputs
# MAGIC
# MAGIC **Switch driver and reviewer now.**
# MAGIC
# MAGIC **Request for Genie Code** (also in the workbook):
# MAGIC
# MAGIC ```text
# MAGIC Complete only the cell that starts with "# TASK 3".
# MAGIC 1. Add ReasonCode to `matched`. The first rule that fails decides: NOT_POSTED when StatusClass is
# MAGIC    NOT_POSTED. UNEXPECTED_STATUS when StatusClass is UNEXPECTED. UNKNOWN_CUSTOMER when CustomerMatches
# MAGIC    is 0, AMBIGUOUS_CUSTOMER when it is above 1. UNKNOWN_PRODUCT and AMBIGUOUS_PRODUCT in the same way
# MAGIC    for ProductMatches. Otherwise NULL.
# MAGIC 2. Add Disposition: ACCEPTED when ReasonCode is NULL, EXCLUDED for NOT_POSTED, QUARANTINED for every
# MAGIC    other reason.
# MAGIC 3. `accepted`: the ACCEPTED rows, joined to `customers` for CustomerName, Segment, Country, Region,
# MAGIC    and to `products` for ProductName, ProductLine.
# MAGIC 4. `exceptions`: every other row. No row may be dropped, and no missing value may be filled.
# MAGIC Do not select or rename columns: the next cell does that. Do not run the cell: I review it first.
# MAGIC ```
# MAGIC
# MAGIC **Review before you run.**
# MAGIC
# MAGIC 1. Is the order of the conditions the order of the rules? What does a draft with an unknown customer get?
# MAGIC 2. Why can the joins to `customers` and `products` not multiply a row here, although they could in Task 2?
# MAGIC 3. Where do the rows go that are not accepted? Is any value replaced by a placeholder such as 'UNKNOWN'?

# COMMAND ----------

# TASK 3. Decide once, then split.
#   decided      matched + ReasonCode + Disposition (ACCEPTED, QUARANTINED, or EXCLUDED)
#   accepted     the ACCEPTED rows, with the customer and product attributes
#   exceptions   every other delivered row, with Disposition and ReasonCode
decided = matched      # TODO: add ReasonCode and Disposition
accepted = decided     # TODO: only the ACCEPTED rows, with the customer and product attributes
exceptions = decided   # TODO: every other row

# COMMAND ----------

accepted, exceptions = contract_columns(accepted, exceptions)   # supplied: the columns of the contract, in order
check_task_3(accepted, exceptions)
summary()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prove it on the training data
# MAGIC
# MAGIC Seven checks passed on 56 rows. Now the same code meets about 50,000 rows.
# MAGIC
# MAGIC 1. Set the widget **Dataset** at the top of the notebook to `training`.
# MAGIC 2. Select **Run all**.
# MAGIC 3. Compare the lines of checks C5, C6, and C7 with the output in the workbook.
# MAGIC
# MAGIC The next cell shows what your exception report would tell the business today.

# COMMAND ----------

# RESULT (supplied): the exception report, by reason
exception_report(exceptions)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Record: what you assumed, what you can explain, what is still open
# MAGIC
# MAGIC Double-click this cell and fill it in. It is part of your lab output, and the debrief starts here.
# MAGIC
# MAGIC **Three assumptions that we confirmed or corrected**
# MAGIC
# MAGIC 1.
# MAGIC 2.
# MAGIC 3.
# MAGIC
# MAGIC **One generated expression that we can explain without the assistant** (copy it, then say in one
# MAGIC sentence what it does to a NULL, to a credit, or to a duplicate master key)
# MAGIC
# MAGIC -
# MAGIC
# MAGIC **How our joins and filters behave** (two sentences)
# MAGIC
# MAGIC -
# MAGIC
# MAGIC **Open test targets** (from check C6 on the fixture: which rules are not implemented yet)
# MAGIC
# MAGIC -
