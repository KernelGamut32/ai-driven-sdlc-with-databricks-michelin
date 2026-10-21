"""Run the O2I transformation and write the output tables.

Processes the datasets of lab_config.DATASETS. Spark work runs on Databricks compute, whichever
way you start this file.
"""
import lab_config
from o2i import report, transform
from o2i.session import get_spark, output_schema


def main():
    spark = get_spark()
    schema = output_schema(spark)
    report.print_header(spark, schema)
    for dataset in lab_config.DATASETS:
        outputs = transform.build_outputs(spark, dataset)
        names = transform.write_outputs(outputs, schema, dataset)
        report.print_outcomes(dataset, names, transform.outcome_counts(spark, names))


if __name__ == "__main__":
    main()
