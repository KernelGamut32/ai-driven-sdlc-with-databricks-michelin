# Lab requests, ready to paste

Every request of Labs 1 to 4, in the order of the Participant Workbook. A request is a starting
point: read it before you send it, and change it when your situation differs.

Three rules hold for every request in this file:

1. The assistant proposes. You review the change before anything runs.
2. You run the tests and the checks yourself.
3. An answer that edits a test, a fixture, the contract, or a file that you did not name is declined.

## Lab 1. Genie Code, in the notebook

### Context, at the end of your own prompt from Exercise 1

```text
In this notebook I will ask for one small step at a time. Change only the cell that I name.
Do not run anything unless I ask. Do not write code yet.
First list the assumptions that you would have to make about this data, and wait for my answer.
```

### Task 1

```text
Complete only the cell that starts with "# TASK 1". Keep every row of `lines` and every delivered
column unchanged, and add three columns:
- StatusClass: 'POSTED' when Status, trimmed and in upper case, is POSTED. 'NOT_POSTED' when it is
  DRAFT or CANCELLED. 'UNEXPECTED' for any other value, including NULL.
- TaxAmount: NetAmount x TaxRate, rounded half up to 2 decimals, as DECIMAL(18,2).
  When TaxRate is NULL, no tax applies: 0.00.
- GrossAmount: NetAmount + TaxAmount, as DECIMAL(18,2).
Do not filter. Do not overwrite Status. Do not run the cell: I review it first.
```

### Task 2, reference request

Write your own request first. Use this one when you are stuck for more than two minutes.

```text
Complete only the cell that starts with "# TASK 2". Add two columns to `prepared` and name the
result `matched`:
- CustomerMatches: the number of rows in `customers` with exactly this CustomerID. 0 when there is none.
- ProductMatches: the number of rows in `products` with exactly this ProductID. 0 when there is none.
`matched` must have exactly one row for each row of `prepared`. Aggregate each master table to one
row for each key before you join it. Do not join the master attributes yet. Do not trim a key and
do not change its case. Do not run the cell: I review it first.
```

### Task 3

```text
Complete only the cell that starts with "# TASK 3".
1. Add ReasonCode to `matched`. The first rule that fails decides: NOT_POSTED when StatusClass is
   NOT_POSTED. UNEXPECTED_STATUS when StatusClass is UNEXPECTED. UNKNOWN_CUSTOMER when CustomerMatches
   is 0, AMBIGUOUS_CUSTOMER when it is above 1. UNKNOWN_PRODUCT and AMBIGUOUS_PRODUCT in the same way
   for ProductMatches. Otherwise NULL.
2. Add Disposition: ACCEPTED when ReasonCode is NULL, EXCLUDED for NOT_POSTED, QUARANTINED for every
   other reason.
3. `accepted`: the ACCEPTED rows, joined to `customers` for CustomerName, Segment, Country, Region,
   and to `products` for ProductName, ProductLine.
4. `exceptions`: every other row. No row may be dropped, and no missing value may be filled.
Do not select or rename columns: the next cell does that. Do not run the cell: I review it first.
```

## Lab 2. GitHub Copilot, in VS Code

### Request 2.1: orient, without an edit (step 1)

```text
Read AGENTS.md, scratch/lab1_reviewed.py, o2i/transform.py, and o2i/rules.py. Do not edit any file.
1. Three functions in o2i/transform.py and two functions in o2i/rules.py raise NotImplementedError.
   For each of them, name the lines of scratch/lab1_reviewed.py that hold its logic.
2. List everything in scratch/lab1_reviewed.py that you would be tempted to improve while you move
   it. I want the logic moved, not improved.
3. List the assumptions that you make about the data.
```

### Request 2.2: move the logic (step 2)

```text
Complete count_master_matches, decide, and with_amounts in o2i/transform.py. Move the logic from
scratch/lab1_reviewed.py without changing its meaning.
- Keep every function signature and every docstring.
- Use the names of o2i/config.py where the module already uses them.
- Edit only o2i/transform.py. Do not touch scratch/, tests/, docs/, or any other file.
- No new import and no new dependency. No pandas, no UDF, no cache, no persist.
- Do not run anything. I run the tests myself.
After the edit, list each function that you changed and the lines of lab1_reviewed.py that it came from.
```

### Request 2.3: the plain-Python twins (step 3)

```text
Write tax_amount and gross_amount in o2i/rules.py. They are the plain-Python twins of the Spark
expressions in with_amounts in o2i/transform.py.
- Decimal in, Decimal out. Pass every argument through _as_decimal, so that a float raises TypeError.
- Round half up to two decimals with round_half_up.
- A tax rate of None means that no tax applies: the tax is 0.00. A tax rate of 0 is a rate.
- A credit stays negative.
Edit only o2i/rules.py. Do not edit the tests. Do not run anything.
Then tell me, without running code, what tax_amount(Decimal("3.00"), Decimal("0.0550")) and
tax_amount(Decimal("-3.00"), Decimal("0.0550")) return, and why.
```

## Lab 3. GitHub Copilot, in VS Code

### Request 3.1: the test cases that are missing (step 1)

```text
Read docs/business_contract.md, tests/unit/test_rules.py, and tests/unit/test_fixture.py.
Do not edit any file. Do not take any expected value from o2i/rules.py or o2i/transform.py.
List up to eight cases of the business contract that no code test covers yet. For each case give:
the rule or section of the contract, concrete input values, the expected result, and how you
derived the expected result from the contract.
Mark every expected result that you calculated yourself with CHECK BY HAND.
```

### Request 3.2: two code tests (step 2)

```text
In tests/unit/test_rules.py, replace the placeholder bodies of test_tax_rounds_half_up_on_a_tie and
test_tax_of_a_credit_rounds_away_from_zero_on_a_tie with real tests.
Use these cases. I verified them by hand against the contract and the fixture workbook:
- net 3.00 at rate 0.0550: tax 0.17, gross 3.17
- net 0.50 at rate 0.2100: tax 0.11
- net -3.00 at rate 0.0550: tax -0.17, gross -3.17
Write the expected values as Decimal literals. Do not compute an expected value with the function
under test. Edit only these two tests. Do not edit anything in o2i/. Do not run anything.
```

### Request 3.3: three data-quality checks (step 3)

```text
In o2i/checks.py, implement the three checks whose docstrings say "LAB 3, CHECK 1", "LAB 3, CHECK 2",
and "LAB 3, CHECK 3": reconciliation, conflicts_held, and signed_amounts. Each docstring is the
specification. Keep the docstrings.
- Follow the style of the checks that are already implemented in this file: read from ctx, return
  a CheckResult, and use _keys for the evidence.
- A check reports. It never changes data, and it never filters the delivered rows to make itself pass.
- PySpark DataFrame API only. Do not collect a full table. No pandas and no UDF.
Edit only these three functions. Do not edit o2i/transform.py or o2i/rules.py. Do not run anything.
```

### Request 3.4: from a failing check to a decision in the code (step 4)

Replace the text in angle brackets with the output of your own run.

```text
The data-quality check signed_amounts fails on the training data. Its output is:
<paste the line of the check and its evidence lines>
Do not edit any file. Read o2i/transform.py and name the one expression that decides AMOUNT_MISMATCH.
Show with the values of <one RawRowID from the evidence> why that line is held.
Then say what the smallest correction is, and which rows would change their outcome.
```

### Request 3.5: the smallest fix (step 5)

Send it once for each cause, after you have named the cause yourself.

```text
Make the smallest change in <o2i/rules.py or o2i/transform.py> that corrects this cause:
<the cause, in your own words>
No refactoring and no renaming. Do not change tests, checks, fixtures, or documents.
Then tell me which code tests and which data-quality checks I should run, and what each of them
should show.
```

## Lab 4. Your choice of tool

### Request 4.1: the acceptance cases, before any code (step 1)

```text
Read docs/change_request_CR-2026-041.md and docs/business_contract.md. Do not edit any file.
List the acceptance cases of rule R8 as a table: situation, example values, expected disposition,
expected reason code. Include a case in which an earlier rule decides first, a valid credit, and an
exact replay. Then list what the change request says the rule does not do.
```

### Request 4.2: the tests that must fail first (step 2)

```text
In tests/unit/test_rules.py, add the decision tests for rule R8. Edit only this file.
- In the helper decide(), the clean line gets order_ref_present=True and order_matches=1.
- test_each_rule_has_its_reason: add MISSING_ORDER_REF (order_ref_present False), UNKNOWN_ORDER_REF
  (order_matches 0), and AMBIGUOUS_ORDER_REF (order_matches 2). All three are QUARANTINED.
- test_the_first_failing_rule_decides: add one case that shows rule R7 before rule R8.
- test_every_reason_is_a_reason_of_the_contract: add the three new situations.
These tests will fail until the rule exists. That is intended. Do not change o2i/. Do not run anything.
```

### Request 4.3: the bounded change (step 3)

```text
Implement rule R8 of docs/change_request_CR-2026-041.md. Read AGENTS.md and the change request first.
Scope:
- o2i/rules.py: decide_disposition gets two keyword arguments, order_ref_present and order_matches,
  and three outcomes after rule R7. evaluate_rows gets the order lines as a fourth argument and
  computes both facts for every row.
- o2i/transform.py: read the orders table. In add_facts, add the facts f_order_ref_present and
  f_order_matches: count the order lines for each OrderID and OrderLineNumber and join the count, as
  the customer and product rules do. Extend decide after rule R7. No inner join and no filter.
- Update every caller of a function whose signature you change, in o2i/ and in tests/.
Do not change the order or the meaning of rules R1 to R7. Do not change an expected value, a fixture
file, or an assertion that exists today.
The rule checks that the order line exists, with OrderID and OrderLineNumber together. It does not
compare quantity, price, customer, product, or order status.
Do not run anything. When you are done, list every file that you changed. For each new line of the
decision, name the acceptance case that it serves.
```

### Request 4.4: a data-quality check for the new rule (optional)

```text
In o2i/checks.py, add a check named order_reference and put it into CHECKS after
referential_integrity. It passes when every row of ctx.accepted has an OrderID and an
OrderLineNumber that match exactly one row of ctx.orders. Evidence: up to five accepted rows that
do not, as RawRowID / OrderID / OrderLineNumber. Follow the style of referential_integrity.
Edit only o2i/checks.py. Do not run anything.
```

### Request 4.5: the contract document (optional)

```text
Update docs/business_contract.md to version 1.1 with the text of docs/change_request_CR-2026-041.md:
the version line, the row of the orders table in section 2, rule R8 in the table of section 4, one
detail line for R8, and the change history. Change nothing else in the document.
```
