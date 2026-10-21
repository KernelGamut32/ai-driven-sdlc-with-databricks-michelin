"""Compare the module (o2i.transform) with the reviewed logic of Lab 1 (scratch/lab1_reviewed.py).

For each dataset of lab_config.DATASETS, both outputs are compared in five ways: schemas, key sets,
row counts, signed amounts, and aggregates. On the fixture, the amounts of the module are also
compared with the plain-Python rules. Parity means that every line says PASS.
"""
import lab_config
from o2i import parity, report, rules, transform
from o2i.session import get_spark, output_schema
from scratch.lab1_reviewed import lab1_outputs


def main() -> int:
    spark = get_spark()
    report.print_header(spark, output_schema(spark))
    failed = 0
    for dataset in lab_config.DATASETS:
        reference_accepted, reference_exceptions = lab1_outputs(spark, dataset)
        module = transform.build_outputs(spark, dataset)
        accepted = parity.compare(reference_accepted, module.accepted,
                                  amount_columns=("NetAmount", "TaxAmount", "GrossAmount"), group_columns=("Currency",))
        exceptions = parity.compare(reference_exceptions, module.exceptions,
                                    amount_columns=("NetAmount",), group_columns=("Disposition", "ReasonCode"))
        print()
        print(parity.format_comparisons(f"accepted lines, dataset '{dataset}'", accepted))
        print(parity.format_comparisons(f"exceptions, dataset '{dataset}'", exceptions))
        failed += sum(1 for c in accepted + exceptions if not c.passed)
        if dataset == "fixture":
            # A line without NetAmount has no amount to compare. Rule R1 will hold such lines: it is not implemented yet.
            rows = (module.accepted.filter("NetAmount IS NOT NULL")
                    .select("RawRowID", "NetAmount", "TaxRate", "TaxAmount", "GrossAmount").collect())
            differs = [r["RawRowID"] for r in rows
                       if (rules.tax_amount(r["NetAmount"], r["TaxRate"]), rules.gross_amount(r["NetAmount"], r["TaxRate"]))
                       != (r["TaxAmount"], r["GrossAmount"])]
            print(f"  {'PASS' if not differs else 'FAIL'}  rules agreement {len(rows) - len(differs)} of {len(rows)} "
                  f"accepted fixture amounts equal o2i.rules"
                  + (f"; differing rows: {', '.join(differs[:5])}" if differs else ""))
            failed += 1 if differs else 0
    print(f"\nPARITY: {'ALL COMPARISONS PASS' if failed == 0 else 'NOT REACHED, failed comparisons: ' + str(failed)}")
    return failed


if __name__ == "__main__":
    main()
