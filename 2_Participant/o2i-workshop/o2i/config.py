"""Names and constants shared by the rules and the transformation.

This module imports nothing from Spark, so local tests can use it.
State of Lab 2: the code implements the reviewed logic of Lab 1, which covers rules R2, R5, and R6
of the business contract and the derived amounts. The other rules are open test targets.
"""
from __future__ import annotations

CONTRACT_VERSION = "1.0"
IMPLEMENTED_RULES = ("R2", "R5", "R6")

GRAIN = ("InvoiceID", "LineNumber")

ACCEPTED, QUARANTINED, EXCLUDED = "ACCEPTED", "QUARANTINED", "EXCLUDED"

# A reason code decides the disposition. Every other reason code means QUARANTINED.
EXCLUDED_REASONS = ("NOT_POSTED",)

# Table names inside the input schema, for each dataset that the entry points can process.
DATASET_TABLES = {
    "fixture": {"invoice_lines": "fixture_invoice_lines", "customers": "fixture_customers",
                "products": "fixture_products", "orders": "fixture_orders",
                "expected_results": "fixture_expected_results", "expected_amounts": "fixture_expected_amounts"},
    "training": {"invoice_lines": "invoice_lines", "customers": "customers", "products": "products",
                 "orders": "orders", "expected_results": None, "expected_amounts": None},
}

# Output columns and Spark types, in order. InvoiceDate is still text: rule R4 is not implemented yet.
ACCEPTED_SCHEMA = (
    ("RawRowID", "string"), ("InvoiceID", "string"), ("LineNumber", "int"), ("InvoiceDate", "string"),
    ("DocumentType", "string"), ("CustomerID", "string"), ("CustomerName", "string"), ("Segment", "string"),
    ("Country", "string"), ("Region", "string"), ("ProductID", "string"), ("ProductName", "string"),
    ("ProductLine", "string"), ("OrderID", "string"), ("OrderLineNumber", "int"),
    ("Quantity", "decimal(12,3)"), ("UnitPrice", "decimal(18,4)"), ("NetAmount", "decimal(18,2)"),
    ("TaxRate", "decimal(6,4)"), ("TaxAmount", "decimal(18,2)"), ("GrossAmount", "decimal(18,2)"),
    ("Currency", "string"), ("LoadBatchID", "string"),
)
EXCEPTIONS_SCHEMA = (
    ("RawRowID", "string"), ("InvoiceID", "string"), ("LineNumber", "int"), ("Disposition", "string"),
    ("ReasonCode", "string"), ("Status", "string"), ("InvoiceDate", "string"), ("DocumentType", "string"),
    ("CustomerID", "string"), ("ProductID", "string"), ("OrderID", "string"), ("OrderLineNumber", "int"),
    ("Quantity", "decimal(12,3)"), ("UnitPrice", "decimal(18,4)"), ("NetAmount", "decimal(18,2)"),
    ("TaxRate", "decimal(6,4)"), ("Currency", "string"), ("LoadBatchID", "string"),
)
