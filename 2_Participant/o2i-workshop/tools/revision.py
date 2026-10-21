"""Print the revision of the o2i package on this machine.

    python tools/revision.py

Compare the fingerprint with the first line that a run on Databricks prints. When both are equal,
the code that ran on Databricks is the code that you reviewed here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from o2i import config, revision  # noqa: E402

if __name__ == "__main__":
    print(f"{revision.describe()} | contract {config.CONTRACT_VERSION}")
