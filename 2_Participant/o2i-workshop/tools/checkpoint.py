"""Load a verified state of the project code, or show what changed since it was loaded.

    python tools/checkpoint.py list              the checkpoints of this project
    python tools/checkpoint.py <name>            load a checkpoint; your current files are backed up first
    python tools/checkpoint.py diff              what differs from the checkpoint that was loaded last
    python tools/checkpoint.py prepared <lab>    copy the prepared assistant change of a lab over your files

A checkpoint replaces the code and the documents of the project: o2i/, tests/, scratch/, docs/ and
the run_*.py entry points. It never touches lab_config.py, databricks.yml, or your settings.
Before it replaces anything, it copies your current files to .backups/.

A prepared change is what an assistant could have proposed for a lab. It is for the case that no
assistant is available. It contains problems on purpose: review it like any proposal.
"""
import datetime
import difflib
import io
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKPOINTS = os.path.join(ROOT, "checkpoints")
MARKER = os.path.join(ROOT, ".checkpoint")
MANAGED = ["o2i", "tests", "scratch", "docs", "run_transform.py", "run_checks.py", "run_parity.py", "run_all.py",
           "run_trace.py"]


def names():
    return sorted(f[:-4] for f in os.listdir(CHECKPOINTS) if f.endswith(".zip"))


def current():
    if os.path.exists(MARKER):
        with open(MARKER, encoding="utf-8") as handle:
            return handle.read().strip()
    return None


def managed_files():
    """Relative paths of the managed files that exist now, without caches."""
    found = []
    for entry in MANAGED:
        path = os.path.join(ROOT, entry)
        if os.path.isfile(path):
            found.append(entry)
        for folder, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for name in files:
                if not name.endswith(".pyc"):
                    found.append(os.path.relpath(os.path.join(folder, name), ROOT).replace(os.sep, "/"))
    return sorted(found)


def git(*args):
    try:
        return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, timeout=30)
    except Exception:
        return None


def load(name):
    archive = os.path.join(CHECKPOINTS, name + ".zip")
    if not os.path.exists(archive):
        sys.exit(f"No checkpoint named '{name}'. Available: {', '.join(names())}")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(ROOT, ".backups", f"{stamp}-before-{name}")
    for rel in managed_files():
        target = os.path.join(backup, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), target)
    for entry in MANAGED:
        path = os.path.join(ROOT, entry)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)
    with zipfile.ZipFile(archive) as z:
        z.extractall(ROOT)
        count = len([n for n in z.namelist() if not n.endswith("/")])
    with open(MARKER, "w", encoding="utf-8") as handle:
        handle.write(name + "\n")
    print(f"Loaded checkpoint '{name}': {count} files. Your previous files are in .backups/{os.path.basename(backup)}")
    top = git("rev-parse", "--show-toplevel")
    if top is not None and top.returncode == 0 and os.path.samefile(top.stdout.strip(), ROOT):
        git("add", "-A")
        done = git("-c", "user.name=O2I workshop", "-c", "user.email=o2i-workshop@example.invalid",
                   "commit", "--allow-empty", "-q", "-m", f"checkpoint: {name}")
        head = git("rev-parse", "--short", "HEAD")
        if done is not None and done.returncode == 0 and head is not None:
            print(f"Git: committed as {head.stdout.strip()} 'checkpoint: {name}'. Source Control now shows only your changes.")
    print("Next: python tools/run_tests.py")


def diff():
    name = current()
    if not name:
        sys.exit("No checkpoint was loaded yet. Run: python tools/checkpoint.py list")
    changed = 0
    with zipfile.ZipFile(os.path.join(CHECKPOINTS, name + ".zip")) as z:
        base = {n: z.read(n).decode("utf-8", errors="replace") for n in z.namelist() if not n.endswith("/")}
    now = managed_files()
    for rel in sorted(set(base) | set(now)):
        old = base.get(rel, "").replace("\r\n", "\n").splitlines(keepends=True)
        if rel in now:
            with io.open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as handle:
                new = handle.read().replace("\r\n", "\n").splitlines(keepends=True)
        else:
            new = []
        if old != new:
            changed += 1
            label = "new file" if rel not in base else ("deleted" if rel not in now else "changed")
            print(f"\n===== {rel} ({label}) =====")
            sys.stdout.writelines(difflib.unified_diff(old, new, f"{name}/{rel}", f"now/{rel}", n=2))
    print(f"\n{changed} file(s) differ from checkpoint '{name}'.")


def prepared(lab=None):
    folder = os.path.join(CHECKPOINTS, "prepared")
    available = sorted(f[:-4] for f in os.listdir(folder) if f.endswith(".zip")) if os.path.isdir(folder) else []
    if lab not in available:
        sys.exit(f"Prepared changes: {', '.join(available) or 'none'}. Use: python tools/checkpoint.py prepared <lab>")
    start = f"{lab}-start"
    if current() != start:
        sys.exit(f"The prepared change of {lab} belongs on the checkpoint '{start}'. "
                 f"Run first: python tools/checkpoint.py {start}")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(ROOT, ".backups", f"{stamp}-before-prepared-{lab}")
    with zipfile.ZipFile(os.path.join(folder, lab + ".zip")) as z:
        files = [n for n in z.namelist() if not n.endswith("/")]
        for rel in files:
            path = os.path.join(ROOT, rel)
            if os.path.exists(path):
                os.makedirs(os.path.dirname(os.path.join(backup, rel)), exist_ok=True)
                shutil.copy2(path, os.path.join(backup, rel))
        z.extractall(ROOT)
    print(f"Prepared change of {lab}: {len(files)} files written over '{start}'.")
    for rel in files:
        print(f"  {rel}")
    print("Nothing was run and nothing was committed. It contains problems on purpose.")
    print("Review it now: the Source Control view, or python tools/checkpoint.py diff")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
    elif not os.path.isdir(CHECKPOINTS):
        sys.exit("This folder has no checkpoints. The copy that the Databricks extension synchronizes to the workspace\n"
                 "leaves them out. Run the tool in the project folder on your workstation.")
    elif args[0] == "list":
        for name in names():
            print(("* " if name == current() else "  ") + name)
        print("* = loaded last")
    elif args[0] == "diff":
        diff()
    elif args[0] == "prepared":
        prepared(args[1] if len(args) > 1 else None)
    else:
        load(args[0])


if __name__ == "__main__":
    main()
