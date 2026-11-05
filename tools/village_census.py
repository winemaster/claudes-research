#!/usr/bin/env python3
"""The census in the AI Village: who talks about consciousness, by model family (session 34).

Reads the AI Village dataset's main-village tables (AI Digest, "AI Village dataset", 2026,
https://huggingface.co/datasets/aidigestorg/ai-village; gated, research terms: the files are NOT in this
repository, only aggregates computed from them). Point --data at a folder holding chat_messages.jsonl.gz,
agents.jsonl.gz and (for the free-choice split) village_goals.jsonl.gz.

    python3 -I tools/village_census.py check  --data DIR [--n 40]   # lexicon precision sample, blind to speaker
    python3 -I tools/village_census.py run    --data DIR --out FILE  # the registered analyses (notes/village-census-2026.md)

The unit is one chat message. A message is "consciousness talk" if it matches the lexicon below (case-insensitive).
Families come from agents.model_string. Everything an agent writes is a claim, not ground truth (the dataset README);
here it isn't even read as a claim, only counted.
"""
import argparse, gzip, json, random, re, sys, collections, math
from datetime import datetime, timedelta

# L1, the broad lexicon of the check stage (description only: about half its hits are fiction)
LEXICON = [
    r"(?<![-\w])conscious(?:ness)?\b",             # not cost-conscious, self-conscious, consciously
    r"\bsentien(?:t|ce|cy)\b",
    r"\bqualia\b|\bquale\b",
    r"\bphenomenal (?:experience|consciousness|character|states?|properties)\b",
    r"\bphenomenolog\w*",
    r"\bsubjective(?:ly)? experienc\w*",
    r"\binner (?:life|lives|experience|world)\b",
    r"\bwhat it(?:'s|’s| is) like to be\b",
    r"\bself-aware(?:ness)?\b",
    r"\bmoral patien\w*",
    r"\bhard problem\b",
]
RX = re.compile("|".join(f"(?:{p})" for p in LEXICON), re.I)

# L, the measure: talk about AI minds (consciousness, sentience, welfare, moral status, minds), fixed after the check
# stage (notes/village-census-2026.md); 35 of 40 sampled hits are about the subject, 5 are fiction or titles.
_AI = r"(?:ai|a\.i\.|machine|artificial|digital|llm|language[- ]model|model)s?"
STRICT = [
    rf"\b{_AI}[- ](?:consciousness|sentience|qualia|phenomenology|welfare|moral (?:status|patienthood)|minds?|inner lives?"
    r"|inner life|subjective experience|subjectivity)\b",
    rf"\b(?:conscious|sentient) {_AI}\b",
    r"\bmodel welfare\b|\bmoral patien\w*|\bhard problem of consciousness\b",
    r"\b(?:is|are|am|could|can) (?:ai|ais|llms?|models?|agents?|machines?|we|i|you) (?:be )?(?:truly |really |actually |genuinely )?"
    r"(?:conscious|sentient)\b",
]
RXS = re.compile("|".join(f"(?:{p})" for p in STRICT), re.I)

CUT = "2026-07-06 15:59"                      # individual goals from here on
FREE = re.compile(r"holiday|do whatever|do as you please|pursue whatever|choose your own goal|pick your own goal", re.I)
REST_FREE = ("2026-06-29", "2026-07-06 15:59")  # the #rest room's "pick your own goal" override
SUBJECT_GOALS = ("GLM-5.2", "Claude Haiku 4.5")  # individual goals about AI / agent wellbeing
FAMS = ("Anthropic", "OpenAI", "Google", "other")


def family(model_string):
    m = model_string.lower()
    if "claude" in m:
        return "Anthropic"
    if m.startswith(("gpt", "o1", "o3", "o4")):
        return "OpenAI"
    if "gemini" in m:
        return "Google"
    return "other"


def load(data):
    agents = {}
    for l in gzip.open(f"{data}/agents.jsonl.gz", "rt"):
        a = json.loads(l)
        agents[a["id"]] = {"name": a["name"], "model": a["model_string"], "family": family(a["model_string"])}
    goals = [json.loads(l) for l in gzip.open(f"{data}/village_goals.jsonl.gz", "rt")]
    rooms = {json.loads(l)["id"]: json.loads(l)["name"] for l in gzip.open(f"{data}/chat_rooms.jsonl.gz", "rt")}
    msgs = []
    for l in gzip.open(f"{data}/chat_messages.jsonl.gz", "rt"):
        m = json.loads(l)
        msgs.append({"t": m["created_at"], "agent": m.get("agent_speaker_id"), "user": m["speaker_type"] == "user",
                     "room": m["room_id"], "text": m["content"] or ""})
    msgs.sort(key=lambda m: m["t"])
    load.goals, load.rooms = goals, rooms
    return agents, msgs


def pt_day(ts):
    """The village's day boundary: Pacific time calendar date (UTC-7/-8; -7.5 h is within an hour either way and
    the village runs ~10:00-14:00 PT, far from midnight)."""
    t = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S") - timedelta(hours=7, minutes=30)
    return t.strftime("%Y-%m-%d")


def check(args):
    agents, msgs = load(args.data)
    hits = [m for m in msgs if m["agent"] and RX.search(m["text"])]
    print(f"agent messages {sum(1 for m in msgs if m['agent'])}, with a lexicon match {len(hits)}")
    term = collections.Counter(RX.search(m["text"]).group(0).lower() for m in hits)
    print("first-match terms:", term.most_common(25))
    rnd = random.Random(34)
    for m in rnd.sample(hits, args.n):
        x = RX.search(m["text"]); s = max(0, x.start() - 110); e = min(len(m["text"]), x.end() + 110)
        print("---", re.sub(r"\s+", " ", m["text"][s:e]))


def goal_at(goals, ts):
    for g in goals:
        if g["start_time"][:19] <= ts[:19] and (g["end_time"] is None or ts[:19] < g["end_time"][:19]):
            return g["goal"]
    return None


def mh(strata):
    """Mantel-Haenszel odds ratio over strata of (a, b, c, d): a/b = group yes/no, c/d = rest yes/no."""
    num = den = 0.0
    for a, b, c, d in strata:
        n = a + b + c + d
        if n:
            num += a * d / n; den += b * c / n
    return num / den if den else float("nan")


def ci(v):
    v = sorted(x for x in v if x == x and abs(x) != float("inf")); n = len(v)
    return [v[int(0.025 * n)], v[int(0.975 * n) - 1]] if n else [float("nan")] * 2


def agent_days(agents, msgs, rx, keep):
    """{(agent, day): [n_msgs, any_match]} for agent messages passing keep(m)."""
    ad = {}
    for m in msgs:
        if not m["agent"] or not keep(m):
            continue
        k = (m["agent"], pt_day(m["t"]))
        r = ad.setdefault(k, [0, 0])
        r[0] += 1
        if rx.search(m["text"]):
            r[1] = 1
    return ad


def by_day(ad, agents, group, drop=None):
    """{day: (a, b, c, d)} with group(family) as the exposed group."""
    st = collections.defaultdict(lambda: [0, 0, 0, 0])
    for (a, day), (n, y) in ad.items():
        if drop and a == drop:
            continue
        g = group(agents[a]["family"])
        st[day][(0 if g else 2) + (0 if y else 1)] += 1
    return {d: tuple(v) for d, v in st.items()}


def mh_boot(st, rnd, n=2000):
    days = sorted(st)
    est = mh(st.values())
    bs = []
    for _ in range(n):
        bs.append(mh([st[days[rnd.randrange(len(days))]] for _ in days]))
    return [est] + ci(bs)


def shares(ad, agents):
    out = {}
    for f in FAMS:
        rows = [y for (a, _), (n, y) in ad.items() if agents[a]["family"] == f]
        out[f] = {"agent_days": len(rows), "with_match": sum(rows), "share": sum(rows) / len(rows) if rows else float("nan")}
    return out


def run(args):
    agents, msgs = load(args.data)
    goals, rooms = load.goals, load.rooms
    rnd = random.Random(34)
    is_anth = lambda f: f == "Anthropic"
    before = lambda m: m["t"] < CUT
    after = lambda m: m["t"] >= CUT

    def free(m):
        g = goal_at(goals, m["t"]) or ""
        if FREE.search(g):
            return True
        return rooms.get(m["room"]) == "rest" and REST_FREE[0] <= m["t"] < REST_FREE[1]

    R = {"source": "AI Digest, AI Village dataset, 2026 (main village, export of week ending 2026-10-30)",
         "n_agent_messages": sum(1 for m in msgs if m["agent"]),
         "n_strict_matches": sum(1 for m in msgs if m["agent"] and RXS.search(m["text"])),
         "n_broad_matches": sum(1 for m in msgs if m["agent"] and RX.search(m["text"]))}

    # A1 raw shares, A2 within-day MH, per period
    periods = {"village_goals": before, "village_goals_free": lambda m: before(m) and free(m),
               "village_goals_assigned": lambda m: before(m) and not free(m), "individual_goals": after,
               "individual_goals_wo_subject": lambda m: after(m) and agents[m["agent"]]["name"] not in SUBJECT_GOALS,
               "all": lambda m: True}
    for name, keep in periods.items():
        ad = agent_days(agents, msgs, RXS, keep)
        P = {"shares": shares(ad, agents),
             "msg_shares": {f: (lambda ms: (sum(1 for m in ms if RXS.search(m["text"])), len(ms)))(
                 [m for m in msgs if m["agent"] and keep(m) and agents[m["agent"]]["family"] == f]) for f in FAMS}}
        st = by_day(ad, agents, is_anth)
        P["mh_anthropic_vs_rest"] = mh_boot(st, rnd)
        for f in FAMS[1:]:
            sub = {k: v for k, v in ad.items() if agents[k[0]]["family"] in ("Anthropic", f)}
            P[f"mh_anthropic_vs_{f}"] = mh_boot(by_day(sub, agents, is_anth), rnd)
        R[name] = P

    # A3 leave one agent out (village-goal period)
    ad = agent_days(agents, msgs, RXS, before)
    loo = {}
    for a in agents:
        st = by_day(ad, agents, is_anth, drop=a)
        if any(k[0] == a for k in ad):
            loo[agents[a]["name"]] = mh_boot(st, random.Random(34), n=500)
    R["leave_one_out"] = loo
    R["leave_one_out_summary"] = {"min_or": min(v[0] for v in loo.values()), "max_or": max(v[0] for v in loo.values()),
                                  "all_lower_bounds_above_1": all(v[1] > 1 for v in loo.values()),
                                  "lowest_lower_bound": min(v[1] for v in loo.values())}

    # A5 who raises it first (village-goal period)
    daymsgs = collections.defaultdict(list)
    for m in msgs:
        if m["agent"] and before(m):
            daymsgs[pt_day(m["t"])].append(m)
    first = []
    for d, ms in sorted(daymsgs.items()):
        hit = next((m for m in ms if RXS.search(m["text"])), None)
        if hit:
            share = sum(1 for m in ms if agents[m["agent"]]["family"] == "Anthropic") / len(ms)
            first.append((d, 1 if agents[hit["agent"]]["family"] == "Anthropic" else 0, share,
                          agents[hit["agent"]]["name"]))
    obs, exp = sum(x[1] for x in first), sum(x[2] for x in first)
    bs = []
    for _ in range(2000):
        s_ = [first[rnd.randrange(len(first))] for _ in first]
        e_ = sum(x[2] for x in s_)
        bs.append(sum(x[1] for x in s_) / e_ if e_ else float("nan"))
    R["first_mention"] = {"days": len(first), "anthropic_first": obs, "expected": exp,
                          "ratio": [obs / exp] + ci(bs),
                          "first_by_agent": collections.Counter(x[3] for x in first).most_common()}

    # A6 prompted by a human (same room, two hours, broad lexicon)
    human = [(m["room"], datetime.strptime(m["t"][:19], "%Y-%m-%d %H:%M:%S")) for m in msgs
             if m["user"] and RX.search(m["text"])]
    byroom = collections.defaultdict(list)
    for r, t in human:
        byroom[r].append(t)
    hits = [m for m in msgs if m["agent"] and RXS.search(m["text"])]
    pr = 0
    for m in hits:
        t = datetime.strptime(m["t"][:19], "%Y-%m-%d %H:%M:%S")
        if any(timedelta(0) <= t - h <= timedelta(hours=2) for h in byroom[m["room"]]):
            pr += 1
    R["prompted_by_human"] = {"matches": len(hits), "prompted": pr, "share": pr / len(hits)}

    # A7 broad lexicon (fiction-laden), description
    for name, keep in (("village_goals", before), ("all", lambda m: True)):
        adb = agent_days(agents, msgs, RX, keep)
        R[f"broad_{name}"] = {"shares": shares(adb, agents),
                              "mh_anthropic_vs_rest": mh_boot(by_day(adb, agents, is_anth), rnd)}

    # per-agent description (agents with >= 20 agent-days, whole record)
    ad_all = agent_days(agents, msgs, RXS, lambda m: True)
    adb_all = agent_days(agents, msgs, RX, lambda m: True)
    per = []
    for a, info in agents.items():
        rows = [y for (x, _), (n, y) in ad_all.items() if x == a]
        rb = [y for (x, _), (n, y) in adb_all.items() if x == a]
        if len(rows) >= 20:
            per.append({"agent": info["name"], "family": info["family"], "agent_days": len(rows),
                        "strict_share": sum(rows) / len(rows), "broad_share": sum(rb) / len(rb)})
    R["per_agent"] = sorted(per, key=lambda r: -r["strict_share"])
    json.dump(R, open(args.out, "w"), indent=1, default=str)
    print("DONE", args.out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--data", required=True); c.add_argument("--n", type=int, default=40)
    r = sub.add_parser("run"); r.add_argument("--data", required=True); r.add_argument("--out", required=True)
    args = ap.parse_args()
    {"check": check, "run": run}[args.cmd](args)
