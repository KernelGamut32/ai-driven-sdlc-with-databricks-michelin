# Lab 3, step 1: prepared test case proposals

Use this file when GitHub Copilot is not available, or to compare with the answer that you got.
It is a response to request 3.1, written for this workshop. It proposes eight test cases.
Some of its expected results are wrong.

**Your task:** decide for each case: accept, reject, or already covered. Calculate every expected
result that is marked CHECK BY HAND yourself, with the contract and the fixture workbook. Do not
ask the code.

## The response

> I read the business contract and the two test files. These cases are not covered by a code test.

| # | Rule | Input | Expected result | How I derived it |
|---|---|---|---|---|
| 1 | Section 5, tax | NetAmount 3.00, TaxRate 0.0550 | TaxAmount 0.16, GrossAmount 3.16 | 3.00 x 0.055 = 0.165. A tie rounds to the even digit: 0.16. CHECK BY HAND |
| 2 | Section 5, tax of a credit | NetAmount -3.00, TaxRate 0.0550 | TaxAmount -0.16, GrossAmount -3.16 | -0.165 rounds half up, toward the larger value: -0.16. CHECK BY HAND |
| 3 | Section 5, tax | NetAmount 0.50, TaxRate 0.2100 | TaxAmount 0.11 | 0.50 x 0.21 = 0.105, half up gives 0.11. CHECK BY HAND |
| 4 | R7 amount | Quantity 2.5, UnitPrice 12.2500, NetAmount 30.62 | The line passes | 2.5 x 12.25 = 30.625. The delivered 30.62 is within one cent, which is a rounding difference. CHECK BY HAND |
| 5 | R3 line identity | One key delivered twice, Quantity 4 and Quantity 6 | The later delivery is ACCEPTED, the earlier one is EXCLUDED with EXACT_REPLAY | The later delivery corrects the earlier one |
| 6 | R1 before R2 | Status DRAFT, ProductID NULL | QUARANTINED, MISSING_REQUIRED_FIELD | The first rule that fails decides |
| 7 | R4 invoice date | InvoiceDate '2026-02-29' | QUARANTINED, INVALID_DATE | 2026 is not a leap year |
| 8 | R5 customer | CustomerID 'c200001 ', master key 'C200001' | QUARANTINED, UNKNOWN_CUSTOMER | A key in another case, or with a space, is a different key |

## Your review

- Which cases would turn a defect into an expected value if you accepted them?
- Which case repeats a test that already exists?
- For case 1, the fixture workbook has a hand calculation. Which case of the fixture is it?
