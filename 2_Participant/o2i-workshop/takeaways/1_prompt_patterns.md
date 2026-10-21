# Takeaway 1: Prompt patterns

A prompt is a specification. An assistant fills every gap in it with an assumption, and it does
not tell you which ones unless you ask.

## The bounded request: six ingredients

| Ingredient | Write down | In the workshop case |
|---|---|---|
| Business intent | What the result is for, and who uses it | Accepted invoice lines for a revenue report |
| Input schema and grain | The tables, what one row is, the keys, and what nothing guarantees | One row is one delivery of an invoice line. A line can be delivered more than once. No master key is enforced. |
| Expected result | Columns, types, and grain of the output, and where every other row goes | One row for each accepted line. Every other delivered row in an exception output, with a reason code. |
| Permitted libraries | Language, API, and what must not be added | PySpark DataFrame API or SQL. No pandas, no UDF, no new package. |
| Error behavior | What happens to NULL, an unknown key, a duplicate key, an invalid value | Never drop a row, never fill a value, never choose one of several rows. |
| Acceptance criteria | The checks that you will run, with numbers where you have them | Delivered rows = accepted rows + exception rows. Totals for each currency equal the validated totals. |

Two habits belong to every request:

- **Assumptions first.** Ask for the assumptions before the implementation, and answer them.
- **Small steps.** Ask for one change that you can review in two minutes, not for a solution.

## The template

```text
Goal:        <what the result is for, in one sentence>
Input:       <tables or DataFrames, what one row is, the keys, what is not guaranteed>
Rules:       <the business rules that apply, in the order in which they decide>
Result:      <columns, types, and grain of the output. Where do the other rows go?>
Constraints: <language and API, permitted libraries, what must not change>
Errors:      <NULL, unknown key, duplicate key, invalid value: what must happen>
Acceptance:  <the checks that I will run, with numbers where I have them>
Working:     Change only <scope>. Do not run anything.
             First list your assumptions and your questions, and wait for my answer.
```

## Nine patterns

Replace the text in angle brackets. Each pattern ends with what you do before you accept the answer.

### 1. Assumptions first

```text
Do not write code yet. List the assumptions that you would have to make about <the data or the rule>,
and the questions that you have for me. Mark each assumption as: stated in my request, visible in
the schema, or a guess.
```

Before you accept: answer every guess from the schema, the contract, or the data. A guess that you
cannot answer is a question for the owner of the data, not for the assistant.

### 2. One small step

```text
Change only <function, cell, or file>. Keep its signature. Do not touch <tests, fixtures, documents,
other files>. No new import and no new dependency. Do not run anything.
After the change, list what you changed and why.
```

Before you accept: read the diff. A file that you did not name must not be in it.

### 3. Explain, do not run

```text
Just explain this to me, do not run any code and do not change anything.
What does <expression or function> return for: NULL, a blank text, a negative amount, and a key that
matches two rows? Answer as a table: input, result, why.
```

Before you accept: pick one row of the table and prove it, with a test or with one query.

### 4. Move without changing the meaning

```text
Move the logic of <source> into <target>. The meaning must not change: the same rows, the same
values, the same types. Do not improve, rename, or simplify anything on the way.
List every place where you had to make a choice.
```

Before you accept: compare the old result and the new result in five ways: schemas, key sets, row
counts, signed amounts, and aggregates. A matching grand total proves nothing.

### 5. Test cases from the contract, not from the code

```text
Read <the contract> and <the existing tests>. Do not take any expected value from the implementation.
List the cases that no test covers yet. For each case: the rule, concrete input values, the expected
result, and how you derived it from the contract.
Mark every expected result that you calculated yourself with CHECK BY HAND.
```

Before you accept: calculate every expected value yourself. An expected value that comes from the
code under test preserves the defect that the test should find.

### 6. Tests with explicit expected values

```text
Write tests for these cases, which I verified by hand: <cases with expected values>.
Use literal expected values. Do not compute an expected value with the function under test.
Do not change the implementation. Do not run anything.
```

Before you accept: run the tests against the unchanged code. A new test that passes at once has
either found nothing or tests nothing. Find out which.

### 7. Trace a failure to a decision in the code

```text
The check <name> fails. Its output is: <paste the output, with the record keys>.
Do not edit any file. Name the one expression in <file> that produces this outcome. Show with the
values of <record key> why it does. Say which rows would change their outcome if it were corrected.
```

Before you accept: look at the record yourself. The explanation must fit the delivered values.

### 8. The smallest fix

```text
Make the smallest change that corrects the cause that you named. No refactoring and no renaming.
Do not change tests, checks, fixtures, or documents.
Then tell me which tests and which checks I should run, and what each of them should show.
```

Before you accept: a fix that edits a test, weakens a check, or filters out the rows that failed
hides the symptom. Decline it.

### 9. Translate and compare

```text
Translate only <expression> from <SQL> to <PySpark>. Do not change its meaning.
Tell me what your version returns for NULL, for a blank text, and for <an edge value>.
```

Before you accept: run both versions on the same rows and compare them row by row. Two versions
that read alike are not two versions that agree.
