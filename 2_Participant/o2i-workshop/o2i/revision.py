"""Identify the code that ran: a fingerprint of the o2i package, and the Git commit when there is one.

The fingerprint is calculated where the code runs. When the fingerprint that a remote run prints
equals the fingerprint on your workstation, the revision that you reviewed is the revision that ran.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
from typing import Optional

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(PACKAGE_DIR)


def fingerprint() -> str:
    """Twelve hex characters that change when any .py file of the o2i package changes."""
    digest = hashlib.sha256()
    for name in sorted(n for n in os.listdir(PACKAGE_DIR) if n.endswith(".py")):
        with open(os.path.join(PACKAGE_DIR, name), "rb") as handle:
            content = handle.read().replace(b"\r\n", b"\n")      # the same on Windows and on Databricks
        digest.update(name.encode("utf-8") + b"\0" + content + b"\0")
    return digest.hexdigest()[:12]


def git_commit() -> Optional[str]:
    """Short commit hash of the project, with '+changes' when files differ from it. None without Git."""
    try:
        def git(*args):
            return subprocess.run(["git", "-C", PROJECT_DIR, *args], capture_output=True, text=True, timeout=10)
        head = git("rev-parse", "--short", "HEAD")
        if head.returncode != 0:
            return None
        dirty = git("status", "--porcelain", "--", "o2i").stdout.strip()
        return head.stdout.strip() + ("+changes" if dirty else "")
    except Exception:
        return None


def describe() -> str:
    commit = git_commit()
    return f"o2i revision {fingerprint()}" + (f" (git {commit})" if commit else "")
