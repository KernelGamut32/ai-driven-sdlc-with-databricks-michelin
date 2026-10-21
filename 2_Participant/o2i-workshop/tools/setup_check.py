"""Check this workstation before the workshop. Nothing is installed and nothing is sent anywhere.

    python tools/setup_check.py

It checks Python, runs the code tests, prepares a local Git repository when Git is available, and
prints the revision of the code. Send the output to the instructor if a line says CHECK.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def git(*args):
    try:
        return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, timeout=30)
    except Exception:
        return None


def prepare_git():
    """Create a local repository with one commit when Git is available. The labs work without it."""
    without = "The labs work without it: use 'python tools/checkpoint.py diff' to review changes."
    present = git("--version")
    if present is None or present.returncode != 0:
        print(f"NOTE  Git was not found. {without}")
        return
    top = git("rev-parse", "--show-toplevel")
    if top.returncode != 0:
        git("init", "-q")
        git("add", "-A")
        git("-c", "user.name=O2I workshop", "-c", "user.email=o2i-workshop@example.invalid",
            "commit", "-q", "-m", "workshop project as delivered")
        head = git("rev-parse", "--short", "HEAD")
        if head is not None and head.returncode == 0:
            print("OK    Git: local repository created with one commit. Nothing is pushed anywhere.")
        else:
            print(f"NOTE  Git is installed, but a repository could not be created in this folder. {without}")
    elif os.path.samefile(top.stdout.strip(), ROOT):
        print("OK    Git: this folder is a local repository.")
    else:
        print(f"NOTE  This folder is inside another Git repository ({top.stdout.strip()}). The tools leave it alone.")
        print("      Review changes with 'python tools/checkpoint.py diff', or unpack the project outside that repository.")


def main():
    problems = 0
    version = sys.version_info
    ok = version >= (3, 9)
    problems += 0 if ok else 1
    print(f"{'OK   ' if ok else 'CHECK'} Python {version.major}.{version.minor}.{version.micro} (3.9 or later is needed)")

    tests = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "run_tests.py")], capture_output=True, text=True)
    summary = (tests.stdout.strip().splitlines() or ["no output"])[-1]
    ran = re.match(r"\d+ passed, \d+ failed", summary) is not None
    problems += 0 if ran else 1
    print(f"{'OK   ' if ran else 'CHECK'} Code tests ran: {summary}")

    with open(os.path.join(ROOT, "databricks.yml"), encoding="utf-8") as handle:
        host = re.search(r"host:\s*(\S+)", handle.read())
    placeholder = host is None or "0000000000000000" in host.group(1)
    problems += 1 if placeholder else 0
    print(f"{'CHECK' if placeholder else 'OK   '} Workspace in databricks.yml: {host.group(1) if host else 'missing'}"
          + (" (placeholder: ask the instructor for the prepared project)" if placeholder else ""))

    import lab_config
    print(f"OK    Catalog in lab_config.py: {lab_config.CATALOG}")

    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        print("NOTE  This project runs in the workspace. No Git repository is created here: review changes with the action 'checkpoint diff'.")
    else:
        prepare_git()

    from o2i import revision
    print(f"OK    {revision.describe()}")
    print("READY" if problems == 0 else f"NOT READY: {problems} line(s) say CHECK")


if __name__ == "__main__":
    main()
