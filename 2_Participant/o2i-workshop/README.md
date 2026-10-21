# O2I workshop project

Course project of the workshop "AI-Driven SDLC with Databricks". It builds the accepted invoice
dataset of the order-to-invoice (O2I) case and its exception report. All data is fictional.

The Participant Workbook has the steps of every lab. This file is a map.

| You want to | Use |
|---|---|
| Read the rules | `docs/business_contract.md` |
| Look up a column | `docs/data_dictionary.md` |
| Run the code tests on your workstation | `python tools/run_tests.py` |
| See which revision you have | `python tools/revision.py` |
| Run the transformation on Databricks | `run_transform.py` |
| Run the transformation and every data-quality check on Databricks | `run_checks.py` |
| Run the full regression suite | `run_all.py` |
| Follow chosen delivered rows through the rules | `run_trace.py`, with `TRACE_ROWS` in `lab_config.py` |
| Load the starting point of a lab | `python tools/checkpoint.py <name>` |
| See what changed since the last checkpoint | `python tools/checkpoint.py diff` |
| Paste a request of a lab | `prompts/LAB_PROMPTS.md` |
| Work without an assistant | `python tools/checkpoint.py prepared <lab>`, and the folder `prepared_ai_outputs` of your package |
| Keep for your daily work | `takeaways/`: prompt patterns, review checklist, tool-selection guide, review note |

`lab_config.py` holds the catalog of your class and the datasets that a run processes.

Code tests run on your workstation and need only Python. Everything that touches a table runs on
Databricks compute, whichever way you start it.
