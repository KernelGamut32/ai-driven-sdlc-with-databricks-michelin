# Data dictionary of the O2I training data

All data is fictional. The tables are in the schema `o2i` of the class catalog.

| Table | Rows | Dataset |
|---|---|---|
| `invoice_lines`, `customers`, `products`, `orders` | about 50,000 invoice lines | training |
| `fixture_invoice_lines`, `fixture_customers`, `fixture_products`, `fixture_orders` | 56 invoice lines in 48 cases | fixture |
| `fixture_expected_results`, `fixture_expected_amounts` | expected outcome and hand-calculated amounts | fixture |
| `challenge_invoice_lines`, `challenge_expected_results` | 191 invoice lines in 16 cases, with expected outcomes | challenge |
| `reference_totals` | validated totals of the accepted training lines, for each scope of rules and each currency | training |

A fixture table and a challenge table have the columns of the training table of the same name. The challenge batch uses the training tables `customers`, `products`, and `orders`.

## invoice_lines

Delivered sales invoice lines, as extracted from the source systems. Fictional training data.

**Grain.** One delivered row is identified by RawRowID. One invoice line is identified by InvoiceID + LineNumber. A line can be delivered more than once.

| Column | Type | Meaning |
|---|---|---|
| `RawRowID` | string | Technical. Identifies one delivered row. Unique. Assigned at ingestion in delivery order. |
| `InvoiceID` | string | Invoice or credit note number. Together with LineNumber it identifies one invoice line. |
| `LineNumber` | int | Line of the invoice, starting at 1. |
| `InvoiceDate` | string | Invoice date as delivered, as text. Expected format yyyy-MM-dd. Not validated at ingestion. |
| `DocumentType` | string | INVOICE or CREDIT_NOTE. Informational: the sign of Quantity carries the meaning. |
| `Status` | string | Document status as delivered, as text. Not cleaned at ingestion. Business values: POSTED, DRAFT, CANCELLED. |
| `CustomerID` | string | Customer key as delivered. Refers to customers.CustomerID. |
| `ProductID` | string | Product key as delivered. Refers to products.ProductID. |
| `OrderID` | string | Order that the line bills. NULL for an invoice without an order. Refers to orders.OrderID. |
| `OrderLineNumber` | int | Order line that the line bills. Refers to orders.OrderLineNumber. |
| `Quantity` | decimal(12,3) | Invoiced quantity. Negative on a credit line. Carries the sign of the line. |
| `UnitPrice` | decimal(18,4) | Agreed net price for one unit, in Currency. Never negative. |
| `NetAmount` | decimal(18,2) | Net amount of the line as delivered: Quantity x UnitPrice, rounded half up to two decimals. Negative on a credit line. |
| `TaxRate` | decimal(6,4) | Tax rate as a fraction, for example 0.2000 for 20 percent. NULL means that no tax applies to the line. |
| `Currency` | string | ISO currency code of UnitPrice and NetAmount. Amounts in different currencies are never added. |
| `SalesOrg` | string | Sales organization that issued the document. |
| `SourceSystem` | string | Source system of the delivery: ERP_EU or ERP_NA. |
| `LoadBatchID` | string | Technical. Delivery batch, LB- followed by the load date. |
| `IngestedAt` | timestamp | Technical. Time when the row was ingested. |

## customers

Customer master data. Fictional training data.

**Grain.** One row for each CustomerID is expected. The table has no enforced key.

| Column | Type | Meaning |
|---|---|---|
| `CustomerID` | string | Customer key. One row for each key is expected, but the table has no enforced key. |
| `CustomerName` | string | Legal name of the customer. Fictional. |
| `Segment` | string | Customer segment: DEALER, FLEET, DISTRIBUTOR, ECOMMERCE, or OEM. |
| `Country` | string | ISO country code of the customer. |
| `Region` | string | Sales region: EMEA or AMER. |
| `City` | string | City of the customer. |
| `PostalCode` | string | Postal code, as text. |
| `BillingCurrency` | string | Currency in which the customer is invoiced. |
| `PaymentTerms` | string | NET30, NET45, NET60, or PREPAID. |
| `CreditLimit` | decimal(18,2) | Credit limit in the billing currency. |
| `AccountManager` | string | Identifier of the account manager. |
| `ParentCustomerID` | string | CustomerID of the parent company, if any. |
| `IsActive` | boolean | False for a customer that no longer orders. |
| `CreatedDate` | date | Date when the customer was created. |
| `LastUpdated` | timestamp | Time of the last change of this master row. |

## products

Product master data. Fictional training data.

**Grain.** One row for each ProductID is expected. The table has no enforced key.

| Column | Type | Meaning |
|---|---|---|
| `ProductID` | string | Product key. One row for each key is expected, but the table has no enforced key. |
| `ProductName` | string | Product description. Fictional. |
| `ProductLine` | string | PASSENGER, LIGHT_TRUCK, TRUCK_BUS, AGRICULTURAL, TWO_WHEEL, ACCESSORIES, or SERVICES. |
| `ProductFamily` | string | Family inside the product line. |
| `SizeDesignation` | string | Size designation of a tyre. NULL for accessories and services. |
| `RimDiameterInch` | decimal(4,1) | Rim diameter in inches. NULL for accessories and services. |
| `UnitOfMeasure` | string | EA (each), SET, or HR (hour). |
| `ListPrice` | decimal(18,4) | List price for one unit, in ListPriceCurrency. |
| `ListPriceCurrency` | string | Currency of ListPrice. Always EUR. |
| `TaxClass` | string | STANDARD, REDUCED, or EXEMPT. |
| `Status` | string | ACTIVE, PHASE_OUT, or BLOCKED. |
| `WeightKg` | decimal(8,3) | Weight of one unit in kilograms. NULL for accessories and services. |
| `LaunchDate` | date | Date of the market launch. |
| `LastUpdated` | timestamp | Time of the last change of this master row. |

## orders

Customer order lines. Fictional training data.

**Grain.** One row for each OrderID + OrderLineNumber is expected. The table has no enforced key.

| Column | Type | Meaning |
|---|---|---|
| `OrderID` | string | Order number. Together with OrderLineNumber it identifies one order line. |
| `OrderLineNumber` | int | Line of the order, starting at 1. |
| `OrderDate` | date | Date of the order. |
| `CustomerID` | string | Customer who ordered. |
| `ProductID` | string | Product that was ordered. |
| `OrderedQuantity` | decimal(12,3) | Ordered quantity. Always positive. |
| `AgreedUnitPrice` | decimal(18,4) | Agreed net price for one unit, in Currency. |
| `Currency` | string | ISO currency code of AgreedUnitPrice. |
| `OrderStatus` | string | OPEN, CONFIRMED, SHIPPED, INVOICED, or CANCELLED. |
| `SalesChannel` | string | EDI, PORTAL, INSIDE_SALES, or FIELD_SALES. |
| `SalesOrg` | string | Sales organization that took the order. |
| `RequestedDeliveryDate` | date | Delivery date that the customer requested. |
| `LastUpdated` | timestamp | Time of the last change of this order line. |

## fixture_expected_results and challenge_expected_results

Expected outcome of every delivered row, for each version of the business contract. Written from the contract and validated by the instructor.

**Grain.** One row for each RawRowID and ContractVersion.

| Column | Type | Meaning |
|---|---|---|
| `RawRowID` | string | The delivered row. |
| `ContractVersion` | string | Version of the business contract: 1.0 or 1.1. |
| `CaseID` | string | Named case of the fixture (F01 to F48) or of the challenge batch (C01 to C16). |
| `ExpectedDisposition` | string | ACCEPTED, QUARANTINED, or EXCLUDED. |
| `ExpectedReason` | string | Expected reason code. NULL for an accepted row. |

## fixture_expected_amounts

Hand-calculated TaxAmount and GrossAmount of the fixture rows that contract 1.0 accepts.

**Grain.** One row for each RawRowID.

| Column | Type | Meaning |
|---|---|---|
| `RawRowID` | string | The delivered row. |
| `CaseID` | string | Named case of the fixture. |
| `NetAmount` | decimal(18,2) | Net amount as delivered. |
| `TaxRate` | decimal(6,4) | Tax rate as delivered. NULL means that no tax applies. |
| `ExpectedTaxAmount` | decimal(18,2) | NetAmount x TaxRate, rounded half up to two decimals, calculated by hand. 0.00 without a tax rate. |
| `ExpectedGrossAmount` | decimal(18,2) | NetAmount + ExpectedTaxAmount. |

## reference_totals

Validated totals of the accepted training invoice lines, for each scope of rules and each currency. Part of the instructor-validated answer set: calculated independently of the course code. Use it to judge a result. Never use it to produce one.

**Grain.** One row for each Scope and Currency.

| Column | Type | Meaning |
|---|---|---|
| `Scope` | string | Rules that were applied: LAB1 (rules R2, R5, R6 only), CONTRACT_1.0 (rules R1 to R7), or CONTRACT_1.1 (rules R1 to R8). |
| `Currency` | string | ISO currency code. Totals are never added across currencies. |
| `AcceptedRows` | int | Number of accepted invoice lines of the training data in this scope and currency. |
| `NetAmount` | decimal(18,2) | Sum of NetAmount of the accepted lines. Credits are negative and reduce the total. |
| `TaxAmount` | decimal(18,2) | Sum of TaxAmount of the accepted lines: NetAmount x TaxRate, rounded half up for each line, 0.00 without a tax rate. |
| `GrossAmount` | decimal(18,2) | Sum of GrossAmount of the accepted lines: NetAmount + TaxAmount for each line. |
