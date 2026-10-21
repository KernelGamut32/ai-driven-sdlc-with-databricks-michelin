"""Class configuration for the O2I workshop project.

tools/prepare_cohort.py (instructor) writes CATALOG for your class. During the labs you change
DATASETS and, for a trace, TRACE_DATASET and TRACE_ROWS.
"""

CATALOG = "o2iworkshop"              # Unity Catalog catalog of the class
INPUT_SCHEMA = "o2i"          # read-only training tables
OUTPUT_SCHEMA = None          # None: derive o2i_<your user name> from the signed-in user

# Datasets that the run_*.py entry points process, in this order.
#   "fixture"    56 hand-verifiable rows with expected results (seconds)
#   "training"   about 50,000 invoice lines
#   "challenge"  the Lab 4 batch, with expected results
DATASETS = ["fixture", "training"]

# Rows that run_trace.py follows through the rules (Lab 3): a dataset, and RawRowID values of that dataset.
TRACE_DATASET = "fixture"
TRACE_ROWS = ["F0005", "F0017", "F0049"]
