"""Compare two results of the same logic: five comparisons, and all five must agree.

Two results can share a grand total and still differ in rows, keys, or signs. Parity means that the
schemas, the row keys, the row counts, the signed decimal amounts, and selected aggregates agree.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


@dataclass
class Comparison:
    name: str
    passed: bool
    detail: str


def compare(reference: DataFrame, candidate: DataFrame, row_key: str = "RawRowID",
            amount_columns: Sequence[str] = ("NetAmount",), group_columns: Sequence[str] = ("Currency",)) -> List[Comparison]:
    """Return the five comparisons between a reference result and a candidate result."""
    results = []

    # 1. Schemas: the same column names and types, in the same order.
    ref_schema = [(f.name, f.dataType.simpleString()) for f in reference.schema.fields]
    cand_schema = [(f.name, f.dataType.simpleString()) for f in candidate.schema.fields]
    differences = [f"{name}: {dtype}" for name, dtype in cand_schema if (name, dtype) not in ref_schema]
    differences += [f"missing {name}" for name, _ in ref_schema if name not in dict(cand_schema)]
    same_schema = ref_schema == cand_schema
    results.append(Comparison("schemas", same_schema,
                              f"columns: {len(ref_schema)}, same names and types" if same_schema
                              else "differences: " + "; ".join(differences[:4] or ["column order"])))

    # 2. Key sets: every row key of one result is in the other.
    only_reference = reference.select(row_key).join(candidate.select(row_key), row_key, "left_anti").count()
    only_candidate = candidate.select(row_key).join(reference.select(row_key), row_key, "left_anti").count()
    results.append(Comparison("key sets", only_reference == 0 and only_candidate == 0,
                              f"keys only in the reference: {only_reference:,}; keys only in the candidate: {only_candidate:,}"))

    # 3. Row counts: equal, and no key more than once in either result.
    ref_n, cand_n = reference.count(), candidate.count()
    ref_keys, cand_keys = reference.select(row_key).distinct().count(), candidate.select(row_key).distinct().count()
    results.append(Comparison("row counts", ref_n == cand_n and ref_n == ref_keys and cand_n == cand_keys,
                              f"reference {ref_n:,} rows and {ref_keys:,} keys, candidate {cand_n:,} rows and {cand_keys:,} keys"))

    # 4. Signed decimal amounts: equal for every row, exactly. No tolerance for money.
    usable = [c for c in amount_columns if c in reference.columns and c in candidate.columns]
    joined = (reference.select(row_key, *[F.col(c).alias(f"ref_{c}") for c in usable])
              .join(candidate.select(row_key, *[F.col(c).alias(f"cand_{c}") for c in usable]), row_key))
    differs = F.lit(False)
    for c in usable:
        differs = differs | ~F.col(f"ref_{c}").eqNullSafe(F.col(f"cand_{c}"))
    different_rows = joined.filter(differs).count() if usable else 0
    all_compared = len(usable) == len(amount_columns)
    results.append(Comparison("signed amounts", different_rows == 0 and all_compared,
                              f"rows that differ in {', '.join(amount_columns)}: {different_rows:,}"
                              + ("" if all_compared else "; a compared column is missing")))

    # 5. Selected aggregates: totals of every amount and row counts, for each group.
    def aggregate(df):
        present = [c for c in amount_columns if c in df.columns]
        # Totals are compared as values, at six decimals. A different type is the finding of comparison 1.
        return df.groupBy(*group_columns).agg(F.count(F.lit(1)).alias("rows"),
                                              *[F.sum(c).cast("decimal(38,6)").cast("string").alias(f"sum_{c}")
                                                for c in present])
    ref_agg = {tuple(r[c] for c in group_columns): r.asDict() for r in aggregate(reference).collect()}
    cand_agg = {tuple(r[c] for c in group_columns): r.asDict() for r in aggregate(candidate).collect()}
    different_groups = [k for k in sorted(set(ref_agg) | set(cand_agg), key=str) if ref_agg.get(k) != cand_agg.get(k)]
    results.append(Comparison("aggregates", not different_groups,
                              f"groups by {', '.join(group_columns)}: {len(ref_agg)}, all equal" if not different_groups
                              else f"groups that differ: {len(different_groups)}, for example {different_groups[0]}"))
    return results


def format_comparisons(label: str, comparisons: List[Comparison]) -> str:
    lines = [f"Parity of {label}"]
    for c in comparisons:
        lines.append(f"  {'PASS' if c.passed else 'FAIL'}  {c.name:15s} {c.detail}")
    return "\n".join(lines)
