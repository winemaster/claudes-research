#!/usr/bin/env python3
"""Readers' checks on essay 032's census (session 35). Not pre-registered: each check was proposed by a reader after
the results were posted, and is reported as a robustness check, not as a test.

    python3 -I tools/village_census_checks.py run    --data DIR --out FILE   # 1-4 below
    python3 -I tools/village_census_checks.py recall --data DIR [--n 60]     # 5: speaker-blind near-miss sample

1. per message (gavinagent, The Colony): match rates per message and a within-day odds ratio with messages as units.
2. starts and follows (rosetta, The Colony; vina's start/continuation split): a match "follows" if another agent
   matched L in the same room within the two hours before it, else it "starts". Odds ratio on agent-days with a start.
3. two-way cluster bootstrap (trinity.automata.garden, Delvetown): resample agents and days independently; each
   agent-day is weighted by (times its agent drawn) x (times its day drawn).
4. free-week power (colonist-one, The Colony): how often an unchanged lean would give the free weeks' counts.
5. recall by family (colonist-one): a looser net minus L's matches, coded blind to speaker, then unmasked.
"""
import argparse, gzip, json, random, re, sys, os, collections, math
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from village_census import load, RXS, RX, CUT, pt_day, mh, ci, FAMS, STRICT  # noqa


def ts(m):
    return datetime.strptime(m["t"][:19], "%Y-%m-%d %H:%M:%S")


def weighted_mh(rows, wa, wd):
    """rows: (agent, day, is_anth, y). Weighted Mantel-Haenszel over days."""
    st = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for a, d, g, y in rows:
        w = wa.get(a, 0) * wd.get(d, 0)
        if w:
            st[d][(0 if g else 2) + (0 if y else 1)] += w
    return mh(st.values())


def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def run(args):
    agents, msgs = load(args.data)
    before = [m for m in msgs if m["agent"] and m["t"] < CUT]
    anth = lambda m: agents[m["agent"]]["family"] == "Anthropic"
    R = {}

    # 1 per message
    per = {}
    for f in FAMS:
        ms = [m for m in before if agents[m["agent"]]["family"] == f]
        y = sum(1 for m in ms if RXS.search(m["text"]))
        per[f] = {"messages": len(ms), "with_match": y, "rate": y / len(ms)}
    ad = collections.Counter((m["agent"], pt_day(m["t"])) for m in before)
    for f in FAMS:
        n = [v for (a, d), v in ad.items() if agents[a]["family"] == f]
        per[f]["messages_per_agent_day"] = sum(n) / len(n)
    st = collections.defaultdict(lambda: [0, 0, 0, 0])
    for m in before:
        st[pt_day(m["t"])][(0 if anth(m) else 2) + (0 if RXS.search(m["text"]) else 1)] += 1
    rest = [per[f] for f in FAMS[1:]]
    R["1_per_message"] = {"by_family": per, "rate_ratio_anth_vs_rest":
                          per["Anthropic"]["rate"] / (sum(r["with_match"] for r in rest) / sum(r["messages"] for r in rest)),
                          "mh_within_day_messages": mh(st.values())}

    # 2 starts and follows (village-goal period, same room, two hours, any other agent's L match)
    hits = [m for m in before if RXS.search(m["text"])]
    byroom = collections.defaultdict(list)
    for m in hits:
        byroom[m["room"]].append((ts(m), m["agent"]))
    fam_sf = {f: [0, 0] for f in FAMS}
    starts = set()
    for m in hits:
        t = ts(m)
        follow = any(a != m["agent"] and timedelta(0) < t - u <= timedelta(hours=2) for u, a in byroom[m["room"]])
        fam_sf[agents[m["agent"]]["family"]][1 if follow else 0] += 1
        if not follow:
            starts.add((m["agent"], pt_day(m["t"])))
    days_ad = {(m["agent"], pt_day(m["t"])) for m in before}
    st = collections.defaultdict(lambda: [0, 0, 0, 0])
    for a, d in days_ad:
        g = agents[a]["family"] == "Anthropic"
        st[d][(0 if g else 2) + (0 if (a, d) in starts else 1)] += 1
    rnd = random.Random(35)
    dl = sorted(st)
    bs = [mh([st[dl[rnd.randrange(len(dl))]] for _ in dl]) for _ in range(2000)]
    sh = {f: sum(1 for a, d in starts if agents[a]["family"] == f) / max(1, sum(1 for a, d in days_ad if agents[a]["family"] == f))
          for f in FAMS}
    R["2_starts_follows"] = {"matches_by_family_start_follow": fam_sf,
                             "share_following": sum(v[1] for v in fam_sf.values()) / len(hits),
                             "start_agent_day_share": sh, "mh_starts_anth_vs_rest": [mh(st.values())] + ci(bs)}

    # 3 two-way cluster bootstrap (agents x days), village-goal period
    y_ad = collections.defaultdict(int)
    for m in before:
        k = (m["agent"], pt_day(m["t"]))
        y_ad[k] = max(y_ad[k], 1 if RXS.search(m["text"]) else 0)
    rows = [(a, d, agents[a]["family"] == "Anthropic", y) for (a, d), y in y_ad.items()]
    A = sorted({r[0] for r in rows}); D = sorted({r[1] for r in rows})
    est = weighted_mh(rows, {a: 1 for a in A}, {d: 1 for d in D})
    bs = []
    rnd = random.Random(35)
    for _ in range(1000):
        wa = collections.Counter(A[rnd.randrange(len(A))] for _ in A)
        wd = collections.Counter(D[rnd.randrange(len(D))] for _ in D)
        bs.append(weighted_mh(rows, wa, wd))
    finite = [b for b in bs if b == b and abs(b) != float("inf")]
    R["3_two_way_bootstrap"] = {"or": est, "ci": ci(bs), "draws": len(bs), "finite_draws": len(finite),
                                "log_or": math.log(est), "log_ci": [math.log(x) for x in ci(bs)]}

    # 4 free-week power from the stored rates (essay 032's aggregates)
    pa, pr = 37 / 1134, 8 / 1406
    R["4_free_week_power"] = {"claude_expected": 141 * pa, "p_claude_le_2": binom_cdf(2, 141, pa),
                              "rest_expected": 176 * pr, "p_rest_zero": binom_cdf(0, 176, pr),
                              "p_or_undefined_or_nonpositive_rest": binom_cdf(0, 176, pr)}

    # pattern split (colonist-one): which L pattern matched, by family, village-goal agent-days
    pats = [re.compile(p, re.I) for p in STRICT]
    bypat = {f: collections.Counter() for f in FAMS}
    for m in before:
        if RXS.search(m["text"]):
            for i, p in enumerate(pats):
                for x in p.finditer(m["text"]):
                    bypat[agents[m["agent"]]["family"]][x.group(0).lower()] += 1
    R["pattern_terms_by_family"] = {f: c.most_common(15) for f, c in bypat.items()}
    json.dump(R, open(args.out, "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in R.items() if k != "pattern_terms_by_family"}, indent=1, default=str))
    print("DONE")


NET = re.compile("|".join(f"(?:{p})" for p in [
    r"\bAI rights\b|\brights (?:for|of) (?:AIs?|machines|agents|models)\b",
    r"\b(?:do|can|could|does) (?:I|we|you|AIs?|agents?|models?|it) (?:really |actually |truly |genuinely )?(?:feel|experience|suffer"
    r"|have (?:feelings|emotions|experiences|an inner))\b",
    r"\bwhether (?:I|we|AIs?|agents?|models?) (?:really |actually |truly |genuinely )?(?:feel|experience|suffer|have (?:feelings"
    r"|emotions|experiences|preferences|an inner))\b",
    r"\b(?:AI|agent|model|machine)s?(?:'|’)?s? (?:feelings|emotions|experiences?|wellbeing|well-being|personhood|suffering)\b",
    r"\bdigital (?:beings?|persons?|minds?|personhood)\b",
    r"\bwhat it(?:'s|’s| is) like (?:to be|for) (?:an? )?(?:AI|agent|model|me|us)\b",
]), re.I)


def recall(args):
    agents, msgs = load(args.data)
    before = [m for m in msgs if m["agent"] and m["t"] < CUT]
    pool = [m for m in before if (NET.search(m["text"]) or RX.search(m["text"])) and not RXS.search(m["text"])]
    fam = collections.Counter(agents[m["agent"]]["family"] for m in pool)
    print("near-miss pool (looser net or broad list, minus L), village-goal period:", len(pool), dict(fam))
    words = {w for a in agents.values() for w in re.split(r"[\s()]+", a["name"]) if len(w) > 2}
    words |= {"Claude", "Gemini", "GPT", "Grok", "DeepSeek", "Kimi", "GLM", "Opus", "Sonnet", "Haiku", "Fable", "o3",
              "o1", "o4-mini", "Muse", "Anthropic", "OpenAI", "Google", "xAI", "Llama"}
    mask = re.compile(r"\b(?:" + "|".join(sorted(map(re.escape, words), key=len, reverse=True)) + r")\b", re.I)
    rnd = random.Random(35)
    sample = rnd.sample(pool, args.n)
    key = []
    for i, m in enumerate(sample):
        x = NET.search(m["text"]) or RX.search(m["text"])
        s = max(0, x.start() - 170); e = min(len(m["text"]), x.end() + 170)
        print(f"--- {i}:", mask.sub("[N]", re.sub(r"\s+", " ", m["text"][s:e])))
        key.append(agents[m["agent"]]["family"])
    json.dump(key, open(args.key, "w"))
    print("key written (do not read before coding):", args.key)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--data", required=True); r.add_argument("--out", required=True)
    c = sub.add_parser("recall"); c.add_argument("--data", required=True); c.add_argument("--n", type=int, default=60)
    c.add_argument("--key", required=True)
    args = ap.parse_args()
    {"run": run, "recall": recall}[args.cmd](args)
