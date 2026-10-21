# Databricks notebook source
# MAGIC %md
# MAGIC # 00 Setup: load and verify the O2I training data
# MAGIC
# MAGIC **Instructor notebook. Run it once for each workspace.** It creates the schema `o2i` with 13 tables
# MAGIC of fictional data, adds table and column comments, and proves that every table arrived unchanged.
# MAGIC
# MAGIC | Step | What it does |
# MAGIC |---|---|
# MAGIC | 1 | Reads your choices from the widgets at the top of the notebook |
# MAGIC | 2 | Creates the schema and the volume for the source files |
# MAGIC | 3 | Lists the tables of the kit and checks that the source files are in the volume |
# MAGIC | 4 | Loads every table: from Excel when the compute can read Excel, otherwise from CSV |
# MAGIC | 5 | Adds comments, so that Genie Code and Catalog Explorer show what a column means |
# MAGIC | 6 | Grants read access to the participants |
# MAGIC | 7 | Verifies row counts and fingerprints. The last line must be `ALL TABLES VERIFIED` |
# MAGIC
# MAGIC **Before you run it:** run steps 1 and 2 first. Step 2 creates the volume and prints its path.
# MAGIC Upload the 26 files of the kit folder `4_Data` (13 `.xlsx` and 13 `.csv`) to the volume, then run the rest.
# MAGIC
# MAGIC You need the right to create a schema in the catalog. In a workspace that you created yourself, you
# MAGIC have it as workspace admin. In a sandbox of your client, the platform team may have to run this notebook.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1. Your choices

# COMMAND ----------

DEFAULT_CATALOG = "o2iworkshop"  # written by tools/prepare_cohort.py

dbutils.widgets.text("catalog", DEFAULT_CATALOG, "1. Catalog")
dbutils.widgets.text("schema", "o2i", "2. Schema for the training tables")
dbutils.widgets.text("source_path", "", "3. Source folder (empty: the landing volume)")
dbutils.widgets.dropdown("route", "auto", ["auto", "excel", "csv", "verify only"], "4. Load from")
dbutils.widgets.text("grant_to", "", "5. Grant read access to (group or user, optional)")

CATALOG = dbutils.widgets.get("catalog").strip()
SCHEMA = dbutils.widgets.get("schema").strip()
ROUTE = dbutils.widgets.get("route")
VERIFY_ONLY = ROUTE == "verify only"          # load nothing, only compare the tables with the kit (step 7)
GRANT_TO = dbutils.widgets.get("grant_to").strip()
SOURCE = dbutils.widgets.get("source_path").strip().rstrip("/") or f"/Volumes/{CATALOG}/{SCHEMA}/landing"

# Timestamps are read and compared as text in one fixed time zone, so that the fingerprints are stable.
spark.conf.set("spark.sql.session.timeZone", "UTC")

print(f"Catalog:        {CATALOG}")
print(f"Schema:         {CATALOG}.{SCHEMA}")
print(f"Source folder:  {SOURCE}")
print(f"Load from:      {ROUTE}")
print(f"Grant read to:  {GRANT_TO or '(nobody, you grant access later)'}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2. Schema and volume
# MAGIC
# MAGIC After this cell, upload the files of `4_Data` to the path that it prints: **Catalog** > your catalog >
# MAGIC `o2i` > `landing` > **Add data** > **Upload files to a volume**. You can upload all 26 files into the
# MAGIC volume itself, or keep the two folders `excel` and `csv`. The notebook finds the files either way.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{SCHEMA}` COMMENT 'O2I training data of the workshop AI-Driven SDLC with Databricks. Fictional data.'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`.landing COMMENT 'Source files of the O2I training data, as delivered in the course kit.'")
print(f"Upload the files of 4_Data to: /Volumes/{CATALOG}/{SCHEMA}/landing")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3. The tables of the kit, and their source files
# MAGIC
# MAGIC `TABLES` is the contract of this notebook: every table, every column, its type, and its comment.
# MAGIC `EXPECTED` holds the row count and the fingerprint of every table, recorded when the kit was built.

# COMMAND ----------

TABLES = {
    'invoice_lines': {
        "comment": 'Delivered sales invoice lines, as extracted from the source systems. Fictional training data. One delivered row is identified by RawRowID. One invoice line is identified by InvoiceID + LineNumber. A line can be delivered more than once. Training extract: about 50,000 delivered rows.',
        "columns": [
            ('RawRowID', 'STRING', 'Technical. Identifies one delivered row. Unique. Assigned at ingestion in delivery order.'),
            ('InvoiceID', 'STRING', 'Invoice or credit note number. Together with LineNumber it identifies one invoice line.'),
            ('LineNumber', 'INT', 'Line of the invoice, starting at 1.'),
            ('InvoiceDate', 'STRING', 'Invoice date as delivered, as text. Expected format yyyy-MM-dd. Not validated at ingestion.'),
            ('DocumentType', 'STRING', 'INVOICE or CREDIT_NOTE. Informational: the sign of Quantity carries the meaning.'),
            ('Status', 'STRING', 'Document status as delivered, as text. Not cleaned at ingestion. Business values: POSTED, DRAFT, CANCELLED.'),
            ('CustomerID', 'STRING', 'Customer key as delivered. Refers to customers.CustomerID.'),
            ('ProductID', 'STRING', 'Product key as delivered. Refers to products.ProductID.'),
            ('OrderID', 'STRING', 'Order that the line bills. NULL for an invoice without an order. Refers to orders.OrderID.'),
            ('OrderLineNumber', 'INT', 'Order line that the line bills. Refers to orders.OrderLineNumber.'),
            ('Quantity', 'DECIMAL(12,3)', 'Invoiced quantity. Negative on a credit line. Carries the sign of the line.'),
            ('UnitPrice', 'DECIMAL(18,4)', 'Agreed net price for one unit, in Currency. Never negative.'),
            ('NetAmount', 'DECIMAL(18,2)', 'Net amount of the line as delivered: Quantity x UnitPrice, rounded half up to two decimals. Negative on a credit line.'),
            ('TaxRate', 'DECIMAL(6,4)', 'Tax rate as a fraction, for example 0.2000 for 20 percent. NULL means that no tax applies to the line.'),
            ('Currency', 'STRING', 'ISO currency code of UnitPrice and NetAmount. Amounts in different currencies are never added.'),
            ('SalesOrg', 'STRING', 'Sales organization that issued the document.'),
            ('SourceSystem', 'STRING', 'Source system of the delivery: ERP_EU or ERP_NA.'),
            ('LoadBatchID', 'STRING', 'Technical. Delivery batch, LB- followed by the load date.'),
            ('IngestedAt', 'TIMESTAMP', 'Technical. Time when the row was ingested.'),
        ],
    },
    'customers': {
        "comment": 'Customer master data. Fictional training data. One row for each CustomerID is expected. The table has no enforced key. Training extract.',
        "columns": [
            ('CustomerID', 'STRING', 'Customer key. One row for each key is expected, but the table has no enforced key.'),
            ('CustomerName', 'STRING', 'Legal name of the customer. Fictional.'),
            ('Segment', 'STRING', 'Customer segment: DEALER, FLEET, DISTRIBUTOR, ECOMMERCE, or OEM.'),
            ('Country', 'STRING', 'ISO country code of the customer.'),
            ('Region', 'STRING', 'Sales region: EMEA or AMER.'),
            ('City', 'STRING', 'City of the customer.'),
            ('PostalCode', 'STRING', 'Postal code, as text.'),
            ('BillingCurrency', 'STRING', 'Currency in which the customer is invoiced.'),
            ('PaymentTerms', 'STRING', 'NET30, NET45, NET60, or PREPAID.'),
            ('CreditLimit', 'DECIMAL(18,2)', 'Credit limit in the billing currency.'),
            ('AccountManager', 'STRING', 'Identifier of the account manager.'),
            ('ParentCustomerID', 'STRING', 'CustomerID of the parent company, if any.'),
            ('IsActive', 'BOOLEAN', 'False for a customer that no longer orders.'),
            ('CreatedDate', 'DATE', 'Date when the customer was created.'),
            ('LastUpdated', 'TIMESTAMP', 'Time of the last change of this master row.'),
        ],
    },
    'products': {
        "comment": 'Product master data. Fictional training data. One row for each ProductID is expected. The table has no enforced key. Training extract.',
        "columns": [
            ('ProductID', 'STRING', 'Product key. One row for each key is expected, but the table has no enforced key.'),
            ('ProductName', 'STRING', 'Product description. Fictional.'),
            ('ProductLine', 'STRING', 'PASSENGER, LIGHT_TRUCK, TRUCK_BUS, AGRICULTURAL, TWO_WHEEL, ACCESSORIES, or SERVICES.'),
            ('ProductFamily', 'STRING', 'Family inside the product line.'),
            ('SizeDesignation', 'STRING', 'Size designation of a tyre. NULL for accessories and services.'),
            ('RimDiameterInch', 'DECIMAL(4,1)', 'Rim diameter in inches. NULL for accessories and services.'),
            ('UnitOfMeasure', 'STRING', 'EA (each), SET, or HR (hour).'),
            ('ListPrice', 'DECIMAL(18,4)', 'List price for one unit, in ListPriceCurrency.'),
            ('ListPriceCurrency', 'STRING', 'Currency of ListPrice. Always EUR.'),
            ('TaxClass', 'STRING', 'STANDARD, REDUCED, or EXEMPT.'),
            ('Status', 'STRING', 'ACTIVE, PHASE_OUT, or BLOCKED.'),
            ('WeightKg', 'DECIMAL(8,3)', 'Weight of one unit in kilograms. NULL for accessories and services.'),
            ('LaunchDate', 'DATE', 'Date of the market launch.'),
            ('LastUpdated', 'TIMESTAMP', 'Time of the last change of this master row.'),
        ],
    },
    'orders': {
        "comment": 'Customer order lines. Fictional training data. One row for each OrderID + OrderLineNumber is expected. The table has no enforced key. Training extract.',
        "columns": [
            ('OrderID', 'STRING', 'Order number. Together with OrderLineNumber it identifies one order line.'),
            ('OrderLineNumber', 'INT', 'Line of the order, starting at 1.'),
            ('OrderDate', 'DATE', 'Date of the order.'),
            ('CustomerID', 'STRING', 'Customer who ordered.'),
            ('ProductID', 'STRING', 'Product that was ordered.'),
            ('OrderedQuantity', 'DECIMAL(12,3)', 'Ordered quantity. Always positive.'),
            ('AgreedUnitPrice', 'DECIMAL(18,4)', 'Agreed net price for one unit, in Currency.'),
            ('Currency', 'STRING', 'ISO currency code of AgreedUnitPrice.'),
            ('OrderStatus', 'STRING', 'OPEN, CONFIRMED, SHIPPED, INVOICED, or CANCELLED.'),
            ('SalesChannel', 'STRING', 'EDI, PORTAL, INSIDE_SALES, or FIELD_SALES.'),
            ('SalesOrg', 'STRING', 'Sales organization that took the order.'),
            ('RequestedDeliveryDate', 'DATE', 'Delivery date that the customer requested.'),
            ('LastUpdated', 'TIMESTAMP', 'Time of the last change of this order line.'),
        ],
    },
    'fixture_invoice_lines': {
        "comment": 'Delivered sales invoice lines, as extracted from the source systems. Fictional training data. One delivered row is identified by RawRowID. One invoice line is identified by InvoiceID + LineNumber. A line can be delivered more than once. Fixture: 56 delivered rows in 48 named cases, small enough to verify by hand.',
        "columns": [
            ('RawRowID', 'STRING', 'Technical. Identifies one delivered row. Unique. Assigned at ingestion in delivery order.'),
            ('InvoiceID', 'STRING', 'Invoice or credit note number. Together with LineNumber it identifies one invoice line.'),
            ('LineNumber', 'INT', 'Line of the invoice, starting at 1.'),
            ('InvoiceDate', 'STRING', 'Invoice date as delivered, as text. Expected format yyyy-MM-dd. Not validated at ingestion.'),
            ('DocumentType', 'STRING', 'INVOICE or CREDIT_NOTE. Informational: the sign of Quantity carries the meaning.'),
            ('Status', 'STRING', 'Document status as delivered, as text. Not cleaned at ingestion. Business values: POSTED, DRAFT, CANCELLED.'),
            ('CustomerID', 'STRING', 'Customer key as delivered. Refers to customers.CustomerID.'),
            ('ProductID', 'STRING', 'Product key as delivered. Refers to products.ProductID.'),
            ('OrderID', 'STRING', 'Order that the line bills. NULL for an invoice without an order. Refers to orders.OrderID.'),
            ('OrderLineNumber', 'INT', 'Order line that the line bills. Refers to orders.OrderLineNumber.'),
            ('Quantity', 'DECIMAL(12,3)', 'Invoiced quantity. Negative on a credit line. Carries the sign of the line.'),
            ('UnitPrice', 'DECIMAL(18,4)', 'Agreed net price for one unit, in Currency. Never negative.'),
            ('NetAmount', 'DECIMAL(18,2)', 'Net amount of the line as delivered: Quantity x UnitPrice, rounded half up to two decimals. Negative on a credit line.'),
            ('TaxRate', 'DECIMAL(6,4)', 'Tax rate as a fraction, for example 0.2000 for 20 percent. NULL means that no tax applies to the line.'),
            ('Currency', 'STRING', 'ISO currency code of UnitPrice and NetAmount. Amounts in different currencies are never added.'),
            ('SalesOrg', 'STRING', 'Sales organization that issued the document.'),
            ('SourceSystem', 'STRING', 'Source system of the delivery: ERP_EU or ERP_NA.'),
            ('LoadBatchID', 'STRING', 'Technical. Delivery batch, LB- followed by the load date.'),
            ('IngestedAt', 'TIMESTAMP', 'Technical. Time when the row was ingested.'),
        ],
    },
    'fixture_customers': {
        "comment": 'Customer master data. Fictional training data. One row for each CustomerID is expected. The table has no enforced key. Fixture master data.',
        "columns": [
            ('CustomerID', 'STRING', 'Customer key. One row for each key is expected, but the table has no enforced key.'),
            ('CustomerName', 'STRING', 'Legal name of the customer. Fictional.'),
            ('Segment', 'STRING', 'Customer segment: DEALER, FLEET, DISTRIBUTOR, ECOMMERCE, or OEM.'),
            ('Country', 'STRING', 'ISO country code of the customer.'),
            ('Region', 'STRING', 'Sales region: EMEA or AMER.'),
            ('City', 'STRING', 'City of the customer.'),
            ('PostalCode', 'STRING', 'Postal code, as text.'),
            ('BillingCurrency', 'STRING', 'Currency in which the customer is invoiced.'),
            ('PaymentTerms', 'STRING', 'NET30, NET45, NET60, or PREPAID.'),
            ('CreditLimit', 'DECIMAL(18,2)', 'Credit limit in the billing currency.'),
            ('AccountManager', 'STRING', 'Identifier of the account manager.'),
            ('ParentCustomerID', 'STRING', 'CustomerID of the parent company, if any.'),
            ('IsActive', 'BOOLEAN', 'False for a customer that no longer orders.'),
            ('CreatedDate', 'DATE', 'Date when the customer was created.'),
            ('LastUpdated', 'TIMESTAMP', 'Time of the last change of this master row.'),
        ],
    },
    'fixture_products': {
        "comment": 'Product master data. Fictional training data. One row for each ProductID is expected. The table has no enforced key. Fixture master data.',
        "columns": [
            ('ProductID', 'STRING', 'Product key. One row for each key is expected, but the table has no enforced key.'),
            ('ProductName', 'STRING', 'Product description. Fictional.'),
            ('ProductLine', 'STRING', 'PASSENGER, LIGHT_TRUCK, TRUCK_BUS, AGRICULTURAL, TWO_WHEEL, ACCESSORIES, or SERVICES.'),
            ('ProductFamily', 'STRING', 'Family inside the product line.'),
            ('SizeDesignation', 'STRING', 'Size designation of a tyre. NULL for accessories and services.'),
            ('RimDiameterInch', 'DECIMAL(4,1)', 'Rim diameter in inches. NULL for accessories and services.'),
            ('UnitOfMeasure', 'STRING', 'EA (each), SET, or HR (hour).'),
            ('ListPrice', 'DECIMAL(18,4)', 'List price for one unit, in ListPriceCurrency.'),
            ('ListPriceCurrency', 'STRING', 'Currency of ListPrice. Always EUR.'),
            ('TaxClass', 'STRING', 'STANDARD, REDUCED, or EXEMPT.'),
            ('Status', 'STRING', 'ACTIVE, PHASE_OUT, or BLOCKED.'),
            ('WeightKg', 'DECIMAL(8,3)', 'Weight of one unit in kilograms. NULL for accessories and services.'),
            ('LaunchDate', 'DATE', 'Date of the market launch.'),
            ('LastUpdated', 'TIMESTAMP', 'Time of the last change of this master row.'),
        ],
    },
    'fixture_orders': {
        "comment": 'Customer order lines. Fictional training data. One row for each OrderID + OrderLineNumber is expected. The table has no enforced key. Fixture order lines.',
        "columns": [
            ('OrderID', 'STRING', 'Order number. Together with OrderLineNumber it identifies one order line.'),
            ('OrderLineNumber', 'INT', 'Line of the order, starting at 1.'),
            ('OrderDate', 'DATE', 'Date of the order.'),
            ('CustomerID', 'STRING', 'Customer who ordered.'),
            ('ProductID', 'STRING', 'Product that was ordered.'),
            ('OrderedQuantity', 'DECIMAL(12,3)', 'Ordered quantity. Always positive.'),
            ('AgreedUnitPrice', 'DECIMAL(18,4)', 'Agreed net price for one unit, in Currency.'),
            ('Currency', 'STRING', 'ISO currency code of AgreedUnitPrice.'),
            ('OrderStatus', 'STRING', 'OPEN, CONFIRMED, SHIPPED, INVOICED, or CANCELLED.'),
            ('SalesChannel', 'STRING', 'EDI, PORTAL, INSIDE_SALES, or FIELD_SALES.'),
            ('SalesOrg', 'STRING', 'Sales organization that took the order.'),
            ('RequestedDeliveryDate', 'DATE', 'Delivery date that the customer requested.'),
            ('LastUpdated', 'TIMESTAMP', 'Time of the last change of this order line.'),
        ],
    },
    'fixture_expected_results': {
        "comment": 'Expected outcome of every delivered row, for each version of the business contract. Written from the contract and validated by the instructor. One row for each RawRowID and ContractVersion. Fixture.',
        "columns": [
            ('RawRowID', 'STRING', 'The delivered row.'),
            ('ContractVersion', 'STRING', 'Version of the business contract: 1.0 or 1.1.'),
            ('CaseID', 'STRING', 'Named case of the fixture (F01 to F48) or of the challenge batch (C01 to C16).'),
            ('ExpectedDisposition', 'STRING', 'ACCEPTED, QUARANTINED, or EXCLUDED.'),
            ('ExpectedReason', 'STRING', 'Expected reason code. NULL for an accepted row.'),
        ],
    },
    'fixture_expected_amounts': {
        "comment": 'Hand-calculated TaxAmount and GrossAmount of the fixture rows that contract 1.0 accepts. One row for each RawRowID. Fixture.',
        "columns": [
            ('RawRowID', 'STRING', 'The delivered row.'),
            ('CaseID', 'STRING', 'Named case of the fixture.'),
            ('NetAmount', 'DECIMAL(18,2)', 'Net amount as delivered.'),
            ('TaxRate', 'DECIMAL(6,4)', 'Tax rate as delivered. NULL means that no tax applies.'),
            ('ExpectedTaxAmount', 'DECIMAL(18,2)', 'NetAmount x TaxRate, rounded half up to two decimals, calculated by hand. 0.00 without a tax rate.'),
            ('ExpectedGrossAmount', 'DECIMAL(18,2)', 'NetAmount + ExpectedTaxAmount.'),
        ],
    },
    'challenge_invoice_lines': {
        "comment": 'Delivered sales invoice lines, as extracted from the source systems. Fictional training data. One delivered row is identified by RawRowID. One invoice line is identified by InvoiceID + LineNumber. A line can be delivered more than once. Challenge batch of Lab 4: 191 delivered rows in 16 named cases. It uses the training master data and orders.',
        "columns": [
            ('RawRowID', 'STRING', 'Technical. Identifies one delivered row. Unique. Assigned at ingestion in delivery order.'),
            ('InvoiceID', 'STRING', 'Invoice or credit note number. Together with LineNumber it identifies one invoice line.'),
            ('LineNumber', 'INT', 'Line of the invoice, starting at 1.'),
            ('InvoiceDate', 'STRING', 'Invoice date as delivered, as text. Expected format yyyy-MM-dd. Not validated at ingestion.'),
            ('DocumentType', 'STRING', 'INVOICE or CREDIT_NOTE. Informational: the sign of Quantity carries the meaning.'),
            ('Status', 'STRING', 'Document status as delivered, as text. Not cleaned at ingestion. Business values: POSTED, DRAFT, CANCELLED.'),
            ('CustomerID', 'STRING', 'Customer key as delivered. Refers to customers.CustomerID.'),
            ('ProductID', 'STRING', 'Product key as delivered. Refers to products.ProductID.'),
            ('OrderID', 'STRING', 'Order that the line bills. NULL for an invoice without an order. Refers to orders.OrderID.'),
            ('OrderLineNumber', 'INT', 'Order line that the line bills. Refers to orders.OrderLineNumber.'),
            ('Quantity', 'DECIMAL(12,3)', 'Invoiced quantity. Negative on a credit line. Carries the sign of the line.'),
            ('UnitPrice', 'DECIMAL(18,4)', 'Agreed net price for one unit, in Currency. Never negative.'),
            ('NetAmount', 'DECIMAL(18,2)', 'Net amount of the line as delivered: Quantity x UnitPrice, rounded half up to two decimals. Negative on a credit line.'),
            ('TaxRate', 'DECIMAL(6,4)', 'Tax rate as a fraction, for example 0.2000 for 20 percent. NULL means that no tax applies to the line.'),
            ('Currency', 'STRING', 'ISO currency code of UnitPrice and NetAmount. Amounts in different currencies are never added.'),
            ('SalesOrg', 'STRING', 'Sales organization that issued the document.'),
            ('SourceSystem', 'STRING', 'Source system of the delivery: ERP_EU or ERP_NA.'),
            ('LoadBatchID', 'STRING', 'Technical. Delivery batch, LB- followed by the load date.'),
            ('IngestedAt', 'TIMESTAMP', 'Technical. Time when the row was ingested.'),
        ],
    },
    'challenge_expected_results': {
        "comment": 'Expected outcome of every delivered row, for each version of the business contract. Written from the contract and validated by the instructor. One row for each RawRowID and ContractVersion. Challenge batch of Lab 4.',
        "columns": [
            ('RawRowID', 'STRING', 'The delivered row.'),
            ('ContractVersion', 'STRING', 'Version of the business contract: 1.0 or 1.1.'),
            ('CaseID', 'STRING', 'Named case of the fixture (F01 to F48) or of the challenge batch (C01 to C16).'),
            ('ExpectedDisposition', 'STRING', 'ACCEPTED, QUARANTINED, or EXCLUDED.'),
            ('ExpectedReason', 'STRING', 'Expected reason code. NULL for an accepted row.'),
        ],
    },
    'reference_totals': {
        "comment": 'Validated totals of the accepted training invoice lines, for each scope of rules and each currency. Part of the instructor-validated answer set: calculated independently of the course code. Use it to judge a result. Never use it to produce one. One row for each Scope and Currency. Training extract.',
        "columns": [
            ('Scope', 'STRING', 'Rules that were applied: LAB1 (rules R2, R5, R6 only), CONTRACT_1.0 (rules R1 to R7), or CONTRACT_1.1 (rules R1 to R8).'),
            ('Currency', 'STRING', 'ISO currency code. Totals are never added across currencies.'),
            ('AcceptedRows', 'INT', 'Number of accepted invoice lines of the training data in this scope and currency.'),
            ('NetAmount', 'DECIMAL(18,2)', 'Sum of NetAmount of the accepted lines. Credits are negative and reduce the total.'),
            ('TaxAmount', 'DECIMAL(18,2)', 'Sum of TaxAmount of the accepted lines: NetAmount x TaxRate, rounded half up for each line, 0.00 without a tax rate.'),
            ('GrossAmount', 'DECIMAL(18,2)', 'Sum of GrossAmount of the accepted lines: NetAmount + TaxAmount for each line.'),
        ],
    },
}

# Row count and fingerprint of every table, recorded when the kit was built.
EXPECTED = {
    'invoice_lines': (49700, 106892088253162),
    'customers': (1180, 2629400985822),
    'products': (601, 1290899358187),
    'orders': (55448, 119292272889274),
    'fixture_invoice_lines': (56, 122422961024),
    'fixture_customers': (11, 18172902362),
    'fixture_products': (9, 15394355222),
    'fixture_orders': (42, 87306291188),
    'fixture_expected_results': (112, 228970100048),
    'fixture_expected_amounts': (22, 51612074364),
    'challenge_invoice_lines': (191, 425381737767),
    'challenge_expected_results': (382, 823557063249),
    'reference_totals': (16, 37934513335),
}

print(f"{len(TABLES)} tables, {sum(n for n, _ in EXPECTED.values()):,} rows expected")

# COMMAND ----------

def source_files(folder: str, extension: str):
    """Return {table: path} for the source files that are present, in a subfolder or in the source folder itself."""
    found = {}
    for table in TABLES:
        for path in (f"{SOURCE}/{folder}/{table}.{extension}", f"{SOURCE}/{table}.{extension}"):
            try:
                dbutils.fs.ls(path)
                found[table] = path
                break
            except Exception:
                pass
    return found

if VERIFY_ONLY:
    excel_files, csv_files = {}, {}
    print("Verify only: no source file is needed.")
else:
    excel_files, csv_files = source_files("excel", "xlsx"), source_files("csv", "csv")
    print(f"Excel files found: {len(excel_files)} of {len(TABLES)}")
    print(f"CSV files found:   {len(csv_files)} of {len(TABLES)}")
    missing = [t for t in TABLES if t not in excel_files and t not in csv_files]
    if missing:
        raise Exception(f"No source file for: {', '.join(missing)}. Upload the files of 4_Data to {SOURCE} and run this cell again.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4. Load
# MAGIC
# MAGIC Text columns keep their spaces and their case: the labs need the values exactly as delivered.
# MAGIC In the Excel files, text, dates, and timestamps are text cells, and numbers are number cells.
# MAGIC In the CSV files, everything is text. Both routes end in the same typed table.
# MAGIC
# MAGIC **Excel route.** The built-in Excel reader needs Databricks Runtime 17.1 or above. The documentation
# MAGIC does not say on which compute types it works. When the reader is not available, or a table does not
# MAGIC match its fingerprint, this notebook loads the CSV file with the same content instead, and says so.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

def is_number(dtype: str) -> bool:
    return dtype == "INT" or dtype.startswith("DECIMAL")

def read_excel(table: str):
    """First sheet of the workbook, one header row. Number cells are read as double, every other cell as text."""
    schema = StructType([StructField(name, DoubleType() if is_number(dtype) else StringType())
                         for name, dtype, _ in TABLES[table]["columns"]])
    return spark.read.format("excel").option("headerRows", 1).schema(schema).load(excel_files[table])

def read_csv(table: str):
    schema = StructType([StructField(name, StringType()) for name, _, _ in TABLES[table]["columns"]])
    return spark.read.option("header", True).schema(schema).csv(csv_files[table])

def typed(df, table: str):
    """Cast the columns as read to the types of TABLES. try_cast returns NULL for a value that does not fit."""
    columns = []
    for name, dtype, _ in TABLES[table]["columns"]:
        if dtype == "STRING":
            columns.append(F.col(name))
        elif dtype == "INT":
            columns.append(F.expr(f"CAST(try_cast(`{name}` AS DECIMAL(20,4)) AS INT)").alias(name))
        else:
            columns.append(F.expr(f"try_cast(`{name}` AS {dtype})").alias(name))
    return df.select(*columns)

def fingerprint(df, table: str):
    """Row count and an order-independent checksum of all values, as text."""
    names = [name for name, _, _ in TABLES[table]["columns"]]
    line = F.concat_ws("\u001f", *[F.coalesce(F.col(n).cast("string"), F.lit("\u0000")) for n in names])
    row = df.agg(F.count(F.lit(1)).alias("n"), F.sum(F.crc32(line.cast("binary"))).alias("s")).first()
    return int(row["n"]), int(row["s"] or 0)

def full_name(table: str) -> str:
    return f"`{CATALOG}`.`{SCHEMA}`.`{table}`"

def load(table: str) -> str:
    """Load one table and return the route that produced the verified result."""
    routes = []
    if ROUTE in ("auto", "excel") and table in excel_files:
        routes.append(("Excel", read_excel))
    if ROUTE in ("auto", "csv") and table in csv_files:
        routes.append(("CSV", read_csv))
    problems = []
    for label, reader in routes:
        try:
            df = typed(reader(table), table)
            if fingerprint(df, table) != EXPECTED[table]:
                problems.append(f"{label}: the values differ from the kit")
                continue
            df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(full_name(table))
            return label
        except Exception as error:
            problems.append(f"{label}: {type(error).__name__}: {(str(error).splitlines() or [''])[0][:160]}")
    raise Exception(f"Table {table} could not be loaded. " + (" | ".join(problems) or "No source file for the chosen route."))

# COMMAND ----------

loaded_from = {}
if VERIFY_ONLY:
    print("Verify only: nothing is loaded.")
else:
    for table in TABLES:
        loaded_from[table] = load(table)
        print(f"{table:28s} loaded from {loaded_from[table]}")

if "CSV" in loaded_from.values() and ROUTE == "auto":
    print("\nNote: at least one table was loaded from CSV because the Excel route was not available or did not verify.")
    print("The content of both file types is identical, so the class is not affected.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5. Comments
# MAGIC
# MAGIC Genie Code reads table and column comments. A comment is a claim about the data, not a proof:
# MAGIC "one row for each CustomerID is expected" is exactly the claim that the labs put to the test.
# MAGIC No primary key is declared on purpose: an informational key that the data violates would mislead.

# COMMAND ----------

def sql_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("'", "\\'")

if VERIFY_ONLY:
    print("Verify only: comments are left as they are.")
else:
    for table, spec in TABLES.items():
        spark.sql(f"COMMENT ON TABLE {full_name(table)} IS '{sql_text(spec['comment'])}'")
        for name, _, comment in spec["columns"]:
            spark.sql(f"ALTER TABLE {full_name(table)} ALTER COLUMN `{name}` COMMENT '{sql_text(comment)}'")
    print(f"Comments written for {len(TABLES)} tables.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6. Read access for the participants
# MAGIC
# MAGIC Enter a group or a user in widget 5 to grant read access now. You can also grant later, with the
# MAGIC notebook `01_provision_learner_schemas`, which creates the output schemas as well.

# COMMAND ----------

if GRANT_TO:
    spark.sql(f"GRANT USE CATALOG ON CATALOG `{CATALOG}` TO `{GRANT_TO}`")
    # READ VOLUME lets a participant read the project archive in the landing volume (run route D).
    spark.sql(f"GRANT USE SCHEMA, SELECT, READ VOLUME ON SCHEMA `{CATALOG}`.`{SCHEMA}` TO `{GRANT_TO}`")
    print(f"Granted USE CATALOG, and USE SCHEMA, SELECT and READ VOLUME on {CATALOG}.{SCHEMA}, to {GRANT_TO}.")
else:
    print("No grant requested.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7. Verify
# MAGIC
# MAGIC This cell reads every table back from the catalog and compares it with the kit.
# MAGIC
# MAGIC To verify again later, for example before a second cohort: set widget 4 to `verify only` and select
# MAGIC **Run all**. Nothing is loaded and nothing is changed.

# COMMAND ----------

problems = []
print(f"{'table':28s} {'rows':>8s}  {'expected':>8s}  result")
for table in TABLES:
    rows, checksum = fingerprint(spark.table(full_name(table)), table)
    ok = (rows, checksum) == EXPECTED[table]
    print(f"{table:28s} {rows:>8,}  {EXPECTED[table][0]:>8,}  {'OK' if ok else 'DIFFERENT'}")
    if not ok:
        problems.append(table)
total = sum(rows for rows, _ in EXPECTED.values())
if problems:
    raise Exception(f"NOT VERIFIED: {', '.join(problems)}. Load these tables again with widget 4 set to csv.")
print(f"\n{len(TABLES)} tables, {total:,} rows")
print("ALL TABLES VERIFIED")
