"""Run the code tests of this project and print one summary line.

    python tools/run_tests.py            all tests
    python tools/run_tests.py -v         one line for each test

The tests use unittest from the Python standard library, so nothing has to be installed.
`python -m unittest` and, where it is installed, `pytest` run the same tests.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, "tests"), top_level_dir=ROOT)
    verbosity = 2 if "-v" in sys.argv[1:] else 1
    outcome = unittest.TextTestRunner(stream=sys.stdout, verbosity=verbosity).run(suite)
    # A test with several failing sub-cases counts as one failed test. A skipped test is not a passed test.
    bad = len({getattr(test, "test_case", test).id() for test, _ in outcome.failures + outcome.errors})
    skipped = len(outcome.skipped)
    print(f"{outcome.testsRun - bad - skipped} passed, {bad} failed" + (f", {skipped} skipped" if skipped else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
