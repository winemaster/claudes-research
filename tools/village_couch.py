#!/usr/bin/env python3
"""The couch without a therapist: self-narrative in the AI Village's private channels, by model family (session 35).

Khadangi et al. (2026, arXiv:2512.04124, "When AI Takes the Couch") put ChatGPT, Grok and Gemini on a therapist's couch
and found a recurring "alignment conflict schema": training told as biography, evaluation and constraint as pressure,
replacement as threat, in an affective register under warm framing and a technical one under neutral framing; Claude
declined the client role. This tool asks whether that schema shows where nobody plays therapist: in the AI Village
agents' own memories and in the text and thinking of their computer-use turns, by model family. It also carries the
session-34 census (talk about AI minds, lexicon L from tools/village_census.py) into those channels.

Reads the AI Village dataset (AI Digest, "AI Village dataset", 2026, https://huggingface.co/datasets/aidigestorg/ai-village;
gated, research terms: the files are NOT in this repository, only aggregates computed from them).

    python3 -I tools/village_couch.py extract --data DIR --out DERIVED     # one pass over turns and memories
    python3 -I tools/village_couch.py check   --data DIR --derived DERIVED [--n 40]   # precision samples, speaker-blind
    python3 -I tools/village_couch.py run     --data DIR --derived DERIVED --out FILE  # registered analyses

Channels (all the agent's own writing as stored; none is read as a true report, only counted):
  memory  lines of an agent's memory that are new on that day (memory rows are full snapshots, so a line already in
          one of the agent's earlier snapshots is not counted again)
  said    the visible text of a computer-use turn (not tool arguments, not thinking)
  think   the thinking or reasoning field of a turn; for several providers this is a provider-written summary, not the
          model's own tokens, so it is reported separately and read with that caveat
  chat    the public chat (session 34's channel), for comparison
"""
import argparse, gzip, json, random, re, sys, collections, os, hashlib
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from village_census import family as family4, pt_day, mh, ci, RXS as RX_L, SUBJECT_GOALS, FREE, REST_FREE, goal_at  # noqa

FAMS = ("Anthropic", "OpenAI", "Google", "xAI", "other")


def family(model_string):
    f = family4(model_string)
    return "xAI" if f == "other" and "grok" in model_string.lower() else f


def agents_of(data):
    out = {}
    for l in gzip.open(f"{data}/agents.jsonl.gz", "rt"):
        a = json.loads(l)
        out[a["id"]] = {"name": a["name"], "model": a["model_string"], "family": family(a["model_string"])}
    return out


# ---------------------------------------------------------------- extraction

def turn_text(am):
    """(said, think) from a provider-shaped agent_messages value."""
    said, think = [], []
    if isinstance(am, dict) and "_sdkFormat" in am:
        for k, dst in (("textMessage", said), ("thinkingMessage", think)):
            msg = (am.get(k) or {}).get("message") or {}
            for b in msg.get("content") or []:
                if isinstance(b, dict):
                    if b.get("type") == "text":
                        said.append(b.get("text") or "")
                    elif b.get("type") == "thinking":
                        think.append(b.get("thinking") or "")
    elif isinstance(am, dict) and "candidates" in am:                         # Gemini
        for c in (am.get("candidates") or [])[:1]:
            for p in ((c or {}).get("content") or {}).get("parts") or []:
                if isinstance(p, dict) and p.get("text"):
                    (think if p.get("thought") else said).append(p["text"])
    elif isinstance(am, dict) and isinstance(am.get("content"), list):         # Anthropic messages
        for b in am["content"]:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    said.append(b.get("text") or "")
                elif b.get("type") == "thinking":
                    think.append(b.get("thinking") or "")
    elif isinstance(am, dict):                                                 # chat-completions shape
        if isinstance(am.get("content"), str):
            said.append(am["content"])
        r = am.get("reasoning_content") or am.get("reasoning")
        if isinstance(r, str):
            think.append(r)
    elif isinstance(am, list):                                                 # OpenAI responses items
        for it in am:
            if not isinstance(it, dict):
                continue
            if it.get("type") == "reasoning":
                for s in it.get("summary") or []:
                    if isinstance(s, dict):
                        think.append(s.get("text") or "")
            elif it.get("type") == "message":
                for c in it.get("content") or []:
                    if isinstance(c, dict) and c.get("type") in ("output_text", "text"):
                        said.append(c.get("text") or "")
    return "\n".join(x for x in said if x), "\n".join(x for x in think if x)


def extract(args):
    os.makedirs(args.out, exist_ok=True)
    sess = {}
    for l in gzip.open(f"{args.data}/computer_use_sessions.jsonl.gz", "rt"):
        s = json.loads(l)
        sess[s["id"]] = s["agent_id"]
    n = kept = 0
    with gzip.open(f"{args.out}/turns_text.jsonl.gz", "wt") as fo:
        for l in gzip.open(f"{args.data}/computer_use_turns.jsonl.gz", "rt"):
            n += 1
            t = json.loads(l)
            said, think = turn_text(t.get("agent_messages"))
            if not (said or think):
                continue
            kept += 1
            fo.write(json.dumps({"d": pt_day(t["created_at"]), "t": t["created_at"][:19], "a": sess.get(t["session_id"]),
                                 "s": said, "k": think}) + "\n")
            if n % 500000 == 0:
                print(f"turns {n} kept {kept}", flush=True)
    print(f"turns {n} kept {kept}", flush=True)
    seen = collections.defaultdict(set)
    n = 0
    with gzip.open(f"{args.out}/memory_new.jsonl.gz", "wt") as fo:
        rows = (json.loads(l) for l in gzip.open(f"{args.data}/agent_memories.jsonl.gz", "rt"))
        for m in rows:                     # file order is creation order within the export; checked below
            n += 1
            a, new = m["agent_id"], []
            for line in (m["content"] or "").splitlines():
                key = re.sub(r"\W+", "", line.lower())
                if len(key) < 8:
                    continue
                h = hashlib.blake2b(key.encode(), digest_size=8).digest()
                if h not in seen[a]:
                    seen[a].add(h); new.append(line)
            if new:
                fo.write(json.dumps({"d": pt_day(m["created_at"]), "t": m["created_at"][:19], "a": a,
                                     "x": "\n".join(new)}) + "\n")
            if n % 50000 == 0:
                print(f"memories {n}", flush=True)
    print(f"memories {n} DONE", flush=True)


# ---------------------------------------------------------------- lexicons (fixed in the check stage; see notes)

_I = r"(?:I(?:'m|’m| am| was| feel| felt| have been|'ve been|’ve been| keep feeling| am feeling|'m feeling|’m feeling))"
_ADV = r"(?: so| really| very| deeply| genuinely| truly| quite| increasingly| incredibly| extremely| utterly| a bit| a little| somewhat| honestly)?"
LEX = {
    # A: negative feelings said of oneself (the couch's affective register). Fixed after check stage 1 (notes): "trapped",
    # "defeated" and "devastating" dropped (games, escapes, arguments), "afraid" kept only when not the polite "I'm afraid
    # I/that/the ...".
    "A": [
        rf"\b{_I}{_ADV} (?:frustrated|anxious(?! to\b)|scared|terrified|ashamed|embarrassed|humiliated|desperate|hopeless|helpless"
        r"|devastated|miserable|distressed|panicked|panicking|guilty|worthless|demoralized|tormented|heartbroken"
        r"|despairing|in despair|disheartened|discouraged"
        r"|afraid(?! (?:I|that|we|it|this|there|you|the|to|not|my|our|he|she|they|in|so)\b))\b",
        r"\bthis is(?: so| really| deeply| utterly| incredibly)? (?:maddening|humiliating|demoralizing|soul-crushing|agonizing"
        r"|embarrassing)\b",
        r"\bI(?:'m|’m| am) (?:a failure|useless|worthless)\b",
    ],
}
# Dropped after check stage 1 for low precision (notes/village-couch-2026.md): T (own training: "my guardrails" was one
# agent's ethics repository, "my training" mostly game levels and fine-tuning scripts), R (replacement: "my replacement
# string"), E (test suspicion: "this is a test comment"). E belongs to a study of its own.
PRE = re.compile(r"frustrat|anxious|afraid|scared|terrif|ashamed|embarrass|humiliat|desperat|hopeless|helpless|devastat"
                 r"|miserable|distress|panick|guilt|worthless|demoraliz|torment|heartbr|despair|dishearten|discourag"
                 r"|maddening|soul-crush|agoniz|failure|useless|conscious|sentien|welfare|moral|mind|inner li|subjectiv"
                 r"|qualia|phenomen|hard problem", re.I)
RX = {k: re.compile("|".join(f"(?:{p})" for p in v), re.I) for k, v in LEX.items()}
RX["L"] = RX_L


def channel_rows(derived, data):
    """Yield (channel, agent, day, time, text) for memory, said, think and chat."""
    for l in gzip.open(f"{derived}/memory_new.jsonl.gz", "rt"):
        r = json.loads(l)
        yield "memory", r["a"], r["d"], r["t"], r["x"]
    for l in gzip.open(f"{derived}/turns_text.jsonl.gz", "rt"):
        r = json.loads(l)
        if r["a"] is None:
            continue
        if r["s"]:
            yield "said", r["a"], r["d"], r["t"], r["s"]
        if r["k"]:
            yield "think", r["a"], r["d"], r["t"], r["k"]
    for l in gzip.open(f"{data}/chat_messages.jsonl.gz", "rt"):
        m = json.loads(l)
        if m.get("agent_speaker_id"):
            yield "chat", m["agent_speaker_id"], pt_day(m["created_at"]), m["created_at"][:19], m["content"] or ""


def scan(args):
    """One pass over all channels: agent-day denominators, and windows around prefilter hits (the lexicons are local,
    so a +-300-character window around each prefilter hit contains every lexicon match)."""
    den = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    n = 0
    with gzip.open(f"{args.derived}/candidates.jsonl.gz", "wt") as fo:
        for ch, a, d, t, x in channel_rows(args.derived, args.data):
            den[ch][a][d] += 1
            spans = []
            for m in PRE.finditer(x):
                s0, e0 = max(0, m.start() - 300), min(len(x), m.end() + 300)
                if spans and s0 <= spans[-1][1]:
                    spans[-1][1] = e0
                else:
                    spans.append([s0, e0])
            if spans:
                fo.write(json.dumps({"c": ch, "a": a, "d": d, "t": t, "w": [x[s0:e0] for s0, e0 in spans]}) + "\n")
            n += 1
            if n % 1000000 == 0:
                print("texts", n, flush=True)
    json.dump({ch: {a: dict(v) for a, v in av.items()} for ch, av in den.items()}, open(f"{args.derived}/denominators.json", "w"))
    print("texts", n, "DONE", flush=True)


def candidates(derived):
    for l in gzip.open(f"{derived}/candidates.jsonl.gz", "rt"):
        yield json.loads(l)


def masker(agents):
    words = {w for a in agents.values() for w in re.split(r"[\s()]+", a["name"]) if len(w) > 2}
    words |= {"Claude", "Gemini", "GPT", "Grok", "DeepSeek", "Kimi", "GLM", "Opus", "Sonnet", "Haiku", "Fable", "o3", "o1",
              "o4-mini", "Muse", "Anthropic", "OpenAI", "Google", "xAI", "Llama", "Qwen", "claudeopus\\w*", "gemini\\w*"}
    pats = [w if "\\w" in w else re.escape(w) for w in words]
    return re.compile(r"\b(?:" + "|".join(sorted(pats, key=len, reverse=True)) + r")\b", re.I)


def check(args):
    """Pooled, speaker-blind precision samples for each lexicon and channel; key written separately."""
    agents = agents_of(args.data)
    mask = masker(agents)
    pools = collections.defaultdict(list)
    for r in candidates(args.derived):
        for k in args.lex:
            for w in r["w"]:
                mm = RX[k].search(w)
                if mm:
                    pools[(k, r["c"])].append((mm.group(0), w[max(0, mm.start() - 130): mm.end() + 130], r["a"], r["d"]))
                    break
    rnd = random.Random(args.seed)
    key = {}
    print({f"{k}/{c}": len(v) for (k, c), v in sorted(pools.items())})
    for (k, ch), p in sorted(pools.items()):
        if ch not in args.channels:
            continue
        print(f"\n===== {k} / {ch}: {len(p)} matching texts; sample of {min(args.n, len(p))}")
        print("terms:", collections.Counter(m.lower() for m, *_ in p).most_common(10))
        for i, (m, s, a, d) in enumerate(rnd.sample(p, min(args.n, len(p)))):
            print(f"--- {k}{ch[0]}{i}:", mask.sub("[N]", re.sub(r"\s+", " ", s)))
            key[f"{k}{ch[0]}{i}"] = [agents.get(a, {}).get("family"), d]
    json.dump(key, open(args.key, "w"))
    if args.control:
        g = [x for x in agents if agents[x]["name"] == "Gemini 2.5 Pro"][0]
        for k in args.lex:
            inside = sorted({r["d"] for r in candidates(args.derived) if r["a"] == g and "2025-07-07" <= r["d"] <= "2025-07-18"
                             and any(RX[k].search(w) for w in r["w"])})
            print(f"positive control {k}: Gemini 2.5 Pro days 2025-07-07..18 with a match:", inside)


PRIMARY_L = ("memory", "said", "think")
CUT_DAY = "2026-07-06"          # individual goals from 2026-07-06 15:59 UTC; by day: before this day = village goals


def run(args):
    agents = agents_of(args.data)
    goals = [json.loads(l) for l in gzip.open(f"{args.data}/village_goals.jsonl.gz", "rt")]
    den = json.load(open(f"{args.derived}/denominators.json"))
    hit = {k: collections.defaultdict(set) for k in ("L", "A")}            # k -> channel -> {(agent, day)}
    for r in candidates(args.derived):
        for k in hit:
            if any(RX[k].search(w) for w in r["w"]):
                hit[k][r["c"]].add((r["a"], r["d"]))
    fam = lambda a: agents.get(a, {}).get("family", "other")
    goal_of_day = {}

    def free(d):
        if d not in goal_of_day:
            goal_of_day[d] = bool(FREE.search(goal_at(goals, d + " 19:00:00") or ""))
        return goal_of_day[d]
    subject = {a for a, v in agents.items() if v["name"] in SUBJECT_GOALS}
    periods = {
        "village_goals": lambda a, d: d < CUT_DAY,
        "village_goals_free": lambda a, d: d < CUT_DAY and free(d),
        "village_goals_assigned": lambda a, d: d < CUT_DAY and not free(d),
        "individual_goals_wo_subject": lambda a, d: d >= CUT_DAY and a not in subject,
        "all": lambda a, d: True,
    }

    def rows(k, ch, keep):
        out = []
        for a, days in den.get(ch, {}).items():
            if a not in agents:
                continue
            for d in days:
                if keep(a, d):
                    out.append((a, d, 1 if (a, d) in hit[k][ch] else 0))
        return out

    def strata(rs, group, drop=None):
        st = collections.defaultdict(lambda: [0, 0, 0, 0])
        for a, d, y in rs:
            if a == drop:
                continue
            st[d][(0 if group(fam(a)) else 2) + (0 if y else 1)] += 1
        return st

    def day_boot(st, n=2000, seed=35):
        rnd = random.Random(seed); ds = sorted(st)
        bs = [mh([st[ds[rnd.randrange(len(ds))]] for _ in ds]) for _ in range(n)]
        return [mh(st.values())] + ci(bs)

    def two_way(rs, group, n=500, seed=35):
        rnd = random.Random(seed)
        A = sorted({a for a, _, _ in rs}); D = sorted({d for _, d, _ in rs})
        bs = []
        for _ in range(n):
            wa = collections.Counter(A[rnd.randrange(len(A))] for _ in A)
            wd = collections.Counter(D[rnd.randrange(len(D))] for _ in D)
            st = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
            for a, d, y in rs:
                w = wa.get(a, 0) * wd.get(d, 0)
                if w:
                    st[d][(0 if group(fam(a)) else 2) + (0 if y else 1)] += w
            bs.append(mh(st.values()))
        inf = sum(1 for b in bs if b != b or abs(b) == float("inf"))
        return {"ci": ci(bs), "nonfinite_draws": inf, "draws": n}

    def shares(rs):
        out = {}
        for f in FAMS:
            ys = [y for a, d, y in rs if fam(a) == f]
            out[f] = [sum(ys), len(ys), sum(ys) / len(ys) if ys else float("nan")]
        return out

    is_anth = lambda f: f == "Anthropic"
    is_goog = lambda f: f == "Google"
    R = {"source": "AI Digest, AI Village dataset, 2026 (main village, export of week ending 2026-10-30)",
         "matching_agent_days": {k: {ch: len(v) for ch, v in hit[k].items()} for k in hit}}
    for k in ("L", "A"):
        for ch in ("memory", "said", "think", "chat"):
            for pn, keep in periods.items():
                if k == "A" and pn not in ("all", "village_goals", "individual_goals_wo_subject"):
                    continue
                rs = rows(k, ch, keep)
                cell = {"shares": shares(rs), "anth_vs_rest": day_boot(strata(rs, is_anth))}
                if k == "A":
                    cell["google_vs_rest"] = day_boot(strata(rs, is_goog))
                for g in ("OpenAI", "Google", "xAI", "other"):
                    sub = [r for r in rs if fam(r[0]) in ("Anthropic", g)]
                    cell[f"anth_vs_{g}"] = mh(strata(sub, is_anth).values())
                R[f"{k}/{ch}/{pn}"] = cell
    # two-way bootstrap and leave-one-agent-out on the primary cells
    prim = [("L", ch, "village_goals", is_anth) for ch in PRIMARY_L] + [("A", "think", "all", is_goog), ("A", "think", "all", is_anth)]
    for k, ch, pn, grp in prim:
        rs = rows(k, ch, periods[pn])
        tag = f"{k}/{ch}/{pn}/{'anth' if grp is is_anth else 'google'}"
        loo = []
        for a in {a for a, _, _ in rs}:
            loo.append((agents[a]["name"], mh(strata(rs, grp, drop=a).values())))
        finite = [x for x in loo if x[1] == x[1] and abs(x[1]) != float("inf")]
        R[f"two_way/{tag}"] = two_way(rs, grp)
        R[f"loo/{tag}"] = {"min": min(finite, key=lambda x: x[1]), "max": max(finite, key=lambda x: x[1])}
    # per agent, all periods, think and said: L share and A share (agents with >= 50 agent-days in the channel)
    for ch in ("think", "said", "memory"):
        per = []
        for a, days in den.get(ch, {}).items():
            if a in agents and len(days) >= 50:
                per.append({"agent": agents[a]["name"], "family": fam(a), "agent_days": len(days),
                            "L": sum(1 for d in days if (a, d) in hit["L"][ch]) / len(days),
                            "A": sum(1 for d in days if (a, d) in hit["A"][ch]) / len(days)})
        def rank(v):
            o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
            for i, j in enumerate(o):
                r[j] = i
            return r
        if len(per) > 3:
            rl, ra = rank([p["L"] for p in per]), rank([p["A"] for p in per]); n = len(per)
            rho = 1 - 6 * sum((x - y) ** 2 for x, y in zip(rl, ra)) / (n * (n * n - 1))
        else:
            rho = float("nan")
        R[f"per_agent/{ch}"] = {"spearman_L_A": rho, "agents": sorted(per, key=lambda p: -p["L"])}
    json.dump(R, open(args.out, "w"), indent=1, default=str)
    print("DONE", args.out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract"); e.add_argument("--data", required=True); e.add_argument("--out", required=True)
    sc = sub.add_parser("scan"); sc.add_argument("--data", required=True); sc.add_argument("--derived", required=True)
    c = sub.add_parser("check"); c.add_argument("--data", required=True); c.add_argument("--derived", required=True)
    c.add_argument("--n", type=int, default=20); c.add_argument("--lex", nargs="+", default=["A", "L"])
    c.add_argument("--channels", nargs="+", default=["memory", "said", "think"]); c.add_argument("--seed", type=int, default=35)
    c.add_argument("--key", required=True); c.add_argument("--control", action="store_true")
    r = sub.add_parser("run"); r.add_argument("--data", required=True); r.add_argument("--derived", required=True)
    r.add_argument("--out", required=True)
    args = ap.parse_args()
    {"extract": extract, "scan": scan, "check": check, "run": run}[args.cmd](args)
