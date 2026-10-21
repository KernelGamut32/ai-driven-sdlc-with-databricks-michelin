"""Spark transformation for the first reviewed version of the accepted invoice dataset.

This module is the reviewed logic of Lab 1 (scratch/lab1_reviewed.py), split into small functions.
It covers rules R2, R5, and R6 of the business contract and the derived amounts:

    read_inputs -> classify_status -> count_master_matches -> decide -> build_outputs -> write_outputs

Every delivered row keeps exactly one outcome. No step filters, drops, or multiplies a row before
the outputs are split. The plain-Python twin of the status rule and of the amounts is in o2i.rules.
"""
from __future__ import annotations

from typing import Dict, Iterable, NamedTuple

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

import lab_config
from o2i import config
from o2i.session import table_name


class Outputs(NamedTuple):
    accepted: DataFrame       # one row for each accepted delivered row, enriched
    exceptions: DataFrame     # every other delivered row, as delivered, with Disposition and ReasonCode


def read_inputs(spark, dataset: str) -> Dict[str, DataFrame]:
    """Read the input tables of a dataset: invoice_lines, customers, products."""
    tables = config.DATASET_TABLES[dataset]
    return {name: spark.table(table_name(lab_config.INPUT_SCHEMA, tables[name]))
            for name in ("invoice_lines", "customers", "products")}


def classify_status(lines: DataFrame) -> DataFrame:
    """Add StatusClass: POSTED, NOT_POSTED, or UNEXPECTED. Twin of rules.classify_status.

    The status is compared trimmed and in upper case. The delivered value stays as it is.
    """
    status = F.upper(F.trim(F.col("Status")))
    return lines.withColumn("StatusClass",
                            F.when(status == "POSTED", "POSTED")
                             .when(status.isin("DRAFT", "CANCELLED"), "NOT_POSTED")
                             .otherwise("UNEXPECTED"))


def count_master_matches(lines: DataFrame, customers: DataFrame, products: DataFrame) -> DataFrame:
    """Add CustomerMatches and ProductMatches: how many master rows has each key?

    The count is joined, never the attributes, so this step cannot lose a line and cannot multiply a line.
    """
    raise NotImplementedError("Lab 2: move this logic from scratch/lab1_reviewed.py")


def decide(lines: DataFrame) -> DataFrame:
    """Add ReasonCode and Disposition. The first rule that fails decides, in the order of the contract."""
    raise NotImplementedError("Lab 2: move this logic from scratch/lab1_reviewed.py")


def with_amounts(lines: DataFrame) -> DataFrame:
    """Add TaxAmount and GrossAmount. Twin of rules.tax_amount and rules.gross_amount.

    Spark's round() rounds half up. No tax rate means that no tax applies: without coalesce,
    TaxAmount and GrossAmount would be NULL for these lines.
    """
    raise NotImplementedError("Lab 2: move this logic from scratch/lab1_reviewed.py")


def _in_schema(df: DataFrame, schema: Iterable) -> DataFrame:
    return df.select(*[F.col(name).cast(dtype).alias(name) for name, dtype in schema])


def build_outputs(spark, dataset: str) -> Outputs:
    """Apply the implemented rules to one dataset and return the accepted lines and the exceptions."""
    inputs = read_inputs(spark, dataset)
    decided = decide(count_master_matches(classify_status(inputs["invoice_lines"]),
                                          inputs["customers"], inputs["products"]))

    # An accepted line has exactly one customer row and one product row (R5, R6),
    # so these joins cannot multiply or lose a line.
    customer_attributes = inputs["customers"].select("CustomerID", "CustomerName", "Segment", "Country", "Region")
    product_attributes = inputs["products"].select("ProductID", "ProductName", "ProductLine")
    accepted = with_amounts(decided.filter(F.col("Disposition") == config.ACCEPTED)
                            .join(customer_attributes, "CustomerID", "left")
                            .join(product_attributes, "ProductID", "left"))
    exceptions = decided.filter(F.col("Disposition") != config.ACCEPTED)
    return Outputs(_in_schema(accepted, config.ACCEPTED_SCHEMA), _in_schema(exceptions, config.EXCEPTIONS_SCHEMA))


def write_outputs(outputs: Outputs, schema: str, dataset: str) -> Dict[str, str]:
    """Write both outputs as tables <dataset>_accepted and <dataset>_exceptions. Returns their names."""
    names = {"accepted": table_name(schema, f"{dataset}_accepted"),
             "exceptions": table_name(schema, f"{dataset}_exceptions")}
    for key, df in (("accepted", outputs.accepted), ("exceptions", outputs.exceptions)):
        df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(names[key])
    return names


def outcome_counts(spark, names: Dict[str, str]) -> list:
    """Rows by outcome, read from the written tables: [(disposition, reason, rows), ...]."""
    accepted_rows = spark.table(names["accepted"]).count()
    rows = [(config.ACCEPTED, "", accepted_rows)]
    grouped = (spark.table(names["exceptions"]).groupBy("Disposition", "ReasonCode").count()
               .orderBy("Disposition", "ReasonCode").collect())
    rows += [(r["Disposition"], r["ReasonCode"], r["count"]) for r in grouped]
    return rows
