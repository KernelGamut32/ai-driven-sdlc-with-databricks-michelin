"""Spark session and output location, for every way this project runs.

The same entry points run in four ways: from VS Code with Databricks Connect, from VS Code with
Upload and Run File, from VS Code as a workflow, and from a notebook in the workspace. In each case
Spark processing happens on Databricks compute.
"""
from __future__ import annotations

import os
import re

import lab_config


def get_spark():
    """Return the Spark session of the current run route."""
    if "DATABRICKS_RUNTIME_VERSION" in os.environ:               # the code runs on Databricks compute
        from pyspark.sql import SparkSession
        return SparkSession.builder.getOrCreate()
    try:
        from databricks.connect import DatabricksSession        # local run through Databricks Connect
        return DatabricksSession.builder.getOrCreate()
    except ImportError:
        from pyspark.sql import SparkSession                    # plain Apache Spark
        return SparkSession.builder.getOrCreate()


def output_schema(spark) -> str:
    """The schema that receives the output tables: lab_config.OUTPUT_SCHEMA, or o2i_<your user name>."""
    if lab_config.OUTPUT_SCHEMA:
        return lab_config.OUTPUT_SCHEMA
    user = spark.sql("SELECT current_user() AS u").first()["u"]
    return "o2i_" + re.sub(r"[^a-z0-9]+", "_", user.split("@")[0].lower()).strip("_")


def table_name(schema: str, table: str) -> str:
    """Fully qualified table name in the class catalog. A catalog name with a hyphen needs backticks."""
    catalog = lab_config.CATALOG
    if not re.fullmatch(r"[A-Za-z0-9_]+", catalog):
        catalog = f"`{catalog}`"
    return f"{catalog}.{schema}.{table}"
