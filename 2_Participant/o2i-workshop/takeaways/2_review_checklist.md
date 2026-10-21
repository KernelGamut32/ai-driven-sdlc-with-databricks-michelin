# Takeaway 2: Code and data review checklist

Use it for a change that an assistant wrote, and for a change that you wrote. The questions are
the same.

## Before it runs: inspect

| Look for | Because |
|---|---|
| A file, function, or cell that you did not name | The change is larger than the request |
| A new import, package, UDF, shell command, or network call | Dependencies and commands need approval, not momentum |
| `filter`, an inner join, `dropDuplicates`, `dropna`, `limit` | Each of them can lose rows without an error |
| A join to a table whose key is not proven unique | One line becomes two, and every total grows |
| A delivered value that is overwritten, trimmed, filled, or defaulted | The evidence is gone, and the report looks cleaner than the data |
| `double` or `float` for money, `abs()`, a filter on positive amounts, arithmetic with NULL | Precision, signs, and missing values change totals silently |
| An edited test, expected value, fixture, or contract | The oracle was changed to fit the code |

## After it ran: validate

"The code ran" is not evidence. These six questions are the test matrix of the workshop.

| Question | Evidence that answers it |
|---|---|
| Behavior and precision: does each function do what the rule says? | Code tests with expected values calculated by hand. Include a NULL, a rounding tie, and a credit. |
| Schema and required fields: does the output have the agreed shape? | Columns and types equal the contract. No NULL in a column that must be filled. |
| Uniqueness and replay: is every business key in the output once? | One accepted row for each key. Replays are documented. Conflicting rows are held, not chosen. |
| Relationships and joins: did a join lose or multiply rows? | Every accepted key has exactly one master row. Row counts by key before and after each join. |
| Business rules: are the right rows in and the right rows out? | Only allowed status values are accepted. A valid credit is accepted with its sign. |
| Reconciliation and regression: is every row accounted for, and did nothing else move? | Delivered rows = accepted + exceptions, by row key. Totals for each currency. Fixture, parity, and the full suite pass. |

## Before you say "review ready": explain

All five, or the verdict is "needs rework".

1. **Correctness.** The result matches expected cases that did not come from the code.
2. **Regression protection.** A test or check failed before the change and passes after it. Everything that passed before still passes.
3. **Data accountability.** No silent loss and no fan-out. Accepted rows and exception rows reconcile with the delivered rows.
4. **Cross-tool fidelity.** The revision that you reviewed is the revision that ran on Databricks.
5. **Human understanding.** You can explain the behavior and its limits without reading an AI answer.

Three things you never do to get a green run: delete a failing assertion, skip it, or weaken it.
