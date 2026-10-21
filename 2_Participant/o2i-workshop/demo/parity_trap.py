"""Parity trap: four results that share a grand total with the reference, and none of them is equal to it.

Run this file on Databricks, in the same way as the run_*.py entry points. It reads no table and
writes nothing, so it is also the quickest test of your run route.

The reference is a small accepted dataset. Each candidate is what a plausible change would produce.
All five have the same EUR grand total. The five comparisons of o2i.parity tell them apart:
schemas, key sets, row counts, signed amounts, and aggregates.
"""
import os
import sys
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "demo" else HERE
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pyspark.sql import functions as F  # noqa: E402

from o2i import parity, revision  # noqa: E402
from o2i.session import get_spark  # noqa: E402

SCHEMA = "RawRowID string, Segment string, Currency string, NetAmount decimal(18,2)"

REFERENCE = [
    ("T01", "DEALER", "EUR", D("1200.00")),
    ("T02", "DEALER", "EUR", D("250.00")),
    ("T03", "FLEET", "EUR", D("980.50")),
    ("T04", "FLEET", "EUR", D("-250.00")),      # a valid credit
    ("T05", "OEM", "EUR", D("4310.25")),
    ("T06", "OEM", "EUR", D("1200.00")),
    ("T07", "DEALER", "USD", D("760.00")),
    ("T08", "FLEET", "USD", D("-95.40")),       # a valid credit
]


def changed(rows, **replacements):
    """A copy of the rows in which the rows named by RawRowID are replaced."""
    return [replacements.get(row[0], row) for row in rows]


CANDIDATES = {
    # A cast in a "harmless" cleanup step: every value is equal, the type is not.
    "money as double": None,
    # One line vanished in an inner join, another line met a master key with two rows.
    # Both lines have the same amount, so the count and the total are unchanged.
    "one line lost, one line doubled": [row for row in REFERENCE if row[0] != "T06"] + [REFERENCE[0]],
    # abs() on one credit, and a lost sign on an invoice of the same size.
    "two signs flipped": changed(REFERENCE, T02=("T02", "DEALER", "EUR", D("-250.00")),
                                 T04=("T04", "FLEET", "EUR", D("250.00"))),
    # An ambiguous customer: another master row was picked, so the line moved to another segment.
    "another master row picked": changed(REFERENCE, T05=("T05", "DEALER", "EUR", D("4310.25"))),
}


def eur_total(df):
    return df.filter(F.col("Currency") == "EUR").agg(F.sum("NetAmount").cast("decimal(18,2)")).first()[0]


def main() -> int:
    spark = get_spark()
    print(f"{revision.describe()} | Spark {spark.version}")
    reference = spark.createDataFrame(REFERENCE, SCHEMA)
    print(f"\nReference: {reference.count()} rows, EUR grand total {eur_total(reference)}")

    equal = 0
    for name, rows in CANDIDATES.items():
        if rows is None:
            candidate = reference.withColumn("NetAmount", F.col("NetAmount").cast("double"))
        else:
            candidate = spark.createDataFrame(rows, SCHEMA)
        comparisons = parity.compare(reference, candidate, amount_columns=("NetAmount",),
                                     group_columns=("Currency", "Segment"))
        failed = [c.name for c in comparisons if not c.passed]
        equal += 0 if failed else 1
        print()
        print(parity.format_comparisons(f"candidate '{name}': EUR grand total {eur_total(candidate)}", comparisons))
        print(f"  -> the grand total agrees. Comparisons that fail: {len(failed)} of 5 ({', '.join(failed)})")

    print(f"\nPARITY TRAP: {len(CANDIDATES)} candidates share the EUR grand total of the reference. "
          f"Candidates that are equal to it: {equal} of {len(CANDIDATES)}.")
    return equal


if __name__ == "__main__":
    main()
