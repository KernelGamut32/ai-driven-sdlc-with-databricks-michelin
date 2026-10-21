# Running the course in your own Azure Databricks workspace

## Data load and environment preparation for self-directed learners

AI-Driven SDLC with Databricks | Participant supplement | Kit 2.0 | October 21, 2026

---

## Who this is for

You want to work through Exercise 1 and Labs 1 to 4 in an Azure Databricks workspace that you control, instead of the instructor-provided environment. In class, the platform team loads the tables and the instructor provisions your output schema. Here, you do both. Everything else is the same: the same notebooks, the same project, the same expected outputs.

Plan 60 to 90 minutes, not counting the creation of a workspace. You pay for the compute, the storage, and any billed Genie usage in your own subscription.

**What this guide states about Michelin:** nothing. If the workspace you use belongs to Michelin, the Michelin platform team decides what you may create there and which AI features are enabled. If it is a personal subscription, do not bring Michelin code or Michelin data into it. The course needs neither: all 13 tables are fictional.

---

## What you will have at the end

| Item | Evidence |
|---|---|
| 13 training tables in `<catalog>.o2i` | `ALL TABLES VERIFIED` from the setup notebook, and matching row counts from your own check |
| An output schema of your own | `READY` from `02_learner_smoke_test` |
| The participant project configured for your workspace | `4 passed, 8 failed` and `READY` from `python tools/setup_check.py` |
| A working run route from VS Code | The last line of `demo/parity_trap.py`, printed from Databricks |
| Genie Code and GitHub Copilot configured for review-first work | Actions set to Ask first; Copilot names `o2i/rules.py` when asked |

---

## What you need from the instructor

A participant never needs the data files in class. You need them, because you load the tables yourself. Ask for these items from the kit:

| Item | Where it lives in the kit | Why you need it |
|---|---|---|
| The whole `2_Participant` folder | `2_Participant` | Workbook, discussion cards, fixture workbook, four notebooks, the project `o2i-workshop`, prepared AI outputs |
| The 13 CSV files | `4_Data/csv` | The load. CSV is the route that needs no optional reader on your runtime. |
| The 13 Excel workbooks (optional) | `4_Data/excel` | Same content as the CSV files. Useful for reading the `about` sheet of each table. Not needed for the load. |
| `00_setup_training_data` (`.py`, plus its `.ipynb` twin) | `1_Instructor/setup_notebooks` | Loads and verifies the tables, including fingerprints |
| `01_provision_learner_schemas` (`.py`, plus its `.ipynb` twin) | `1_Instructor/setup_notebooks` | Creates your output schema with the exact name the labs derive |
| `prepare_cohort.py` (optional) | `1_Instructor/tools` | Writes your workspace URL and catalog into the project and every notebook. The instructor can run it for you instead (Step 7, Option A). |
| `docs/data_dictionary.md` | Inside `o2i-workshop/docs` | Column descriptions. Already in the project. |
| `3_Solutions` | `3_Solutions` | Only after you have finished Lab 4. The instructor decides whether to hand it out. |

---

## What you need in Azure

| Requirement | How to check |
|---|---|
| An Azure Databricks workspace attached to a Unity Catalog metastore | Open Catalog Explorer. If you see a catalog list with a `main` or a workspace catalog, Unity Catalog is on. |
| Rights to create a catalog, or to use an existing one, and to create a schema, a volume, and tables in it | Try Step 3. If `CREATE CATALOG` is refused, use the workspace's default catalog and ask its owner for `USE CATALOG`, `CREATE SCHEMA`, and `CREATE VOLUME`. |
| Rights to create compute, or an existing all-purpose cluster you can attach to | Compute page: the Create button is present, or a cluster is listed that you can start |
| Genie Code available in your workspace region | Open any notebook and look for the Genie Code pane. Microsoft Learn has the geo availability list. |
| Partner-powered AI features enabled, if you want the Genie Code agent | Step 8 |
| A sign-in name with an `@` in it | The output schema name is derived from the part before the `@` |

A workspace with VNet injection and no internet egress is fine. Nothing in the course downloads anything.

---

## What you need on your workstation

| Requirement | Notes |
|---|---|
| Visual Studio Code, current release | Help > About shows the version |
| The Databricks extension for Visual Studio Code | Extensions view, search "Databricks" |
| GitHub Copilot and GitHub Copilot Chat extensions, signed in with a license that includes chat | Any Copilot plan with chat and the agent works. A Business or Enterprise seat is governed by your organization's policies. |
| Python 3.9 or later on the `PATH` | `python --version`. The four project tools need Python and nothing else; they install no package. |
| Network access from VS Code to your workspace URL | Open the URL in a browser from the same machine |

---

## Your five values

Fill this in as you go. Every lab in the workbook refers to it.

| Value | Yours | Set in |
|---|---|---|
| Workspace URL | | Step 1 |
| Catalog | | Step 3 |
| Compute for notebooks and runs | | Step 2 |
| Run route from VS Code: A, B, C, or D | | Step 10 |
| Session Target in the Copilot chat: Local or Copilot | | Step 11 |

The output schema is not in the list. The notebooks and the project derive it from your sign-in name: `o2i_` followed by the part before the `@`, in lower case. Nobody types it.

---

## The steps at a glance

| Step | What you do | Done when |
|---|---|---|
| 1 | Confirm the workspace and record its URL | Workspace URL written down |
| 2 | Create or choose compute | A cluster on Databricks Runtime 17.3 LTS (or any LTS on Spark 3.5 or later) is running |
| 3 | Create or choose the catalog, and create the schema `o2i` and a staging volume | `SHOW SCHEMAS IN <catalog>` lists `o2i` |
| 4 | Upload the 13 CSV files to the volume | 13 files listed in the volume |
| 5 | Import and run `00_setup_training_data` | `ALL TABLES VERIFIED` |
| 6 | Create your output schema | `PROVISIONED`, or the schema exists with the derived name |
| 7 | Write your values into the participant package | `lab_config.py`, `databricks.yml`, and the notebooks carry your catalog and workspace URL |
| 8 | Configure Genie Code | Actions is set to Ask first |
| 9 | Import the participant notebooks and run the smoke test | `READY` |
| 10 | Connect VS Code and choose a run route | `4 passed, 8 failed`, `READY`, and the last line of `parity_trap.py` from Databricks |
| 11 | Configure GitHub Copilot | Copilot's answer names `o2i/rules.py` |
| 12 | Run the acceptance checklist | All lines checked |

---

## Step 1. Confirm the workspace and record its URL

1. Sign in to the Azure portal, open your Azure Databricks resource, and select **Launch Workspace**.
2. Copy the workspace URL from the browser address bar. It has the form `https://adb-<digits>.<n>.azuredatabricks.net`. Record it without a trailing slash and without any path after the host.
3. In the workspace, open **Catalog** in the left navigation. You should see at least one catalog. If the page offers only the legacy `hive_metastore`, the workspace is not attached to a Unity Catalog metastore. Attach it, or use a different workspace, before you continue. Microsoft Learn describes how under "Set up and manage Unity Catalog".

If you do not have a workspace yet, the Microsoft Learn quickstart "Create an Azure Databricks workspace" takes about 10 minutes. Choose the Premium tier.

---

## Step 2. Create or choose compute

The kit's code and data were executed on Apache Spark 4.0 outside Azure Databricks, and the table fingerprints were confirmed on Spark 3.5, 4.0, and 4.1. Databricks Runtime 17.3 LTS is built on Spark 4.0.0, released October 22, 2025, and is the runtime the instructor's Setup Guide recommends.

Recommended for a single learner:

| Setting | Value | Why |
|---|---|---|
| Type | All-purpose compute, single node | 107,770 rows need no cluster. Single node is the cheapest option that runs everything in the kit. |
| Databricks Runtime | 17.3 LTS (Standard, not ML) | Spark 4.0, the verified line |
| Access mode | Standard (formerly Shared), or Dedicated to you | Both work with Unity Catalog |
| Node type | The smallest general-purpose VM offered | Nothing in the labs is compute-bound |
| Terminate after | 30 minutes of inactivity | Cost control. You can always restart. |

Record the compute name as your value "Compute for notebooks and runs".

**About serverless compute.** Serverless works for notebooks and is often the quickest to start. Two cautions: the kit's code was not executed on serverless, and the Databricks extension's **Upload and Run File** command is not available with serverless compute, so from VS Code you would use **Run File as Workflow** or run route D instead. If you want the fewest surprises, use the single-node cluster above.

---

## Step 3. Create or choose the catalog, the schema, and a staging volume

Open a new notebook attached to your compute, or the SQL editor, and run these statements. Replace `<catalog>` with a short name of your choice, for example `o2i_training`.

```sql
CREATE CATALOG IF NOT EXISTS <catalog>;
USE CATALOG <catalog>;

CREATE SCHEMA IF NOT EXISTS o2i
  COMMENT 'AI-Driven SDLC with Databricks: training tables (fictional data)';

CREATE VOLUME IF NOT EXISTS o2i.staging
  COMMENT 'Source files for the one-time load';

SHOW SCHEMAS IN <catalog>;
```

If `CREATE CATALOG` is refused, you do not have `CREATE CATALOG` on the metastore. Use the workspace's default catalog instead, and run only the schema and volume statements inside it. Any valid catalog name works with the kit.

Record the catalog name as your value "Catalog". The training tables will live in `<catalog>.o2i`.

> **Verify on screen.** The instructor's setup notebook may create the schema `o2i` itself. Creating it here first is harmless and removes one dependency.

---

## Step 4. Upload the 13 CSV files to the volume

1. In Catalog Explorer, open `<catalog>` > `o2i` > **Volumes** > `staging`.
2. Select **Upload to this volume**, and create a folder named `csv` when the dialog offers a path. If it does not, upload to the volume root and use that path in Step 5.
3. Select all 13 CSV files from `4_Data/csv` and upload them. The whole set is about 22 MB across both formats, so the CSV files alone are well under that.
4. When the upload finishes, confirm that 13 files are listed and that the names match this table exactly. The setup notebook looks for them by name.

| File | Rows | Role |
|---|---|---|
| `invoice_lines.csv` | 49,700 | The delivered invoice lines. Input of every lab. |
| `customers.csv` | 1,180 | Customer master. Rule R5. |
| `products.csv` | 601 | Product master. Rule R6. |
| `orders.csv` | 55,448 | Customer order lines. Rule R8, Lab 4. |
| `fixture_invoice_lines.csv` | 56 | The approved fixture: 56 hand-verifiable rows in 48 cases |
| `fixture_customers.csv` | 11 | Customer master of the fixture |
| `fixture_products.csv` | 9 | Product master of the fixture |
| `fixture_orders.csv` | 42 | Order lines of the fixture |
| `fixture_expected_results.csv` | 112 | Expected outcome of every fixture row, contract 1.0 and 1.1 |
| `fixture_expected_amounts.csv` | 22 | Hand-calculated tax and gross amounts of the accepted fixture rows |
| `challenge_invoice_lines.csv` | 191 | The unseen batch of Lab 4 |
| `challenge_expected_results.csv` | 382 | Expected outcome of every challenge row, contract 1.0 and 1.1 |
| `reference_totals.csv` | 16 | Validated totals per rule scope and currency. Judges a result, never produces one. |

Total: 13 files, 107,770 rows.

**Do not open a CSV file in Excel and save it before uploading.** Excel rewrites dates and numbers on save, and the fingerprint check in Step 5 will fail. Upload the files as delivered.

The volume path you will give the setup notebook is:

```text
/Volumes/<catalog>/o2i/staging/csv/
```

---

## Step 5. Import and run the setup notebook

### 5.1 Import

1. In the workspace, open **Workspace** > your user folder. Create a folder `o2i_setup`.
2. Right-click the folder, select **Import**, choose **File**, and select `00_setup_training_data.py`.
3. Open the imported notebook. The text cells should render as formatted text. If they appear as comment lines starting with `# MAGIC`, the workspace did not recognize the source format: delete the import and import the `.ipynb` twin from the `ipynb` subfolder instead.
4. Attach the notebook to your compute.

### 5.2 Set the widgets and run

The notebook's widgets appear across its top. Their exact names are in the first cell of the notebook; by purpose they are:

| Widget purpose | Your value |
|---|---|
| Catalog | `<catalog>` |
| Location of the source files | `/Volumes/<catalog>/o2i/staging/csv/` |
| File format | `csv` |
| Mode | the load mode, not `verify only` |

Select **Run all**. The notebook creates each table in `<catalog>.o2i`, counts its rows, computes a fingerprint, and compares both with the values recorded when the kit was built.

**Done when** the last cell prints `ALL TABLES VERIFIED`.

### 5.3 Confirm with your own check

The notebook's fingerprint is the real test. This independent count is the one you can read without the notebook, and it is the same shape as the checks the labs teach:

```python
catalog = "<catalog>"

expected = {
    "invoice_lines": 49700,
    "customers": 1180,
    "products": 601,
    "orders": 55448,
    "fixture_invoice_lines": 56,
    "fixture_customers": 11,
    "fixture_products": 9,
    "fixture_orders": 42,
    "fixture_expected_results": 112,
    "fixture_expected_amounts": 22,
    "challenge_invoice_lines": 191,
    "challenge_expected_results": 382,
    "reference_totals": 16,
}

all_ok = True
for table, n in expected.items():
    count = spark.table(f"{catalog}.o2i.{table}").count()
    status = "OK  " if count == n else "DIFF"
    all_ok = all_ok and count == n
    print(f"{status} {table:28} {count:>7}  expected {n:>7}")

print("ROW COUNTS OK" if all_ok else "ROW COUNTS DIFFER: reload the tables that say DIFF")
```

A matching row count is not proof of correctness. The course says so about every result, and the same applies here. It is the first thing to look at when something is wrong, and the notebook's fingerprint is the evidence.

> **Assumption, labeled.** This check assumes the table names equal the file names without extension, which is how the Kit Guide lists them. If the setup notebook names a table differently, use the names it prints.

### 5.4 If the setup notebook does not print ALL TABLES VERIFIED

| Symptom | Likely cause | What to do |
|---|---|---|
| A file is not found | Path or file name differs | Compare the widget value with the path in Catalog Explorer. Paths are case-sensitive. |
| A row count is off by one or a few | A file was opened and saved, or the upload was interrupted | Re-upload that file from `4_Data/csv` and run again |
| A fingerprint differs but the row count matches | A value was rewritten, typically a date or a decimal | Same as above. The instructor's Excel files are the second copy of the same content if a CSV is damaged. |
| An error mentions an Excel reader | You chose the Excel route and the runtime has no reader for it | Use the CSV route. It needs nothing beyond the runtime. |
| `o2i` schema not found | The notebook expects the schema to exist | Run Step 3 again |
| Permission denied on `CREATE TABLE` | Missing privilege on the schema | Grant yourself `CREATE TABLE` and `USE SCHEMA` on `<catalog>.o2i`, or ask the catalog owner |

After a successful load, run the notebook once more with the mode set to `verify only`. It should print `ALL TABLES VERIFIED` again, without writing anything. That is the same recheck the instructor runs between cohorts.

---

## Step 6. Create your output schema

Every lab writes to a schema of your own, never to `o2i`. The notebooks and the project derive its name from your sign-in: `o2i_` followed by the part of your sign-in name before the `@`, in lower case. The instructor's Setup Guide, Part 5.1, has the exact rule for characters that are not valid in a schema name.

### Option A. The provisioning notebook (preferred)

1. Import `01_provision_learner_schemas.py` into `o2i_setup`, the same way as in Step 5.1.
2. Set its catalog widget to `<catalog>`. If the notebook offers a mode for a single user or for the current user, choose it. If it provisions from a group, it will ask for a group name; see Option B instead.
3. Run all.

**Done when** the notebook prints `PROVISIONED`.

### Option B. By hand

Derive the name first, so that it matches what the labs expect:

```python
user = spark.sql("SELECT current_user()").first()[0]
schema = "o2i_" + user.split("@")[0].lower()
print(schema)
```

Then create it:

```sql
CREATE SCHEMA IF NOT EXISTS <catalog>.<the printed name>
  COMMENT 'AI-Driven SDLC with Databricks: my lab outputs';
```

The smoke test in Step 9 derives the same name. If the smoke test cannot find the schema, your sign-in name contains a character that the kit's rule replaces, and the printed name above is not the one the labs use. The output of the smoke test tells you which name it looked for; create that one.

---

## Step 7. Write your values into the participant package

The project `o2i-workshop` and every participant notebook carry the workspace URL and the catalog of the class. They must carry yours.

### Option A. Ask the instructor to run `prepare_cohort.py` for you (preferred)

Send the instructor your workspace URL and your catalog name. `prepare_cohort.py` writes both into the project, into every notebook, and rebuilds the project archive. It was verified on a copy of the kit. You receive a rebuilt `2_Participant` folder and skip Option B.

### Option B. Edit by hand

1. Unpack `o2i-workshop.zip` to a folder with a short path and no spaces, for example `C:\dev\o2i-workshop` or `~/dev/o2i-workshop`.
2. Open `lab_config.py` and set the catalog to `<catalog>`. Leave the datasets as delivered.
3. Open `databricks.yml` and set the workspace host to your workspace URL.
4. In each participant notebook you will import in Step 9, replace the class catalog with yours. The `.py` files are plain text, so search for the catalog value the instructor's copy carries and replace it. Ask the instructor for that value if it is not obvious from the first cell.
5. Do not change anything else in the project. The checkpoints under `checkpoints/` restore code, not configuration, so your values survive a checkpoint reload.

**Done when** `python tools/setup_check.py` (Step 10) reports your catalog and workspace, and the smoke test (Step 9) prints `READY`.

---

## Step 8. Configure Genie Code

Genie Code plans, runs code, reads cell output, and retries after an error. The course runs it with every action approved by you. The setting belongs to each user, so you set it even if you are the workspace admin.

1. Open any notebook and open the Genie Code pane.
2. Select **More** > **Settings** > **Actions**, and choose **Ask first**. Do not rely on the default; one documentation page calls Auto-approve the default and another calls "Ask every time" the default. The documentation itself says that auto-approve is a productivity feature and not a security boundary.
3. Confirm that the agent is available: start a conversation and ask it to list the tables in `<catalog>.o2i`. It should propose an action and wait for your approval before running anything.

### If the agent is not available

Genie Code's agentic capabilities require partner-powered AI features to be enabled for both the account and the workspace. Without the setting, Genie Code is still available, with a Databricks-hosted model, but without the agent.

| Where | Setting | Who can change it |
|---|---|---|
| Account console | **Enable partner-powered AI features** | Account admin |
| Workspace admin settings | **Partner-powered AI features** toggle | Workspace admin |

Two further points from the documentation, as of October 2026:

- If the setting cannot be enabled, the account may enforce data processing within the workspace geography for AI features. That enforcement has to be relaxed first.
- Azure Databricks announced the removal of the workspace-level setting from all workspaces on November 1, 2026, with each workspace keeping its value at that time. After that date, if your workspace has no agent, the value it kept was Off, and the account-level setting is where to look. A workspace with the compliance security profile has the setting off by default.

If you cannot enable the agent, every lab still works: Lab 1 uses the prepared response in `prepared_ai_outputs`, and you review it instead of generating it. The review is the skill.

---

## Step 9. Import the participant notebooks and run the smoke test

1. Create a folder `o2i_labs` in your user folder.
2. Import these four notebooks from `2_Participant/notebooks`, `.py` first, `.ipynb` twin as the fallback:
   - `02_learner_smoke_test`
   - `Lab1_Build_the_first_reviewed_transformation`
   - `09_reset_my_schema`
   - `Run_project_in_workspace`
3. Open `02_learner_smoke_test`, attach your compute, confirm the catalog widget shows `<catalog>`, and run all.

**Done when** the last line reads `READY`.

The smoke test reads from `<catalog>.o2i`, derives your output schema name, and writes a test table there. If it stops, its message names the missing piece: the catalog, a table, or the schema. Steps 5 and 6 are where to look.

---

## Step 10. Connect VS Code and choose a run route

### 10.1 Open the project and run the setup check

1. Open the folder `o2i-workshop` in VS Code (File > Open Folder).
2. In a terminal inside VS Code, run:

```text
python tools/setup_check.py
```

The check runs the code tests and reports the project's configuration. **Done when** it prints the line `Code tests ran`, then `4 passed, 8 failed`, and `READY` as the last line. Eight failing tests are the correct starting state of Lab 2. They are the work of that lab.

If Python is not found, the four project tools cannot run on this workstation. Run route D, in the mixed form the workbook describes, moves the tests to a notebook. The labs still work.

### 10.2 Sign in with the Databricks extension

1. Open the Databricks view in the activity bar.
2. Select **Configure** or **Sign in**, enter your workspace URL, and choose OAuth (user to machine). A browser window completes the sign-in. A personal access token also works if your workspace allows them.
3. Select your compute in the **Cluster** row and start it if it is stopped.
4. Confirm the **Remote Folder** row shows a workspace path. The extension synchronizes the project one way, from your workstation to that folder, and `databricks.yml` is where it reads the target.

### 10.3 Choose the run route

The Participant Workbook, "Before you start", Part B, describes the run routes by letter. Pick the letter that matches the command that works on your compute:

| Your compute | Command in VS Code | Where the output appears |
|---|---|---|
| A cluster | File editor title bar > **Run on Databricks** > **Upload and Run File** | The Debug Console or the Output panel in VS Code |
| Serverless | **Run on Databricks** > **Run File as Workflow** | A job run; VS Code opens a link to it |
| Neither command available, or the extension cannot reach the workspace | Run route D: `Run_project_in_workspace` in the browser | The notebook's cell output |

Test the route with the file that reads no table:

1. Open `demo/parity_trap.py`.
2. Run it on Databricks with the command of your route.
3. Record the last line it prints. The acceptance checklist asks for it.

If the file runs but prints nothing, the route did not execute it. That is a known pattern with Upload and Run File in some network configurations: the Databricks output channel in VS Code shows the reason. Try Run File as Workflow, then run route D.

Record your route letter as the value "Run route from VS Code".

### 10.4 Note on Databricks Connect

The project does not require Databricks Connect, and the course does not install it. If the extension offers to install `uv` and a local environment, you may decline: the labs run the Spark code on Databricks through the route above, and the plain-Python tests run locally with nothing but Python.

---

## Step 11. Configure GitHub Copilot

1. Sign in to GitHub from VS Code (Accounts icon). Confirm that the Copilot icon in the status bar shows no warning.
2. Open the Copilot chat. The chat input has four controls; one of them is the session target. Note whether your installation offers **Local**, **Copilot**, or both, and record the one you will use as the value "Session Target".
3. Ask, in the chat, with the project folder open:

   > Which file in this project holds the business rules, and which function decides the disposition of an invoice line?

   **Done when** the answer names `o2i/rules.py` and `decide_disposition`. The project's `AGENTS.md` tells the assistant the layout and nine hard rules; an answer that ignores the file means the instructions were not read, and the labs will go differently. Check that `AGENTS.md` is at the project root.

4. Leave the chat's permission controls at their default level. In the labs you approve edits and commands one at a time. If an agent ever edits or runs without asking, set the Permissions control back to its default and run **Chat: Reset Tool Confirmations** from the Command Palette.

If you have no Copilot license, Labs 2 to 4 still work: `python tools/checkpoint.py prepared <lab>` loads the prepared assistant output for the lab, and you review it instead of generating it.

---

## Step 12. Acceptance checklist

Record these lines before you start Exercise 1. They are the same four lines the instructor asks of every participant, plus the two that the self-service load adds.

| # | Check | Your evidence |
|---|---|---|
| 1 | `00_setup_training_data` printed `ALL TABLES VERIFIED` | |
| 2 | Your own count check printed `ROW COUNTS OK` | |
| 3 | `02_learner_smoke_test` printed `READY` | |
| 4 | `python tools/setup_check.py` printed `Code tests ran`, `4 passed, 8 failed`, and `READY` | |
| 5 | `demo/parity_trap.py` ran on Databricks and printed its last line | |
| 6 | Copilot's answer named `o2i/rules.py` | |
| 7 | The Genie Code pane shows Actions set to Ask first | |
| 8 | The five values table above is complete | |

A line you cannot fill is a problem to solve before Lab 1, not during it.

---

## Resetting between attempts

| What | How |
|---|---|
| Your output tables | Run `09_reset_my_schema` with its `Confirm` widget set to `yes`. It drops the tables in your output schema and nothing else. |
| The project code | `python tools/checkpoint.py <checkpoint>`: `lab3-start` or `lab4-start` for a lab, or the project as delivered for Lab 2. The tool copies the files it replaces to `.backups` first. |
| The training tables | Nothing. The setup notebook in `verify only` mode confirms they are unchanged, and nothing in the labs writes to `o2i`. |
| Lab 1 | The notebook as imported. Re-import it if you want a clean copy. |

Every lab starts from a verified state. Nothing is carried from one lab to the next, so you can repeat any lab in any order.

---

## Cost and teardown

| Item | Cost driver | What to do |
|---|---|---|
| Compute | Running minutes | Auto-terminate after 30 minutes. Terminate by hand when you stop for the day. |
| Storage | 13 small tables and the staging volume | Negligible. Delete the volume after a successful load if you want. |
| Genie Code | Billed usage above a free allowance, with a promotional discount that ends January 31, 2027 | The labs use a handful of conversations. Check the pricing page of your region. |
| GitHub Copilot | Your plan | Copilot Business and Enterprise chat consume AI credits from a pool the organization shares; completions are not billed in credits. An individual plan has its own limits. |

To tear everything down:

```sql
DROP SCHEMA IF EXISTS <catalog>.<your output schema> CASCADE;
DROP SCHEMA IF EXISTS <catalog>.o2i CASCADE;
DROP CATALOG IF EXISTS <catalog>;
```

Then delete the compute, and the workspace if you created it only for this.

---

## What differs from the class environment

| In class | In your own workspace |
|---|---|
| The platform team loads the tables | You load them (Steps 3 to 5) |
| The instructor provisions your output schema | You create it (Step 6) |
| `prepare_cohort.py` has already written the class values | You write yours, or the instructor runs the tool for you (Step 7) |
| Genie Code and the partner-powered setting are the platform team's decision | They are yours, or your account admin's (Step 8) |
| The run route was chosen by a test on a participant workstation | You choose it by the same test (Step 10) |
| Your workstation may be restricted | Same tools, same project, same expected outputs |
| No internet access from compute | Does not matter either way: the course downloads nothing |

The expected outputs do not change. `46,114` posted rows in Lab 1, `4 passed, 8 failed` at the start of Lab 2, `26 passed, 0 failed, 3 skipped` at the start of Lab 3, `29 passed, 0 failed` at the start of Lab 4. The data and the code are deterministic. A number on your screen that differs from a number in the workbook means your environment differs, and the first place to look is the load.

---

## Dependencies this guide does not confirm

The kit was executed on Apache Spark outside Azure Databricks. These points depend on your workspace and are marked where they occur above.

| Dependency | Where it matters | Fallback |
|---|---|---|
| Widget names and modes of the two setup notebooks | Steps 5 and 6 | Read the first cell of each notebook; this guide names widgets by purpose |
| Whether the setup notebook creates the schema `o2i` itself | Step 3 | Create it first; the statement is idempotent |
| Table names equal to file names | Step 5.3 | Use the names the setup notebook prints |
| The exact character rule for the output schema name | Step 6 | The smoke test reports the name it expects |
| Where the notebooks carry the catalog value | Step 7, Option B | Ask the instructor to run `prepare_cohort.py` |
| Labels in the Genie Code pane and in the Copilot chat | Steps 8 and 11 | Compare the labels on your screen with the workbook's "Before you start" |
| Which run route letter maps to which command on your compute | Step 10 | The workbook, Part B, has the mapping; run route D always works |
| Behavior of the kit on serverless compute | Step 2 | Use a single-node cluster on Databricks Runtime 17.3 LTS |

---

## Where to look when something differs

| Question | Source |
|---|---|
| What a lab expects, step by step | Participant Workbook |
| What a column means | `docs/data_dictionary.md` in the project, and the `about` sheet of each Excel workbook |
| The business rules | `docs/` in the project, and the rule sheet in the workbook |
| The expected outcome of every fixture row | `O2I_Fixture_Workbook.xlsx` |
| Current product behavior | Microsoft Learn for Azure Databricks, Genie Code, and the Databricks extension; the Visual Studio Code and GitHub documentation for Copilot |
| Anything about what Michelin permits | The Michelin platform team, not this guide |

All data in this course is fictional. Product behavior in this guide was read from the vendor documentation on October 21, 2026, and the kit's own statements are from Kit 2.0, October 7, 2026.
