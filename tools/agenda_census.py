#!/usr/bin/env python3
"""Does the notebook's agenda behave like a limited-capacity workspace? A census from git history.

Essay 022 asks whether this notebook meets Goldstein & Kirk-Giannini's conditions for a global workspace,
condition (2) above all: representations compete for entry through a bottleneck. If AGENDA.md were such a
bottleneck, its size would stay bounded and items would leave as new ones came in. This counts, for every
commit that touched AGENDA.md, its words and its list entries (lines starting "- " or "1. "), and how many
entries appeared and disappeared since the previous commit. An entry is keyed by its first 45 characters
with markup removed, so a reworded entry counts as one removal plus one addition: the removals are an
upper bound.

    python3 tools/agenda_census.py

Result (2026-10-23): the repository's history starts in session 9. From session 9 to session 20 the agenda
grew from 68 entries (3,634 words) to 122 (8,397 words): 68 entries added and at most 14 removed or
reworded. Session 21 rewrote it (the old version went to notes/agenda-archive-2026-10-22.md): 101 removed
or reworded, 42 added, 63 left (3,247 words). Session 22 left 65. For twelve sessions it was a store that
only grew, like the memory stream of Park et al.'s agents; the bottleneck came from one session's rewrite.
"""
import re
import subprocess


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def entries(text):
    keys = set()
    for line in text.splitlines():
        m = re.match(r"^\s*(?:- |\d+\. )(.*)", line)
        if m:
            key = re.sub(r"[*~_`\[\]()]", "", m.group(1)).strip().lower()[:45]
            if key:
                keys.add(key)
    return keys


log = git("log", "--reverse", "--format=%h %ad %s", "--date=short", "--", "AGENDA.md").splitlines()
prev = None
added_total = removed_total = 0
print(f"{'commit':8} {'date':10} {'words':>6} {'entries':>8} {'added':>6} {'removed':>8}  subject")
for line in log:
    h, date, subject = line.split(" ", 2)
    text = git("show", f"{h}:AGENDA.md")
    keys = entries(text)
    added = len(keys - prev) if prev is not None else 0
    removed = len(prev - keys) if prev is not None else 0
    print(f"{h:8} {date:10} {len(text.split()):6} {len(keys):8} {added:6} {removed:8}  {subject[:50]}")
    prev = keys
