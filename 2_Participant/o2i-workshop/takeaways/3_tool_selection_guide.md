# Takeaway 3: Tool-selection guide

Choose the tool that has the right truth in its context. Then check where the code actually runs.

## Where to start

| Task | Start with | Evidence, and the boundary |
|---|---|---|
| Understand a table, or debug the result of a notebook | Databricks with Genie Code | It sees the schema, the comments, and the output of a cell. Review the actual schema and the actual output. |
| Extract a helper, restructure a module, write a test | VS Code with GitHub Copilot | It sees the whole project and its instructions. Inspect a small diff and run the local code tests. |
| Validate joins, volumes, and governed data access | Approved Databricks compute | Run the transformation and the data-quality checks on the real tables. |
| Accept a change for technical review | A developer and a reviewer | Explain the behavior, the tests, the risks, and the limits. No tool does this for you. |

## Four questions for your next task

| Question | It points to Databricks when | It points to VS Code when |
|---|---|---|
| Context: what must the assistant see? | The answer is in the data, a table comment, or a cell output | The answer is in several files, tests, or project instructions |
| Execution: what must run to prove the result? | Spark, tables, governed data | Plain Python functions and their tests |
| Maintainability: who has to live with the result? | A one-off analysis or an exploration | Code that will be reviewed, versioned, and reused |
| Cost: what is metered? | Genie Code usage for each user, and the compute that runs the cells | Copilot usage from the organization's pool. Spark work still runs on Databricks compute. |

Neither tool is always cheaper. A vague request that needs three corrections costs more than a
bounded request, in both tools. Measure time to a verified result, and rework. Do not measure
generated lines.

## What runs where

| You do this | It runs |
|---|---|
| Edit a file in VS Code | On your workstation |
| Run the code tests (`python tools/run_tests.py`) | On your workstation. Plain Python, no Spark. |
| Run a `run_*.py` file on Databricks from VS Code | On Databricks compute. Your workstation sends the files and shows the output. |
| Use Databricks Connect | Your Python code runs on the workstation. Every Spark operation runs on Databricks compute. |
| Run a notebook cell | On Databricks compute |

Editing locally does not make Spark local, and it does not make it free.

## One source of truth

- A notebook prototype stays in a scratch location.
- After the extraction, the version-controlled project owns the code.
- The folder that the IDE synchronizes to the workspace is a one-way mirror. Never edit the mirror.
- The revision ties both sides together: the revision that you reviewed must be the revision that ran.
