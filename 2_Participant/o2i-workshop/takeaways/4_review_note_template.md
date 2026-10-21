# Takeaway 4: Review note

A review note is the handoff into the review process that your team already has. It replaces
nothing: the pull request, the reviewer, and the approval stay as they are. Keep it to one screen.

```text
REVIEW NOTE

Purpose
  <What the change is for, in one or two sentences. Name the requirement or the change request.>

Code revision
  <Commit or revision that was reviewed>     <The same revision, as printed by the run on Databricks>

Changed behavior
  <What is different for the data now. Name rules, reason codes, columns.>
  <What did not change, where a reader could expect a change.>

Test and data evidence
  Before:  <the test or check that failed, with the number or the record keys>
  After:   <the same test or check, passing>
  Regression: <code tests: n passed. Data-quality checks: n passed, on which datasets.>
  Accountability: <delivered rows = accepted + exceptions, with the three numbers>

Remaining risks and limits
  <What the change does not do. What was not tested. What depends on the environment.>

AI assistance
  <Which assistant wrote or proposed what. What you declined or corrected, and why.>

Questions for the tech lead
  <Decisions that are not yours: a business rule, a data owner, a release step.>

Reviewer: <name>          Date: <date>
```

Three rules for the note:

1. Every number in it comes from a run that you can repeat, not from an AI answer.
2. "Remaining risks" is never empty. A change without limits has not been examined.
3. If you cannot fill in "Changed behavior" without the assistant open, the change is not ready.
