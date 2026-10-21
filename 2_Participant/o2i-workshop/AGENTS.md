# Instructions for AI coding assistants in this project

This project builds the accepted invoice dataset of the order-to-invoice (O2I) case. The business
contract is `docs/business_contract.md`. Read it before you propose a change. When this file and
the contract disagree, the contract wins.

## Layout

- `o2i/rules.py`: the business rules in plain Python. No Spark, standard library only.
- `o2i/transform.py`: the same rules for full tables, in PySpark. Runs on Databricks compute.
- `o2i/checks.py`: data-quality checks on the written output tables.
- `tests/unit/`: code tests for `o2i/rules.py`. They use `unittest` and need no installed package.
- `tests/fixtures/`: the approved fixture and its expected results.
- `run_*.py`: thin entry points. They contain no business logic.
- `docs/`: the business contract, the data dictionary, and change requests.
- `scratch/`: a notebook prototype that is kept as a reference. Never edit it.
- `tools/`, `checkpoints/`, `.backups/`: course tooling. Never change it, and do not read `checkpoints/` or `.backups/`.

## Hard rules

1. Add no dependency. Use the Python standard library and PySpark only. No pandas, no new test framework.
2. Money is `decimal.Decimal` in Python and `DECIMAL` in Spark. Never use float or double for an amount.
3. Round half up to two decimals. Never compare amounts with a tolerance.
4. Keep the sign of every amount. Never use `abs()` on an amount and never filter out negative amounts.
5. Never drop a delivered row. A row that is not accepted goes to the exception output with a reason code.
6. Never choose one of several rows for a business key: no `dropDuplicates` on a key, no "latest row wins".
7. Never change a delivered value. Normalize only inside a comparison.
8. Never edit an expected value, a fixture file, or the contract to make a test or check pass.
9. Never delete, skip, or weaken a test or a check. If you think a test is wrong, say why and stop.

## How to work

- Before you write code, list your assumptions about the data and the rule, and wait for an answer.
- Make the smallest change that satisfies the request. Do not refactor code that the request does not name.
- Change `o2i/rules.py` and `o2i/transform.py` together when a rule changes, so that both still agree.
- After a change, say which tests and checks should be run, and what you expect them to show.
- If a request conflicts with a hard rule or with the contract, say so instead of complying.

The developer reviews every change and is accountable for it. These instructions guide you. They do
not replace the review.
