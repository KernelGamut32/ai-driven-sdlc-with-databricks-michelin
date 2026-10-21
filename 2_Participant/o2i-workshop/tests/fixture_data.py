"""Load the approved fixture files of tests/fixtures as plain Python values. No Spark needed.

The files are copies of the fixture tables in the training schema: 56 delivered invoice lines in
48 cases, tiny master and order tables, and the hand-written expected results.
"""
from __future__ import annotations

import csv
import os
from decimal import Decimal
from typing import Dict, List

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

_DECIMAL = {"Quantity", "UnitPrice", "NetAmount", "TaxRate", "OrderedQuantity", "AgreedUnitPrice",
            "ExpectedTaxAmount", "ExpectedGrossAmount", "CreditLimit", "ListPrice", "WeightKg", "RimDiameterInch"}
_INT = {"LineNumber", "OrderLineNumber"}


def load(name: str) -> List[Dict[str, object]]:
    """Read tests/fixtures/<name>.csv. An empty field is None. Text keeps its spaces."""
    rows = []
    with open(os.path.join(FIXTURE_DIR, f"{name}.csv"), newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            row = {}
            for column, text in record.items():
                if text == "":
                    row[column] = None
                elif column in _DECIMAL:
                    row[column] = Decimal(text)
                elif column in _INT:
                    row[column] = int(text)
                else:
                    row[column] = text
            rows.append(row)
    return rows
