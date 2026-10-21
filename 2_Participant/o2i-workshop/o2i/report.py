"""Plain-text output of the entry points: one header that names the revision, then the numbers."""
from __future__ import annotations

from typing import Dict, List

import lab_config
from o2i import config, revision


def print_header(spark, schema: str) -> None:
    scope = ", ".join(config.IMPLEMENTED_RULES)
    print(f"{revision.describe()} | contract {config.CONTRACT_VERSION}, rules {scope} only | Spark {spark.version}")
    print(f"input {lab_config.CATALOG}.{lab_config.INPUT_SCHEMA} | output {lab_config.CATALOG}.{schema}")


def print_outcomes(dataset: str, names: Dict[str, str], rows: List[tuple]) -> None:
    total = sum(n for _, _, n in rows)
    print(f"\nDataset '{dataset}': {total:,} rows written to {names['accepted']} and {names['exceptions']}")
    for disposition, reason, n in rows:
        print(f"  {disposition:12s} {reason:24s} {n:>8,}")
