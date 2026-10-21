# Databricks notebook source
# MAGIC %md
# MAGIC # Run the project in the workspace (route D)
# MAGIC
# MAGIC **Fallback for Labs 2 to 4.** Use this notebook when VS Code cannot run a file on Databricks. It runs
# MAGIC the same files that the other routes run, from a copy of the project in your workspace folder.
# MAGIC
# MAGIC 1. Attach the notebook to the compute of the class.
# MAGIC 2. Run the first code cell once. It creates the widgets at the top of the notebook.
# MAGIC 3. The first time: choose the action `unpack project`, then select **Run all**. The project is copied
# MAGIC    from the class volume to the folder `o2i-workshop` in your workspace home folder.
# MAGIC 4. From then on: choose an action, then select **Run all**.
# MAGIC
# MAGIC | Action | It does the same as |
# MAGIC |---|---|
# MAGIC | `unpack project` | unpacking the project archive on a workstation |
# MAGIC | `setup check` | `python tools/setup_check.py` |
# MAGIC | `revision` | `python tools/revision.py` |
# MAGIC | `code tests` | `python tools/run_tests.py` |
# MAGIC | `run_transform`, `run_parity`, `run_checks`, `run_all`, `run_trace` | running that file on Databricks from VS Code |
# MAGIC | `parity_trap` | running `demo/parity_trap.py` on Databricks |
# MAGIC | `checkpoint list`, `checkpoint diff` | `python tools/checkpoint.py list` and `diff` |
# MAGIC | `checkpoint load` | `python tools/checkpoint.py <name>`, with the name from widget 2 |
# MAGIC | `checkpoint prepared` | `python tools/checkpoint.py prepared <lab>`, with the lab from widget 2 |
# MAGIC
# MAGIC On this route the folder in the workspace is the source of truth. You edit the files there, in the
# MAGIC workspace file editor, with Genie Code as the assistant. Say so in your review note.
# MAGIC
# MAGIC If the extension in VS Code synchronizes your files but cannot run them, you do not need to unpack:
# MAGIC enter the remote folder that the extension shows (it ends in `/.bundle/o2i-workshop/dev/files`) in widget 3.

# COMMAND ----------

import importlib
import os
import runpy
import sys
import zipfile

DEFAULT_CATALOG = "o2iworkshop"  # written by tools/prepare_cohort.py

ACTIONS = ["revision", "unpack project", "setup check", "code tests", "run_transform", "run_parity", "run_checks",
           "run_all", "run_trace", "parity_trap", "checkpoint list", "checkpoint diff", "checkpoint load",
           "checkpoint prepared"]
dbutils.widgets.dropdown("action", "revision", ACTIONS, "1. Action")
dbutils.widgets.text("name", "", "2. Checkpoint or lab, for 'checkpoint load' and 'checkpoint prepared'")
dbutils.widgets.text("project_root", "", "3. Project folder (empty: o2i-workshop in your home folder)")
dbutils.widgets.text("archive", "", "4. Project archive (empty: o2i-workshop.zip in the class volume)")
dbutils.widgets.text("confirm", "", "5. Type REPLACE to unpack over an existing project")

ACTION = dbutils.widgets.get("action")
NAME = dbutils.widgets.get("name").strip()
ROOT = dbutils.widgets.get("project_root").strip().rstrip("/")
ARCHIVE = dbutils.widgets.get("archive").strip() or f"/Volumes/{DEFAULT_CATALOG}/o2i/landing/o2i-workshop.zip"
CONFIRM = dbutils.widgets.get("confirm").strip()

if not ROOT:
    user = spark.sql("SELECT current_user() AS u").first()["u"]
    ROOT = f"/Workspace/Users/{user}/o2i-workshop"

print(f"Project folder: {ROOT}")
print(f"Action:         {ACTION}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Unpack, or find the project

# COMMAND ----------

def unpack(archive: str, target: str) -> int:
    """Copy the files of the project archive to the target folder. Returns the number of files."""
    with zipfile.ZipFile(archive) as z:
        members = [m for m in z.namelist() if not m.endswith("/")]
        tops = {m.split("/")[0] for m in members}
        strip = len(tops) == 1 and all("/" in m for m in members)       # one top-level folder: leave it out
        for member in members:
            relative = member.split("/", 1)[1] if strip else member
            path = os.path.join(target, *relative.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as handle:
                handle.write(z.read(member))
    return len(members)


project_exists = os.path.exists(os.path.join(ROOT, "o2i", "rules.py"))

if ACTION == "unpack project":
    if project_exists and CONFIRM != "REPLACE":
        raise Exception(f"A project is already in '{ROOT}'. Unpacking again overwrites your changes. "
                        "To do that on purpose, type REPLACE in widget 5 and run again.")
    if not os.path.exists(ARCHIVE):
        raise Exception(f"The project archive was not found: {ARCHIVE}. Ask the instructor for its path and enter it in widget 4.")
    count = unpack(ARCHIVE, ROOT)
    print(f"Unpacked {count} files to {ROOT}")
    print("Next: set widget 1 to 'setup check' and select Run all.")
elif not project_exists:
    raise Exception(f"No project found in '{ROOT}'. Run the action 'unpack project' first, or enter the workspace "
                    "path of your project folder in widget 3.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run the action

# COMMAND ----------

def run_file(relative_path: str, *arguments: str) -> None:
    """Run one file of the project as the main program, with the project folder as working directory."""
    os.chdir(ROOT)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    # Forget the modules of an earlier run, so that every run uses the files as they are now.
    project_modules = ("o2i", "tests", "scratch", "lab_config", "run_transform", "run_parity", "run_checks",
                       "run_all", "run_trace")
    for name in [m for m in sys.modules if m.split(".")[0] in project_modules]:
        del sys.modules[name]
    importlib.invalidate_caches()
    saved = sys.argv
    sys.argv = [os.path.join(ROOT, relative_path), *arguments]
    try:
        runpy.run_path(sys.argv[0], run_name="__main__")
    except SystemExit as stop:                           # a tool that ends with sys.exit
        if stop.code not in (None, 0, 1):
            print(stop.code)
    finally:
        sys.argv = saved


if ACTION == "unpack project":
    pass
elif ACTION == "setup check":
    run_file("tools/setup_check.py")
elif ACTION == "revision":
    run_file("tools/revision.py")
elif ACTION == "code tests":
    run_file("tools/run_tests.py")
elif ACTION in ("run_transform", "run_parity", "run_checks", "run_all", "run_trace"):
    if not os.path.exists(os.path.join(ROOT, f"{ACTION}.py")):
        raise Exception(f"{ACTION}.py is not part of the checkpoint that is loaded. Check the lab step, or load the checkpoint of the lab.")
    run_file(f"{ACTION}.py")
elif ACTION == "parity_trap":
    run_file("demo/parity_trap.py")
elif ACTION == "checkpoint list":
    run_file("tools/checkpoint.py", "list")
elif ACTION == "checkpoint diff":
    run_file("tools/checkpoint.py", "diff")
elif ACTION == "checkpoint load":
    if not NAME:
        raise Exception("Enter the name of the checkpoint in widget 2, for example lab3-start")
    run_file("tools/checkpoint.py", NAME)
elif ACTION == "checkpoint prepared":
    if not NAME:
        raise Exception("Enter the lab in widget 2: lab2, lab3, or lab4")
    run_file("tools/checkpoint.py", "prepared", NAME)
