# Order-to-invoice accepted dataset: business contract

Version 1.0. This is the rule sheet of the workshop case. All companies, customers, products, and
amounts are fictional.

## 1. Purpose

A sales analytics squad needs two things from the delivered invoice lines:

1. One trustworthy dataset of accepted invoice lines, enriched with customer and product attributes.
2. One exception report with every delivered line that is not accepted, and the reason.

A total that nobody can trace back to delivered rows is not acceptable, even when the code ran.

## 2. Inputs

| Table | One row is | Key | Note |
|---|---|---|---|
| `invoice_lines` | One delivered row of one invoice line | `RawRowID` identifies the delivered row. `InvoiceID` + `LineNumber` identifies the invoice line. | A line can be delivered more than once. |
| `customers` | One customer | `CustomerID` | One row for each key is expected. Nothing enforces it. |
| `products` | One product | `ProductID` | One row for each key is expected. Nothing enforces it. |
| `orders` | One order line | `OrderID` + `OrderLineNumber` | Not used by this version of the contract. |

The data dictionary (`docs/data_dictionary.md`) describes every column.

## 3. One outcome for every delivered row

Every delivered row of `invoice_lines` ends in exactly one of three dispositions.

| Disposition | Meaning | Where the row goes |
|---|---|---|
| `ACCEPTED` | The line passed every rule. | Accepted output |
| `QUARANTINED` | The line cannot be trusted. A person must decide. | Exception output, with a reason code |
| `EXCLUDED` | The line is correctly left out, and the reason is documented. | Exception output, with a reason code |

Accountability: for every run, delivered rows = accepted rows + exception rows, counted by `RawRowID`.
No row is dropped without a reason, and no row is counted twice.

Delivered data is evidence. It is never updated, overwritten, or corrected. A proposed correction
needs the approval of a person who owns the data.

## 4. Rules

The rules are checked in this order. The first rule that fails decides the outcome, so every row has
exactly one reason code.

| Rule | A line passes when | Otherwise |
|---|---|---|
| R1 Required fields | `InvoiceID`, `LineNumber`, `InvoiceDate`, `Status`, `CustomerID`, `ProductID`, `Quantity`, `UnitPrice`, `NetAmount`, and `Currency` are present. A text field that is empty or only spaces is missing. | `QUARANTINED`, `MISSING_REQUIRED_FIELD` |
| R2 Status | The status is `POSTED`. The comparison ignores upper and lower case and surrounding spaces. | `DRAFT` or `CANCELLED`: `EXCLUDED`, `NOT_POSTED`. Any other value: `QUARANTINED`, `UNEXPECTED_STATUS` |
| R3 Line identity | The line was delivered once. If it was delivered several times with identical business content, the delivery with the lowest `RawRowID` passes. | The other identical deliveries: `EXCLUDED`, `EXACT_REPLAY`. Deliveries with different content: all of them `QUARANTINED`, `CONFLICTING_DUPLICATE` |
| R4 Invoice date | `InvoiceDate` is written exactly as `yyyy-MM-dd` and is a real calendar date. | `QUARANTINED`, `INVALID_DATE` |
| R5 Customer | `CustomerID` matches exactly one row of `customers`. | No row: `QUARANTINED`, `UNKNOWN_CUSTOMER`. More than one row: `QUARANTINED`, `AMBIGUOUS_CUSTOMER` |
| R6 Product | `ProductID` matches exactly one row of `products`. | No row: `QUARANTINED`, `UNKNOWN_PRODUCT`. More than one row: `QUARANTINED`, `AMBIGUOUS_PRODUCT` |
| R7 Amount | `NetAmount` equals `Quantity` x `UnitPrice`, rounded half up to two decimals. | `QUARANTINED`, `AMOUNT_MISMATCH` |

Details that decide edge cases:

- **R2.** Only the comparison is normalized. The delivered `Status` value stays as it is in every output.
- **R3.** Rule R3 looks only at rows that passed R1 and R2. Business content means every column except
  the technical columns `RawRowID`, `LoadBatchID`, and `IngestedAt`. Choosing one of several different
  deliveries would be a business decision, and this contract does not make it.
- **R5 and R6.** A key matches only when it is exactly equal to the master key. A key in another
  case, or with a space, is a different key. Choosing the most recent of several master rows would be a
  business decision, and this contract does not make it.
- **R7.** A valid credit has a negative `Quantity` and a negative `NetAmount`. It passes like any other line.

## 5. Amounts

- `Quantity` carries the sign. An invoice line has a positive quantity. A credit line has a negative
  quantity. `UnitPrice` is never negative. `NetAmount` has the sign of the quantity.
- Money is decimal, never floating point. Amounts are compared exactly, without a tolerance.
- Rounding is half up to two decimals: 0.165 becomes 0.17, and -0.165 becomes -0.17.
- The accepted output adds two amounts to each line:
  - `TaxAmount` = `NetAmount` x `TaxRate`, rounded half up. When `TaxRate` is NULL, no tax applies and `TaxAmount` is 0.00.
  - `GrossAmount` = `NetAmount` + `TaxAmount`.
- A `TaxRate` of 0.0000 is a rate. NULL is not zero by accident: it means that no tax applies.
- Amounts in different currencies are never added together. This contract has no conversion rule and
  no approved exchange rates.

## 6. Outputs

**Accepted output**, one row for each accepted invoice line. `InvoiceID` + `LineNumber` is unique.

`RawRowID`, `InvoiceID`, `LineNumber`, `InvoiceDate` (date), `DocumentType`, `CustomerID`, `CustomerName`,
`Segment`, `Country`, `Region`, `ProductID`, `ProductName`, `ProductLine`, `OrderID`, `OrderLineNumber`,
`Quantity` decimal(12,3), `UnitPrice` decimal(18,4), `NetAmount` decimal(18,2), `TaxRate` decimal(6,4),
`TaxAmount` decimal(18,2), `GrossAmount` decimal(18,2), `Currency`, `LoadBatchID`

**Exception output**, one row for each delivered row that is not accepted, with the values as delivered.

`RawRowID`, `InvoiceID`, `LineNumber`, `Disposition`, `ReasonCode`, `Status`, `InvoiceDate` (text as
delivered), `DocumentType`, `CustomerID`, `ProductID`, `OrderID`, `OrderLineNumber`, `Quantity`,
`UnitPrice`, `NetAmount`, `TaxRate`, `Currency`, `LoadBatchID`

## 7. What this contract does not allow

- Filling an unknown customer or product with a placeholder and accepting the line.
- Keeping an arbitrary row of several conflicting rows.
- Changing a delivered key, status, date, or amount to make a line pass.
- Dropping negative amounts, or turning them into positive amounts.
- Comparing amounts with a tolerance.
- Adding amounts of different currencies.
- Changing an expected result, or this contract, because the code produces something else. A change
  to the contract is a change request, decided by the people who own the rule.

## Change history

| Version | Change |
|---|---|
| 1.0 | Rules R1 to R7. |
