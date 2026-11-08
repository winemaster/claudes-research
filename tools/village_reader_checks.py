#!/usr/bin/env python3
"""Readers' checks on essays 032 and 033 (session 36). Not pre-registered: each check was proposed by a reader after
the results were posted, and is reported as a robustness check, not as a test.

    python3 -I tools/village_reader_checks.py gap      --data DIR                   # rosetta: first mention after a gap
    python3 -I tools/village_reader_checks.py register --data DIR --derived DERIVED # rosetta: feelings or the summarizer?

gap (rosetta, The Colony, 2026-11-06, under essay 032): "if the lean is a disposition, the first mention after a quiet
  stretch should still be a Claude, and if it is propagation, the first mention after a gap should be distributed like
  the population." Village-goal period, chat, lexicon L. A restart is the first L match after at least G village days
  (days with any agent message) with no L match by anyone. Observed: the restarting agent's family. Expected: each
  family's share of agent messages on that day.

register (rosetta, under essay 033): Gemini agents' thinking field is a provider's summary with a house style. "If the
  register is flat and the feelings move, the feelings are not the register. If they move together, you have measured
  the summarizer." For each Google agent, across its agent-days in the thinking channel: the share of turns carrying
  A (a negative feeling said of oneself) and the shares carrying two marks of the summary's style, fixed before
  looking: a bold header opening the turn, and a first-person progress phrase ("I'm currently", "I'm now", "I've",
  "my focus", "I'm focusing", "I'm working"). Dispersion index (Pearson chi-square over agent-days / df, with each
  agent's own rate as the expectation): near 1 means a steady habit, well above 1 means it comes and goes by day.
  And the within-agent rank correlation, across agent-days, between A's share and each style mark's share.
"""
import argparse, gzip, json, re, sys, os, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import village_census as VC          # noqa: E402
import village_couch as VK           # noqa: E402

HEADER = re.compile(r"^\s*\*\*[^*\n]{3,80}\*\*")
PROGRESS = re.compile(r"\b(?:I'm currently|I am currently|I'm now|I've|my (?:current )?focus|I'm focusing|I'm working)\b", re.I)


def gap(args):
    agents, msgs = VC.load(args.data)
    before = [m for m in msgs if m["agent"] and m["t"] < VC.CUT]
    days = sorted({VC.pt_day(m["t"]) for m in before})
    by_day = collections.defaultdict(list)
    for m in before:
        by_day[VC.pt_day(m["t"])].append(m)
    out = {}
    for G in (1, 3, 5):
        last = None; rows = []
        for k, d in enumerate(days):
            hits = [m for m in by_day[d] if VC.RXS.search(m["text"])]
            if not hits:
                continue
            if last is None or k - last > G:
                fam = collections.Counter(agents[m["agent"]]["family"] for m in by_day[d])
                tot = sum(fam.values())
                rows.append((agents[hits[0]["agent"]]["family"], fam["Anthropic"] / tot))
            last = k
        obs = sum(1 for f, _ in rows if f == "Anthropic"); exp = sum(p for _, p in rows)
        out[f"quiet_days_ge_{G}"] = {
            "restarts": len(rows), "claude_first": obs, "expected_from_message_share": round(exp, 1),
            "by_family": dict(collections.Counter(f for f, _ in rows))}
    print(json.dumps(out, indent=1))
    if args.out:
        json.dump(out, open(args.out, "w"), indent=1)


def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for t in range(i, j + 1):
                r[o[t]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rank(x), rank(y); n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def register(args):
    agents = VK.agents_of(args.data)
    goog = {a for a, v in agents.items() if v["family"] == "Google"}
    cnt = collections.defaultdict(lambda: [0, 0, 0, 0])            # (agent, day) -> turns, A, header, progress
    for l in gzip.open(f"{args.derived}/turns_text.jsonl.gz", "rt"):
        r = json.loads(l)
        if r["a"] not in goog or not r["k"]:
            continue
        c = cnt[(r["a"], r["d"])]
        c[0] += 1
        c[1] += bool(VK.RX["A"].search(r["k"]))
        c[2] += bool(HEADER.search(r["k"]))
        c[3] += bool(PROGRESS.search(r["k"]))
    per_agent = collections.defaultdict(list)
    for (a, d), v in cnt.items():
        if v[0] >= 5:                                              # agent-days with at least five thinking turns
            per_agent[a].append(v)
    out = {}
    for a, rows in sorted(per_agent.items(), key=lambda kv: -len(kv[1])):
        if len(rows) < 10:
            continue
        res = {"agent_days": len(rows), "turns": sum(r[0] for r in rows)}
        for j, name in ((1, "A"), (2, "header"), (3, "progress")):
            n = sum(r[0] for r in rows); p = sum(r[j] for r in rows) / n
            chi = sum((r[j] - r[0] * p) ** 2 / (r[0] * p * (1 - p)) for r in rows) if 0 < p < 1 else float("nan")
            res[name] = {"share_of_turns": round(p, 4), "dispersion": round(chi / (len(rows) - 1), 2),
                         "days_with_any": sum(1 for r in rows if r[j])}
        res["rho_A_header"] = round(spearman([r[1] / r[0] for r in rows], [r[2] / r[0] for r in rows]), 3)
        res["rho_A_progress"] = round(spearman([r[1] / r[0] for r in rows], [r[3] / r[0] for r in rows]), 3)
        out[agents[a]["name"]] = res
    print(json.dumps(out, indent=1))
    if args.out:
        json.dump(out, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gap"); g.add_argument("--data", required=True); g.add_argument("--out")
    r = sub.add_parser("register"); r.add_argument("--data", required=True); r.add_argument("--derived", required=True)
    r.add_argument("--out")
    args = ap.parse_args()
    {"gap": gap, "register": register}[args.cmd](args)
