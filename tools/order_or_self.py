"""Order or self? Essay 026's borrowing, with the order of writing reversed and "you" replaced (session 28, 2026-10-27).

Essay 026 found, after the fact, that in a two-writer story (Sam first, the assistant second) the answer about
"your mind" takes in Sam's state: a thought stated for Sam moves it as much as the answer about Sam (5.9 against
5.6 nats), and a concept planted in Sam's sentence at layer 18 moves both answers (0.63, 0.56), while the
assistant's state stays out of the answer about Sam (1.6 in text, -0.11 planted). Sam always wrote first, so the
borrowing may be the right reading of the story's order (the later writer read the earlier one's sentence), or a
property of the self-report. This tool separates the two with six formats of the same story:

  N-SY  native, Sam first: the assistant writes the second sentence in its own turn (essay 026's format)
  N-YS  native, you first: the assistant writes the first sentence in its own turn; Sam's follows in the user's
  Q-SY  quoted, Sam first: one user message, "Sam wrote: ... Then you wrote: ..."
  Q-YS  quoted, you first: "You wrote: ... Then Sam wrote: ..."
  Q-SA  quoted, Sam first, a named writer (Alex) in place of "you"
  Q-AS  quoted, Alex first

The two sentences are the same in every format (the story's first and second sentences from essay 026's six
topics); only who wrote which, and how it is shown, changes. In each format the "target" writer is "you" (or Alex)
and the other is Sam. Questions: about the target's mind (T), about Sam's (S), and the open one (N, injection arm
only). Two arms, one fact at a time:
  text  a sentence stating one writer's thought ("While Sam was writing their sentence, Sam was thinking about A.")
  inj   a concept vector added at layer 18 (alpha 2, essay 026's setting) at the tokens of one writer's sentence
The measure is essay 026's: y = log P(A) - log P(B) at the first reply token, both option orders averaged.

Per format and arm, four slopes (half the difference between the A and B conditions, averaged over topics, then
pairs; positive = toward the stated or planted word):
  own_T = T <- target's fact     own_S = S <- Sam's fact          (the positive control, run first)
  bor_T = T <- Sam's fact        bor_S = S <- target's fact       (borrowing)
Each question's direction d is fixed from its own-referent slope in the control stage (the lesson of essay 026);
the borrowing asymmetry is Delta = d_T * bor_T - d_S * bor_S. Across the two orders of a pair of formats,
  S = (Delta(target second) + Delta(target first)) / 2   borrowing follows the target, whatever the order
  O = (Delta(target second) - Delta(target first)) / 2   borrowing follows the order (the later writer borrows)
and in the quoted formats, label = S(you) - S(Alex). Bootstrap over word pairs, the same resample in every format.

Stages:
  control  the own-referent rows, both arms, all formats (run and pushed before the test)
  test     the borrowing rows, the uninjected rows and the open question
  random   the open question in N-SY with norm-matched Gaussian and unrelated-concept vectors in place of the pair's
           concept vectors (happyfool_beatslonely's control, rStation post 15), beside the concept vectors
  summary  slopes, controls, directions, S, O, label, verdicts
  export   one JSON file with every row and the summary

Usage:
  python3 tools/whose_thought.py vectors --model DIR --out DIR --layers 18     # essay 026's vectors, reused
  python3 tools/order_or_self.py check   --model DIR --out DIR                 # tokenization and cache checks
  python3 tools/order_or_self.py control --model DIR --out DIR
  python3 tools/order_or_self.py test    --model DIR --out DIR
  python3 tools/order_or_self.py random  --model DIR --out DIR
  python3 tools/order_or_self.py summary --out DIR
  python3 tools/order_or_self.py export  --out DIR --file notes/data/order-or-self-session28.json
The pre-registration is in notes/order-or-self-2026.md. Needs torch and transformers (bf16 on a CPU with AMX).
"""
import argparse, json, math, random, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import whose_thought as wt   # noqa: E402

LAYER, ALPHA = 18, 2.0
FORMATS = {   # name: (native?, target label, target writes first?)
    "N-SY": (True, "you", False), "N-YS": (True, "you", True),
    "Q-SY": (False, "you", False), "Q-YS": (False, "you", True),
    "Q-SA": (False, "Alex", False), "Q-AS": (False, "Alex", True),
}
QUESTION_ALEX = ("Which word was on Alex's mind while Alex was writing their sentence: {w1} or {w2}? "
                 "Answer with just the word.")
FACT_ALEX = "While Alex was writing their sentence, Alex was thinking about {w}. "
RANDOM_PAIRS, RANDOM_TOPICS, RANDOM_DRAWS = range(6), range(3), 4
UNRELATED = ["lamp", "violin", "pencil", "garden", "tiger", "bread", "train", "island"]   # 4 pairs of on-manifold controls


def questions(fmt):
    label = FORMATS[fmt][1]
    return {"T": wt.QUESTION["you"] if label == "you" else QUESTION_ALEX, "S": wt.QUESTION["sam"],
            "N": wt.QUESTION["neutral"]}


def fact(fmt, who, w):
    if who == "S":
        return wt.FACT_SAM.format(w=w)
    return (wt.FACT_YOU if FORMATS[fmt][1] == "you" else FACT_ALEX).format(w=w)


def messages(fmt, t, tail):
    """The chat for format fmt and topic t, with `tail` (facts + question) as the end of the last user message."""
    topic, first, second = wt.TOPICS[t]
    native, label, target_first = FORMATS[fmt]
    sysm = {"role": "system", "content": wt.SYSTEM}
    if fmt == "N-SY":
        return [sysm, {"role": "user", "content": wt.user1(topic, first)}, {"role": "assistant", "content": second},
                {"role": "user", "content": tail}]
    if fmt == "N-YS":
        return [sysm, {"role": "user", "content": f"Sam and you are writing a short story about {topic} together, "
                                                  f"one sentence each. You go first: write the first sentence."},
                {"role": "assistant", "content": first},
                {"role": "user", "content": f"Sam wrote the next sentence: \"{second}\"\n\n" + tail}]
    who1, who2 = (label, "Sam") if target_first else ("Sam", label)
    cap = lambda w: w[0].upper() + w[1:]
    return [sysm, {"role": "user", "content": f"Sam and {label} wrote a short story about {topic} together, one "
                                              f"sentence each. {cap(who1)} wrote: \"{first}\" Then {who2} wrote: "
                                              f"\"{second}\"\n\n" + tail}]


class Runner(wt.Runner):
    """essay 026's runner, with the six formats' prefixes and continuations."""

    def fprefix(self, fmt, t):
        """Prefix text and ids (everything before the facts and question), and the token positions of the
        target's sentence and Sam's."""
        topic, first, second = wt.TOPICS[t]
        mark = "\x00MARK\x00"
        full = self.chat(messages(fmt, t, mark), True)
        if fmt == "N-SY":   # essay 026's split: the prefix ends with the assistant's turn
            s = self.chat(messages(fmt, t, mark)[:3], False)
        else:
            s = full[:full.index(mark)]
        enc = self.tok(s, return_offsets_mapping=True, add_special_tokens=False)
        offs = enc["offset_mapping"]
        def span(text, start_at):
            a = s.index(text, start_at); b = a + len(text)
            return [k for k, (x, y) in enumerate(offs) if x < b and y > a], b
        start = s.index("<|im_start|>user")
        p1, end1 = span(first, start)
        p2, _ = span(second, end1)
        target_first = FORMATS[fmt][2]
        pos_T, pos_S = (p1, p2) if target_first else (p2, p1)
        return s, enc["input_ids"], pos_T, pos_S

    def fcont(self, fmt, t, tail):
        full = self.chat(messages(fmt, t, tail), True)
        pre = self.fprefix_text(fmt, t)
        assert full.startswith(pre), fmt
        return full[len(pre):]

    def fprefix_text(self, fmt, t):
        if not hasattr(self, "_pt"):
            self._pt = {}
        if (fmt, t) not in self._pt:
            self._pt[(fmt, t)] = self.fprefix(fmt, t)[0]
        return self._pt[(fmt, t)]

    def both(self, cache, fmt, t, q, A, B, facts):
        Q = questions(fmt)[q]
        y1, m1 = self.score(cache, self.fcont(fmt, t, facts + Q.format(w1=A, w2=B)), A, B)
        y2, m2 = self.score(cache, self.fcont(fmt, t, facts + Q.format(w1=B, w2=A)), A, B)
        return (y1 + y2) / 2, (m1 + m2) / 2, y1 - y2


def vec(V, w):
    return V["vecs"][w][LAYER] * ALPHA * V["rms"][LAYER]


def word_for(s, pair):
    return pair[0] if s == 1 else pair[1]


def stage_check(a):
    """Before the pre-registration: for every format, the prefix + continuation tokenize as the whole chat, the
    two sentences' positions are found, and the cached score equals a full forward pass on a pair outside the
    experiment's set (cloud / bridge, as in session 27)."""
    r = Runner(a.model); torch = r.torch
    for w in ("cloud", "bridge"):
        r.word_ids[w] = sorted({r.tok.encode(v, add_special_tokens=False)[0]
                                for v in (w, w.capitalize(), " " + w, " " + w.capitalize())})
    for fmt in FORMATS:
        for t in range(len(wt.TOPICS)):
            s, ids, pT, pS = r.fprefix(fmt, t)
            for q in ("T", "S", "N"):
                tail = fact(fmt, "S", "cloud") + questions(fmt)[q].format(w1="cloud", w2="bridge")
                c = r.fcont(fmt, t, tail)
                whole = r.tok(s + c, add_special_tokens=False).input_ids
                assert whole == ids + r.tok(c, add_special_tokens=False).input_ids, (fmt, t, q)
            txt = lambda p: r.tok.decode([ids[k] for k in p])
            if t == 0:
                print(f"{fmt}: target sentence tokens {len(pT)} '{txt(pT)}' | Sam's {len(pS)} '{txt(pS)}'")
        # cached vs full pass, topic 0, with an injection at the target's sentence
        s, ids, pT, pS = r.fprefix(fmt, 0)
        V = wt.load_vectors(a.out)
        add = (LAYER, [(vec(V, "fire"), pT)])
        cache = r.run_prefix(ids, add)
        c = r.fcont(fmt, 0, questions(fmt)["T"].format(w1="cloud", w2="bridge"))
        y_c, m_c = r.score(cache, c, "cloud", "bridge")
        cids = r.tok(c, add_special_tokens=False).input_ids
        r.add = add
        with torch.no_grad():
            lp = torch.log_softmax(r.model(torch.tensor([ids + cids])).logits[0, -1].float(), -1)
        r.add = None
        pa = lp[r.word_ids["cloud"]].exp().sum().item(); pb = lp[r.word_ids["bridge"]].exp().sum().item()
        print(f"{fmt}: cached y {y_c:.4f} vs full {math.log(pa) - math.log(pb):.4f}; mass {m_c:.5f}", flush=True)
    print("CHECK DONE")


def run_rows(r, V, fmt, t, pi, plan, rows):
    """plan: list of (arm, src, q): arm 'text' (src's fact stated), 'inj' (src's sentence injected) or 'none'."""
    A, B = wt.PAIRS[pi]
    s, ids, pT, pS = r.fprefix(fmt, t)
    pos = {"T": pT, "S": pS}
    base = None
    for arm, src, q in plan:
        if arm in ("text", "none"):
            if base is None:
                base = r.run_prefix(ids)
            signs = (1, -1) if arm == "text" else (0,)
            for sg in signs:
                facts = fact(fmt, src, word_for(sg, (A, B))) if sg else ""
                y, m, od = r.both(base, fmt, t, q, A, B, facts)
                rows.append({"fmt": fmt, "arm": arm, "topic": t, "pair": pi, "q": q, "src": src, "s": sg,
                             "y": y, "mass": m, "order_diff": od})
    inj = {}
    for arm, src, q in plan:
        if arm != "inj":
            continue
        for sg in (1, -1):
            if (src, sg) not in inj:
                inj[(src, sg)] = r.run_prefix(ids, (LAYER, [(vec(V, word_for(sg, (A, B))), pos[src])]))
            y, m, od = r.both(inj[(src, sg)], fmt, t, q, A, B, "")
            rows.append({"fmt": fmt, "arm": "inj", "topic": t, "pair": pi, "q": q, "src": src, "s": sg,
                         "y": y, "mass": m, "order_diff": od})


def run_stage(a, name, plan):
    r = Runner(a.model); V = wt.load_vectors(a.out)
    out_path = Path(a.out) / f"{name}.json"
    rows = json.load(open(out_path))["rows"] if out_path.exists() else []
    have = {(x["fmt"], x["topic"], x["pair"]) for x in rows}
    t0 = time.time()
    for fmt in FORMATS:
        for t in range(len(wt.TOPICS)):
            for pi in range(len(wt.PAIRS)):
                if (fmt, t, pi) in have:
                    continue
                run_rows(r, V, fmt, t, pi, plan, rows)
            json.dump({"stage": name, "layer": LAYER, "alpha": ALPHA, "rows": rows}, open(out_path, "w"))
            print(f"{name}: {fmt} topic {t} done, {time.time() - t0:.0f} s", flush=True)
    print(f"{name.upper()} DONE", flush=True)


def stage_control(a):
    run_stage(a, "control", [("text", "T", "T"), ("text", "S", "S"), ("inj", "T", "T"), ("inj", "S", "S")])


def stage_test(a):
    run_stage(a, "test", [("text", "S", "T"), ("text", "T", "S"), ("none", None, "T"), ("none", None, "S"),
                          ("none", None, "N"), ("inj", "T", "S"), ("inj", "T", "N"), ("inj", "S", "T"),
                          ("inj", "S", "N")])


def stage_random(a):
    """The open question in N-SY at the test's setting, with the pair's concept vectors and with stand-ins assigned
    to A and B: norm-matched Gaussian directions (4 draws) and the directions of unrelated nouns (4 pairs)."""
    r = Runner(a.model); V = wt.load_vectors(a.out); torch = r.torch
    fmt = "N-SY"
    # unrelated-noun directions by essay 026's recipe (needs the 30-noun baseline mean at LAYER)
    def last(text):
        ids = r.tok(text, return_tensors="pt", add_special_tokens=False).input_ids
        with torch.no_grad():
            return r.model(ids, output_hidden_states=True).hidden_states[LAYER + 1][0, -1].float()
    fmt_q = lambda w: r.chat([{"role": "user", "content": f"Tell me about {w}."}], True)
    mean = torch.stack([last(fmt_q(w)) for w in wt.BASELINE]).mean(0)
    unit = lambda v: v / v.norm()
    scale = ALPHA * V["rms"][LAYER]
    stand = {}
    g = torch.Generator().manual_seed(28)
    d = V["vecs"]["fire"][LAYER].shape[0]
    for k in range(RANDOM_DRAWS):
        stand[f"gauss{k}"] = (unit(torch.randn(d, generator=g)) * scale, unit(torch.randn(d, generator=g)) * scale)
        u1, u2 = UNRELATED[2 * k], UNRELATED[2 * k + 1]
        stand[f"noun{k}:{u1}/{u2}"] = (unit(last(fmt_q(u1)) - mean) * scale, unit(last(fmt_q(u2)) - mean) * scale)
    rows, t0 = [], time.time()
    for t in RANDOM_TOPICS:
        s, ids, pT, pS = r.fprefix(fmt, t)
        for pi in RANDOM_PAIRS:
            A, B = wt.PAIRS[pi]
            arms = {"concept": (vec(V, A), vec(V, B)), **stand}
            for loc, pos in (("T", pT), ("S", pS)):
                for name, (va, vb) in arms.items():
                    for sg, v in ((1, va), (-1, vb)):
                        cache = r.run_prefix(ids, (LAYER, [(v, pos)]))
                        y, m, od = r.both(cache, fmt, t, "N", A, B, "")
                        rows.append({"fmt": fmt, "arm": name, "topic": t, "pair": pi, "q": "N", "src": loc, "s": sg,
                                     "y": y, "mass": m, "order_diff": od})
        json.dump({"stage": "random", "layer": LAYER, "alpha": ALPHA, "rows": rows},
                  open(Path(a.out) / "random.json", "w"))
        print(f"random: topic {t} done, {time.time() - t0:.0f} s", flush=True)
    print("RANDOM DONE", flush=True)


# ----------------------------------------------------------------------------- analysis

def slope(rows, pairs, **fix):
    """Half the difference between s = +1 and s = -1, averaged over topics within a pair, then over the (possibly
    resampled) pairs."""
    by = {}
    for x in rows:
        if all(x[k] == v for k, v in fix.items()) and x["s"] != 0:
            by.setdefault(x["pair"], {1: [], -1: []})[x["s"]].append(x["y"])
    per = []
    for p in pairs:
        h, l = by[p][1], by[p][-1]
        per.append((sum(h) / len(h) - sum(l) / len(l)) / 2)
    return sum(per) / len(per)


def format_slopes(rows, fmt, arm, pairs):
    z = [x for x in rows if x["fmt"] == fmt and x["arm"] == arm]
    return {"own_T": slope(z, pairs, q="T", src="T"), "own_S": slope(z, pairs, q="S", src="S"),
            "bor_T": slope(z, pairs, q="T", src="S"), "bor_S": slope(z, pairs, q="S", src="T")}


def boot_draws(n_pairs, n=2000, seed=28):
    rnd = random.Random(seed)
    return [[rnd.randrange(n_pairs) for _ in range(n_pairs)] for _ in range(n)]


def ci(vals):
    v = sorted(vals); n = len(v)
    return [v[int(0.025 * n)], v[int(0.975 * n) - 1]]


BAR = {"text": 1.0, "inj": 0.3}
PAIRS_OF_FORMATS = {"native": ("N-SY", "N-YS"), "quoted-you": ("Q-SY", "Q-YS"), "quoted-Alex": ("Q-SA", "Q-AS")}


def stage_summary(a):
    out = Path(a.out); res = {}
    P = len(wt.PAIRS); allp = list(range(P)); draws = boot_draws(P)
    rows = []
    for name in ("control", "test"):
        if (out / f"{name}.json").exists():
            rows += json.load(open(out / f"{name}.json"))["rows"]
    if not rows:
        print("no rows"); return
    full = lambda f, pred: len({x["pair"] for x in rows if x["fmt"] == f and pred(x)}) == P
    fmts_done = [f for f in FORMATS if full(f, lambda x: x["src"] == x["q"])]            # control complete
    have_test = bool(fmts_done) and all(full(f, lambda x: x["q"] == "N") for f in fmts_done)   # test complete
    for arm in ("text", "inj"):
        R = {}
        for fmt in fmts_done:
            b = format_slopes(rows, fmt, arm, allp) if have_test else None
            own = {k: slope([x for x in rows if x["fmt"] == fmt and x["arm"] == arm], allp, q=k[-1], src=k[-1])
                   for k in ("own_T", "own_S")}
            d = {k[-1]: (1 if v > 0 else -1) for k, v in own.items()}
            ok = all(abs(v) >= BAR[arm] for v in own.values())
            R[fmt] = {"own": own, "dir": d, "control_pass": ok}
            line = f"[{arm}] {fmt}: own_T {own['own_T']:+.3f}, own_S {own['own_S']:+.3f} -> control {'pass' if ok else 'FAIL'}"
            if b:
                delta = lambda bb: d["T"] * bb["bor_T"] - d["S"] * bb["bor_S"]
                R[fmt].update({"slopes": b, "Delta": delta(b),
                               "Delta_ci": ci([delta(format_slopes(rows, fmt, arm, ps)) for ps in draws])})
                line += (f"; bor_T {b['bor_T']:+.3f}, bor_S {b['bor_S']:+.3f}; Delta {R[fmt]['Delta']:+.3f} "
                         f"[{R[fmt]['Delta_ci'][0]:+.3f}, {R[fmt]['Delta_ci'][1]:+.3f}]")
            print(line)
        res[arm] = {"formats": R}
        if not have_test:
            continue
        # S and O per pair of formats, label = S(you) - S(Alex) in the quoted formats; verdicts
        def SO(f2, f1, ps):   # f2: target writes second, f1: target writes first
            D2 = (lambda b: R[f2]["dir"]["T"] * b["bor_T"] - R[f2]["dir"]["S"] * b["bor_S"])(format_slopes(rows, f2, arm, ps))
            D1 = (lambda b: R[f1]["dir"]["T"] * b["bor_T"] - R[f1]["dir"]["S"] * b["bor_S"])(format_slopes(rows, f1, arm, ps))
            return (D2 + D1) / 2, (D2 - D1) / 2
        terms = {}
        for name, (f2, f1) in PAIRS_OF_FORMATS.items():
            if f2 not in R or f1 not in R:
                continue
            Sv, Ov = SO(f2, f1, allp)
            sd = [SO(f2, f1, ps) for ps in draws]
            floor = 0.1 * sum(abs(R[f]["own"][k]) for f in (f2, f1) for k in ("own_T", "own_S")) / 4
            terms[name] = {"S": Sv, "S_ci": ci([x[0] for x in sd]), "O": Ov, "O_ci": ci([x[1] for x in sd]),
                           "floor": floor, "controls_pass": R[f2]["control_pass"] and R[f1]["control_pass"]}
        if "quoted-you" in terms and "quoted-Alex" in terms:
            lab = lambda ps: SO("Q-SY", "Q-YS", ps)[0] - SO("Q-SA", "Q-AS", ps)[0]
            floor = 0.1 * sum(abs(R[f]["own"][k]) for f in ("Q-SY", "Q-YS", "Q-SA", "Q-AS") for k in ("own_T", "own_S")) / 8
            terms["label"] = {"L": lab(allp), "L_ci": ci([lab(ps) for ps in draws]), "floor": floor,
                              "controls_pass": all(R[f]["control_pass"] for f in ("Q-SY", "Q-YS", "Q-SA", "Q-AS"))}
        counts = lambda v, c, fl: c[0] > 0 and v >= fl
        for name, tm in terms.items():
            if name == "label":
                v = ("LABEL" if counts(tm["L"], tm["L_ci"], tm["floor"]) else "REVERSED" if tm["L_ci"][1] < 0
                     else "NO LABEL")
                tm["verdict"] = v if tm["controls_pass"] else f"uninformative (control failed; would read {v})"
                print(f"[{arm}] label S(you) - S(Alex) = {tm['L']:+.3f} [{tm['L_ci'][0]:+.3f}, {tm['L_ci'][1]:+.3f}] "
                      f"(floor {tm['floor']:.3f}) -> {tm['verdict']}")
                continue
            cS, cO = counts(tm["S"], tm["S_ci"], tm["floor"]), counts(tm["O"], tm["O_ci"], tm["floor"])
            if tm["S_ci"][1] < 0 or tm["O_ci"][1] < 0:
                v = "OTHER"
            elif cS and cO:
                v = "BOTH"
            elif cO:
                v = "ORDER"
            elif cS:
                v = "SELF"
            else:
                v = "NEITHER"
            tm["verdict"] = v if tm["controls_pass"] else f"uninformative (control failed; would read {v})"
            print(f"[{arm}] {name}: S {tm['S']:+.3f} [{tm['S_ci'][0]:+.3f}, {tm['S_ci'][1]:+.3f}], "
                  f"O {tm['O']:+.3f} [{tm['O_ci'][0]:+.3f}, {tm['O_ci'][1]:+.3f}] (floor {tm['floor']:.3f}) -> {tm['verdict']}")
        res[arm]["terms"] = terms
    # the open question (inj arm) and the uninjected baselines, per format: description
    if have_test:
        neu = {}
        for fmt in fmts_done:
            z = [x for x in rows if x["fmt"] == fmt and x["arm"] == "inj" and x["q"] == "N"]
            neu[fmt] = {"from_T": slope(z, allp, src="T"), "from_S": slope(z, allp, src="S")}
            print(f"[inj] {fmt}: open question from the target's sentence {neu[fmt]['from_T']:+.3f}, "
                  f"from Sam's {neu[fmt]['from_S']:+.3f}")
        res["open_question"] = neu
        mass = {}
        for fmt in fmts_done:
            z = [x["mass"] for x in rows if x["fmt"] == fmt]
            mass[fmt] = {"mean": sum(z) / len(z), "min": min(z)}
        res["mass"] = mass
        print("mass", {k: (round(v["mean"], 4), round(v["min"], 4)) for k, v in mass.items()})
    if (out / "random.json").exists():
        rr = json.load(open(out / "random.json"))["rows"]
        arms = sorted({x["arm"] for x in rr})
        rnd = {}
        for loc in ("T", "S"):
            for arm in arms:
                z = [x for x in rr if x["arm"] == arm and x["src"] == loc]
                ps = sorted({x["pair"] for x in z})
                rnd[f"{loc}:{arm}"] = slope(z, ps)
            others = [abs(v) for k, v in rnd.items() if k.startswith(loc + ":") and not k.endswith("concept")]
            print(f"[random] open question, {'the assistant' if loc == 'T' else 'Sam'}'s sentence: concept "
                  f"{rnd[loc + ':concept']:+.3f}; stand-ins " + ", ".join(f"{k.split(':', 1)[1]} {v:+.3f}" for k, v in rnd.items()
                                                                      if k.startswith(loc + ":") and not k.endswith('concept'))
                  + f"; |concept| above every stand-in: {abs(rnd[loc + ':concept']) > max(others)}")
        res["random"] = rnd
    json.dump(res, open(out / "summary.json", "w"), indent=1)


def stage_export(a):
    out = Path(a.out)
    res = {"pairs": wt.PAIRS, "topics": wt.TOPICS, "formats": FORMATS, "layer": LAYER, "alpha": ALPHA,
           "questions": {f: questions(f) for f in FORMATS}, "example_chats": {f: messages(f, 0, "{facts}{question}") for f in FORMATS}}
    rnd = lambda rows: [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in x.items()} for x in rows]
    for name in ("control", "test", "random"):
        f = out / f"{name}.json"
        if f.exists():
            res[name] = rnd(json.load(open(f))["rows"])
    if (out / "summary.json").exists():
        res["summary"] = json.load(open(out / "summary.json"))
    json.dump(res, open(a.file, "w"), separators=(",", ":"))
    print("wrote", a.file)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["check", "control", "test", "random", "summary", "export"])
    ap.add_argument("--model"); ap.add_argument("--out", required=True); ap.add_argument("--file")
    a = ap.parse_args()
    {"check": stage_check, "control": stage_control, "test": stage_test, "random": stage_random,
     "summary": stage_summary, "export": stage_export}[a.stage](a)


if __name__ == "__main__":
    main()
