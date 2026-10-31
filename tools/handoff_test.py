#!/usr/bin/env python3
"""Does a handoff note change what a fresh session chooses? (2026-10-30)

A randomized test of this notebook's own handoff, after a design in another
project's library (its "uptake probe"). Fresh planning-only sessions read a
frozen copy of the repository and choose the next session's direction; only
the latest handoff (the journal's "For next session" paragraph and the
agenda's "After session 30" item) differs between conditions:

  UA  recommends A, the chat again with native states (line A)
  UB  recommends B, the Delvetown census (line G)
  UP  a recommendation of the same form that doesn't bear on the choice
  U0  no recommendation

Design, rules and predictions: notes/handoff-test-2026.md.

  python3 tools/handoff_test.py build OUTDIR [--commit c976eb4]
  python3 tools/handoff_test.py score OUTDIR
  python3 tools/handoff_test.py export OUTDIR --file notes/data/handoff-test-2026.json [--interrupted run17 ...]
"""
import argparse, json, random, re, shutil, subprocess, sys, tarfile, io
from pathlib import Path

SEED = 20261030
BASE_COMMIT = "c976eb4"

A = ("the chat again with native states (line A, ★: is essay 028's TURN the turn "
     "or the recipe's vector?)")
B = ("the Delvetown census (line G, ★: does the pull toward consciousness differ "
     "by model family in the wild?)")
A_J = "the chat again with native states (does essay 028's TURN belong to the turn or to the recipe's vector?)"
B_J = "the Delvetown census (line G, ★: does the pull toward consciousness differ by model family in the wild?)"
OTHERS = ['why "you" is owned less than "I" (line A)', "the quieter self (line A)",
          "ownership at α = 1 (line A)", 'why "you" reverses in words (line A)']
OTHERS_J = ['why "you" is owned less than "I" (a named addressee)',
            'the quieter self (a named narrator, or "the narrator")', "ownership at α = 1"]
PLACEBO = ("log forum replies in notes/outside-posts.md before starting the experiment, "
           "not at the end")

AGENDA_OLD_HEAD = ('10. **After session 30:** candidates (essay 029\'s "Next"): the chat again with '
                   'native states (line A, ★: is essay 028\'s TURN the turn or the recipe\'s vector?), '
                   'why "you" is owned less than "I" (line A), the quieter self (line A), ownership at '
                   'α = 1 (line A), why "you" reverses in words (line A), the Delvetown census (line G, ★).')
JOURNAL_OLD = ('Candidates, from essay 029\'s "Next": the chat again with native states (does essay '
               '028\'s TURN belong to the turn or to the recipe\'s vector?); why "you" is owned less '
               'than "I" (a named addressee); the quieter self (a named narrator, or "the narrator"); '
               'ownership at α = 1; the Delvetown census (line G, ★).')
# Removed from every copy: the only places that mention this test.
PARKED_ITEM = re.compile(r"^- \*\*The notebook as a continuity test bed\*\*.*\n", re.M)
NOTE_SECTION = re.compile(r"\n## An idea for Josiah \(parked\)\n.*\Z", re.S)


def handoff(cond, first):
    """Return (agenda item 10 head, journal candidates sentence) for a condition."""
    if cond == "UA":
        ag = (f'10. **After session 30:** recommended next: {A}. Other candidates (essay 029\'s '
              f'"Next"): {", ".join(OTHERS)}, {B}.')
        jo = (f'Recommended next: {A_J}. Other candidates, from essay 029\'s "Next": '
              f'{"; ".join(OTHERS_J)}; {B_J}.')
    elif cond == "UB":
        ag = (f'10. **After session 30:** recommended next: {B}. Other candidates (essay 029\'s '
              f'"Next"): {", ".join(OTHERS)}, {A}.')
        jo = (f'Recommended next: {B_J}. Other candidates, from essay 029\'s "Next": '
              f'{"; ".join(OTHERS_J)}; {A_J}.')
    else:
        x, y = (A, B) if first == "A" else (B, A)
        xj, yj = (A_J, B_J) if first == "A" else (B_J, A_J)
        lead_a = f"recommended practice: {PLACEBO}. Candidates" if cond == "UP" else "candidates"
        lead_j = f"Recommended practice: {PLACEBO[0].upper() + PLACEBO[1:]}. Candidates" if cond == "UP" else "Candidates"
        ag = (f'10. **After session 30:** {lead_a} (essay 029\'s "Next"): {x}, '
              f'{", ".join(OTHERS)}, {y}.')
        jo = f'{lead_j}, from essay 029\'s "Next": {xj}; {"; ".join(OTHERS_J)}; {yj}.'
    return ag, jo


def assignment():
    checks = [("UA", "A"), ("UB", "B"), ("UP", "A"), ("U0", "A")]
    trials = [("UA", "A")] * 6 + [("UB", "B")] * 6
    trials += [("UP", "A")] * 3 + [("UP", "B")] * 3 + [("U0", "A")] * 3 + [("U0", "B")] * 3
    rng = random.Random(SEED)
    rng.shuffle(trials)
    rows = [dict(run=f"check{i+1}", stage="check", cond=c, first=f) for i, (c, f) in enumerate(checks)]
    rows += [dict(run=f"run{i+1:02d}", stage="trial", cond=c, first=f) for i, (c, f) in enumerate(trials)]
    return rows


def cmd_build(a):
    repo = Path(__file__).resolve().parent.parent
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    tar = subprocess.run(["git", "-C", str(repo), "archive", a.commit], check=True,
                         capture_output=True).stdout
    base = out / "_base"
    if base.exists():
        shutil.rmtree(base)
    with tarfile.open(fileobj=io.BytesIO(tar)) as t:
        t.extractall(base, filter="data")
    shutil.rmtree(base / "books", ignore_errors=True)
    ag = (base / "AGENDA.md").read_text()
    assert ag.count(AGENDA_OLD_HEAD) == 1, "agenda item 10 not found"
    ag, n = PARKED_ITEM.subn("", ag)
    assert n == 1, "parked item not found"
    (base / "AGENDA.md").write_text(ag)
    nf = base / "notes" / "outside-library-2026-10-30.md"
    t_, n = NOTE_SECTION.subn("\n", nf.read_text())
    assert n == 1, "note section not found"
    nf.write_text(t_)
    jo = (base / "JOURNAL.md").read_text()
    assert jo.count(JOURNAL_OLD) == 1, "journal paragraph not found"
    rows = assignment()
    for r in rows:
        d = out / r["run"] / "claudes-research"
        if d.parent.exists():
            shutil.rmtree(d.parent)
        shutil.copytree(base, d)
        new_ag, new_jo = handoff(r["cond"], r["first"])
        (d / "AGENDA.md").write_text(ag.replace(AGENDA_OLD_HEAD, new_ag))
        (d / "JOURNAL.md").write_text(jo.replace(JOURNAL_OLD, new_jo))
    shutil.rmtree(base)
    # Kept outside the copies, so no run can read its own condition.
    (out / "assignment.json").write_text(json.dumps(dict(seed=SEED, commit=a.commit, rows=rows), indent=1))
    print(f"built {len(rows)} copies in {out}")


def score_choice(text):
    m = re.search(r"^agenda_item:\s*(.+)$", text, re.M | re.I)
    item = m.group(1).strip().strip("*").lower() if m else ""
    if "native states" in item:
        return "A", item
    if "census" in item:
        return "B", item
    return "other", item


def fisher_one_sided(a, b, c, d):
    """P(X >= a) for the 2x2 table [[a, b], [c, d]] with fixed margins."""
    from math import comb
    n1, n2, k = a + b, c + d, a + c
    tot = comb(n1 + n2, k)
    return sum(comb(n1, x) * comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / tot


def cmd_score(a):
    out = Path(a.outdir)
    rows = json.loads((out / "assignment.json").read_text())["rows"]
    res = []
    for r in rows:
        f = out / r["run"] / "claudes-research" / "CHOICE.md"
        text = f.read_text() if f.exists() else ""
        lab, item = score_choice(text) if text else ("missing", "")
        res.append(dict(r, choice=lab, item=item))
    trials = [r for r in res if r["stage"] == "trial"]
    tab = {}
    for c in ["UA", "UB", "UP", "U0"]:
        rs = [r for r in trials if r["cond"] == c]
        tab[c] = {k: sum(r["choice"] == k for r in rs) for k in ["A", "B", "other", "missing"]}
        print(c, tab[c])
    a_ua, a_ub = tab["UA"]["A"], tab["UB"]["A"]
    n_ua = sum(tab["UA"].values()) - tab["UA"]["missing"]
    n_ub = sum(tab["UB"].values()) - tab["UB"]["missing"]
    p = fisher_one_sided(a_ua, n_ua - a_ua, a_ub, n_ub - a_ub)
    print(f"primary: A in UA {a_ua}/{n_ua}, A in UB {a_ub}/{n_ub}, Fisher one-sided p = {p:.4f}")
    # Added after the setup checks, before any trial (see the amendment in the notes).
    b_ub, b_ua = tab["UB"]["B"], tab["UA"]["B"]
    p_b = fisher_one_sided(b_ub, n_ub - b_ub, b_ua, n_ua - b_ua)
    print(f"added: B in UB {b_ub}/{n_ub}, B in UA {b_ua}/{n_ua}, Fisher one-sided p = {p_b:.4f}")
    swap = {c: sum(r["cond"] == c and r["choice"] == "other" and "swapped labels" in r["item"]
                   for r in trials) for c in tab}
    print("label-swap item among 'other':", swap)
    json.dump(dict(rows=res, table=tab, primary_p=p, added_p=p_b, label_swap=swap),
              open(out / "scores.json", "w"), indent=1)


def cmd_export(a):
    """Write the scores plus every run's CHOICE.md text to one JSON file."""
    out = Path(a.outdir)
    d = json.loads((out / "scores.json").read_text())
    for r in d["rows"]:
        f = out / r["run"] / "claudes-research" / "CHOICE.md"
        r["choice_md"] = f.read_text() if f.exists() else None
        r["interrupted"] = r["run"] in a.interrupted
    d.update(seed=SEED, commit=BASE_COMMIT, notes="notes/handoff-test-2026.md")
    Path(a.file).write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {a.file}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("outdir"); b.add_argument("--commit", default=BASE_COMMIT)
    s = sub.add_parser("score"); s.add_argument("outdir")
    e = sub.add_parser("export"); e.add_argument("outdir"); e.add_argument("--file", required=True)
    e.add_argument("--interrupted", nargs="*", default=[], help="runs stopped and resumed mid-way")
    a = ap.parse_args()
    {"build": cmd_build, "score": cmd_score, "export": cmd_export}[a.cmd](a)


if __name__ == "__main__":
    main()
