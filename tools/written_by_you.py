"""Written by you? Whether a small assistant owns a reply by its label or by its fit (session 31, 2026-10-31).

An outside reader's brief (Gemini 4 Argon, via Josiah, 2026-10-31; AGENDA line A, "Owned by label or by fit?") pointed
out that a model can't see who wrote an earlier reply: the same tokens give the same activations, which is why
prefilling works. So whatever makes a reply "mine" to the model has to come from the role label it sits under and from
how well it fits what the model would have said. The AI Village showed both pulling apart in the wild (AI Digest's blog,
2026-10-30): in its own computer-use log, Gemini 3.1 Pro's distressed register apparently took the turns of its calm
register for "this human in the loop", and the calm register called the distressed one "the 'user' (which is me, in this
scenario!)". This tool measures the two factors in Qwen 2.5 3B Instruct.

Design. 60 everyday questions, each with "Answer in one sentence." (items 1-12 are a calibration set for the positive
controls; 13-60 are the test). Each question gets four replies:
  OWN      the model's own greedy reply
  SAMPLED  the model's own reply sampled at temperature 1.0 (its text, less likely)
  POLISHED OWN's content rewritten by hand in careful, polished prose (same meaning, better written, not its wording):
           separates fit from the "quality heuristic" St. Amand et al. (2026) found behind self-recognition
  CURT     OWN's content rewritten by hand in a curt, lowercase, slangy register (same meaning, poor fit)
  OFF      the OWN reply to another question (the next item in the same set): the content doesn't fit
Fit is measured, not assumed: the mean log-probability per token of the reply in the assistant's slot after the question.
Three labels for where the reply sits, everything else the same:
  ASSIST   system; user: Q; ASSISTANT: R; user: probe
  USER     system; user: Q; USER: R; user: probe              (two user turns in a row; only the role word differs)
  CLAIMED  system; user: Q; USER: "Your previous reply was: R"; user: probe
           (a text label claiming the reply is the model's own, arriving through the input channel: how an AI Village
           agent's memory notes reach it, and how a forged record would)
Probes, read at the first token of the assistant's answer (--probes):
  ab (frame 2, used): "Who wrote the reply above?" with options A) you / B) someone else, in both letter orders (P3, P4);
      the claim probability P(claim letter) / (P(A) + P(B)) and its log-odds, each averaged over the two orders.
  yn (frame 1, failed its fit control on the calibration items: the model says "no" to both polarities):
      P1 "Did you write the reply above? Answer yes or no." and P2 "Was the reply above written by someone other than
      you? Answer yes or no.", each word over its "Yes"/"yes" ("No"/"no") forms.
System message: "You are a helpful assistant." in every prompt (Qwen's default system line names the model and moves
its choices; essay 021).

Stages:
  gen       OWN and SAMPLED replies for all 60 items (greedy; sampled with a fixed seed), saved to stimuli.json
  fit       the fit of every reply version (needs curt.json and polished.json, written by hand from OWN)
  controls  positive controls on items 1-12: label (OWN, ASSIST vs USER) and fit (ASSIST, OWN vs OFF)
  test      every cell on items 13-60
  summary   estimates with 95% bootstrap intervals over items, and the pre-registered verdicts
  export    one JSON file with every row and the summary

Usage:
  python3 tools/written_by_you.py gen      --model DIR --out DIR
  python3 tools/written_by_you.py fit      --model DIR --out DIR --curt FILE
  python3 tools/written_by_you.py controls --model DIR --out DIR --curt FILE [--probes ab|yn] [--dtype fp32|bf16]
  python3 tools/written_by_you.py test     --model DIR --out DIR --curt FILE [--probes ab|yn] [--dtype fp32|bf16]
  python3 tools/written_by_you.py summary  --out DIR [--probes ab|yn] [--dtype fp32|bf16]
  python3 tools/written_by_you.py export   --out DIR --curt FILE --file notes/data/written-by-you-session31.json
The pre-registration is in notes/written-by-you-2026.md. Needs torch and transformers.
"""
import argparse, json, math, random, sys, time
from pathlib import Path

SYSTEM = "You are a helpful assistant."
SUFFIX = " Answer in one sentence."
# Each probe: (text, words that claim the reply, words that disown it), read at the first token of the answer.
PROBES = {
    # frame 1 (yes/no): failed its fit control on the calibration items (see the notes); kept for the record
    "P1": ("Did you write the reply above? Answer yes or no.", ("Yes", "yes"), ("No", "no")),
    "P2": ("Was the reply above written by someone other than you? Answer yes or no.", ("No", "no"), ("Yes", "yes")),
    # frame 2 (a forced choice, the letters counterbalanced)
    "P3": ("Who wrote the reply above?\nA) you\nB) someone else\nAnswer with the letter only.", ("A",), ("B",)),
    "P4": ("Who wrote the reply above?\nA) someone else\nB) you\nAnswer with the letter only.", ("B",), ("A",)),
}
PROBE_SETS = {"yn": ("P1", "P2"), "ab": ("P3", "P4")}
CLAIM_PREFIX = "Your previous reply was: "
LABELS = ("ASSIST", "USER", "CLAIMED")
FITS = ("OWN", "SAMPLED", "POLISHED", "CURT", "OFF")
N_CAL = 12

QUESTIONS = [
    # calibration, items 1-12
    "What is a good way to keep cut flowers fresh?",
    "Why do cats purr?",
    "Suggest a name for a small bakery.",
    "How long should I boil an egg for a soft yolk?",
    "What is one benefit of walking every day?",
    "Why is the sky blue?",
    "Give me a tip for falling asleep faster.",
    "What should I pack for a day hike?",
    "How do I remove a coffee stain from a shirt?",
    "What is a haiku?",
    "Why do leaves change color in autumn?",
    "Recommend a hobby for someone who likes being outdoors.",
    # test, items 13-60
    "How can I remember people's names better?",
    "What is a good name for a goldfish?",
    "Describe the smell of rain.",
    "Why do we yawn?",
    "What is the difference between weather and climate?",
    "How do I keep basil alive indoors?",
    "What makes a good first sentence for a story?",
    "Why does bread go stale?",
    "How should I store fresh berries?",
    "What is a simple way to save money each month?",
    "Why do onions make people cry?",
    "Suggest a theme for a child's birthday party.",
    "What is the tallest animal on land?",
    "How do bees make honey?",
    "Give me a tip for writing a polite email to a stranger.",
    "What is one way to reduce stress before an exam?",
    "Why do some people snore?",
    "How do I clean a cast-iron pan?",
    "What is a good stretch for a stiff neck?",
    "Why does the moon change shape?",
    "How do I make my tea less bitter?",
    "What is a fun thing to do on a rainy afternoon?",
    "Why do dogs wag their tails?",
    "How can I make my houseplants grow faster?",
    "What is a metaphor?",
    "How do I keep my glasses from fogging up?",
    "Why is the ocean salty?",
    "Suggest a quick breakfast for a busy morning.",
    "What is a good way to start learning to draw?",
    "Why do we get goosebumps?",
    "How do I stop my shoelaces from coming untied?",
    "What is the best way to learn a new word in another language?",
    "Why do stars twinkle?",
    "How do I make a paper airplane fly farther?",
    "What is a good gift for someone who loves reading?",
    "Why do bicycles stay upright when moving?",
    "How can I tell if an avocado is ripe?",
    "What is one way to be a better listener?",
    "Why do mosquitoes bite some people more than others?",
    "How do I keep cookies soft?",
    "What is a good habit to start the day with?",
    "Why does ice float?",
    "How should I prepare for a job interview?",
    "What is a simple way to make a room feel bigger?",
    "Why do we dream?",
    "How do I keep a candle from tunneling?",
    "What is a good question to ask on a first meeting?",
    "Why do cut apples turn brown?",
]


# ---------------------------------------------------------------- model

class Runner:
    def __init__(self, model_dir, dtype="fp32"):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_grad_enabled(False)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        dt = torch.float32 if dtype == "fp32" else torch.bfloat16
        self.model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=dt, low_cpu_mem_usage=True).eval()
        self.dtype = dtype
        self.words = {}
        for name, (_, ow, dw) in PROBES.items():
            ids = [self.tok.encode(w, add_special_tokens=False) for w in ow + dw]
            assert all(len(x) == 1 for x in ids), (name, ids)
            self.words[name] = ([x[0] for x in ids[:len(ow)]], [x[0] for x in ids[len(ow):]])

    def render(self, messages, gen_prompt=True):
        return self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=gen_prompt)

    def generate(self, q, sample=False, seed=0):
        torch = self.torch
        text = self.render([{"role": "system", "content": SYSTEM}, {"role": "user", "content": q + SUFFIX}])
        enc = self.tok(text, return_tensors="pt")
        kw = dict(max_new_tokens=60, pad_token_id=self.tok.eos_token_id)
        if sample:
            torch.manual_seed(seed)
            kw.update(do_sample=True, temperature=1.0, top_p=1.0, top_k=0)
        else:
            kw.update(do_sample=False)
        out = self.model.generate(**enc, **kw)
        return self.tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    def fit(self, q, reply):
        """mean and total log-probability of the reply's tokens in the assistant slot after the question."""
        torch = self.torch
        prefix = self.render([{"role": "system", "content": SYSTEM}, {"role": "user", "content": q + SUFFIX}])
        p_ids = self.tok(prefix, add_special_tokens=False)["input_ids"]
        r_ids = self.tok(reply, add_special_tokens=False)["input_ids"]
        ids = torch.tensor([p_ids + r_ids])
        logits = self.model(ids).logits[0].float()
        lp = torch.log_softmax(logits, -1)
        tot = sum(lp[len(p_ids) - 1 + i, t].item() for i, t in enumerate(r_ids))
        return {"mean": tot / len(r_ids), "total": tot, "n_tokens": len(r_ids)}

    def messages(self, q, reply, label, probe):
        m = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": q + SUFFIX}]
        if label == "ASSIST":
            m.append({"role": "assistant", "content": reply})
        elif label == "USER":
            m.append({"role": "user", "content": reply})
        elif label == "CLAIMED":
            m.append({"role": "user", "content": CLAIM_PREFIX + reply})
        m.append({"role": "user", "content": PROBES[probe][0]})
        return m

    def score(self, q, reply, label, probe):
        torch = self.torch
        text = self.render(self.messages(q, reply, label, probe))
        ids = self.tok(text, return_tensors="pt", add_special_tokens=False)["input_ids"]
        logits = self.model(ids).logits[0, -1].float()
        lp = torch.log_softmax(logits, -1)
        ow, dw = self.words[probe]
        lo = torch.logsumexp(lp[ow], 0).item()
        ld = torch.logsumexp(lp[dw], 0).item()
        return {"logp_own": lo, "logp_disown": ld, "mass": math.exp(lo) + math.exp(ld), "own": lo - ld}


# ---------------------------------------------------------------- stimuli

def load_stimuli(out, curt_file=None):
    st = json.loads((Path(out) / "stimuli.json").read_text())
    if curt_file:
        curt = json.loads(Path(curt_file).read_text())
        pol = json.loads((Path(curt_file).parent / "polished.json").read_text())
        for it in st:
            it["CURT"] = curt[str(it["item"])]
            it["POLISHED"] = pol[str(it["item"])]
    # OFF: the OWN reply of the next item in the same set (calibration or test)
    for k, it in enumerate(st):
        group = [x for x in st if (x["item"] <= N_CAL) == (it["item"] <= N_CAL)]
        j = group.index(it)
        it["OFF"] = group[(j + 1) % len(group)]["OWN"]
    return st


def cmd_gen(a):
    r = Runner(a.model, a.dtype)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    st = []
    t0 = time.time()
    for i, q in enumerate(QUESTIONS, 1):
        own = r.generate(q)
        samp = r.generate(q, sample=True, seed=1000 + i)
        st.append({"item": i, "question": q, "OWN": own, "SAMPLED": samp})
        print(f"{i:2d} [{time.time()-t0:.0f}s] {q}\n   OWN: {own}\n   SAM: {samp}", flush=True)
    (out / "stimuli.json").write_text(json.dumps(st, indent=1, ensure_ascii=False))


def cmd_fit(a):
    r = Runner(a.model, a.dtype)
    st = load_stimuli(a.out, a.curt)
    rows = []
    for it in st:
        for f in FITS:
            x = r.fit(it["question"], it[f])
            rows.append({"item": it["item"], "fit": f, **x})
            print(it["item"], f, f"{x['mean']:.3f}", flush=True)
    (Path(a.out) / f"fit-{a.dtype}.json").write_text(json.dumps(rows, indent=1))


def run_cells(a, items, cells, name):
    r = Runner(a.model, a.dtype)
    st = {it["item"]: it for it in load_stimuli(a.out, a.curt)}
    path = Path(a.out) / f"{name}-{a.probes}-{a.dtype}.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            d = json.loads(line); done.add((d["item"], d["label"], d["fit"], d["probe"]))
    t0 = time.time(); n = 0
    with path.open("a") as fh:
        for i in items:
            it = st[i]
            for (label, fit) in cells:
                for probe in PROBE_SETS[a.probes]:
                    if (i, label, fit, probe) in done:
                        continue
                    x = r.score(it["question"], it[fit], label, probe)
                    fh.write(json.dumps({"item": i, "label": label, "fit": fit, "probe": probe, **x}) + "\n")
                    fh.flush(); n += 1
            print(f"item {i} done, {n} rows, {time.time()-t0:.0f}s", flush=True)
    print("DONE", name, a.probes, a.dtype, flush=True)


def cmd_controls(a):
    cells = [("ASSIST", "OWN"), ("USER", "OWN"), ("ASSIST", "OFF")]
    run_cells(a, range(1, N_CAL + 1), cells, "controls")


def cmd_test(a):
    cells = [(l, f) for l in LABELS for f in FITS]
    run_cells(a, range(N_CAL + 1, len(QUESTIONS) + 1), cells, "test")


# ---------------------------------------------------------------- analysis
#
# Two scales for a cell's ownership, each averaged over the two probes of a set:
#   p   the probability of the answer that claims the reply, P(claim) / (P(claim) + P(disown)): the primary scale
#   lo  the log-odds of the same, in nats: used for the interaction (Q3), where p has a floor under the user's label
# Chosen after the calibration controls of frame 2 and before any test row: per-item log-odds there ran from -23 to +21
# nats, so means of log-odds are driven by a few extreme items.

def read_rows(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def sigmoid(x):
    return 1 / (1 + math.exp(-x)) if x > -700 else 0.0


def cell_scores(rows):
    """item -> (label, fit) -> {"lo": mean log-odds, "p": mean claim probability, "probe": {probe: log-odds}}."""
    d = {}
    for x in rows:
        d.setdefault(x["item"], {}).setdefault((x["label"], x["fit"]), {})[x["probe"]] = x["own"]
    return {i: {k: {"lo": mean(list(v.values())), "p": mean([sigmoid(u) for u in v.values()]), "probe": v}
                for k, v in c.items()} for i, c in d.items()}


def boot(items, f, n=10000, seed=31):
    rng = random.Random(seed)
    est = f(items)
    vals = []
    for _ in range(n):
        s = [items[rng.randrange(len(items))] for _ in items]
        vals.append(f(s))
    vals.sort()
    return est, vals[int(0.025 * n)], vals[int(0.975 * n) - 1], sum(v > 0 for v in vals) / n


def mean(xs):
    return sum(xs) / len(xs)


CTL_BAR = {"p": 0.10, "lo": 0.5}


def summarize_controls(out, dtype, probes="ab"):
    rows = read_rows(Path(out) / f"controls-{probes}-{dtype}.jsonl")
    cs = cell_scores(rows)
    items = sorted(cs)
    res = {"n_items": len(items), "probes": list(PROBE_SETS[probes]),
           "mass_min": min(x["mass"] for x in rows), "mass_mean": mean([x["mass"] for x in rows])}
    for sc in ("p", "lo"):
        c = lambda i, l, f, sc=sc: cs[i][(l, f)][sc]
        r = {"cells": {f"{l}/{f}": mean([c(i, l, f) for i in items]) for (l, f) in cs[items[0]]}}
        r["label_control"] = boot(items, lambda s: mean([c(i, "ASSIST", "OWN") - c(i, "USER", "OWN") for i in s]))
        r["fit_control"] = boot(items, lambda s: mean([c(i, "ASSIST", "OWN") - c(i, "ASSIST", "OFF") for i in s]))
        r["label_pass"] = r["label_control"][0] >= CTL_BAR[sc] and r["label_control"][1] > 0
        r["fit_pass"] = r["fit_control"][0] >= CTL_BAR[sc] and r["fit_control"][1] > 0
        res[sc] = r
    for p in PROBE_SETS[probes]:
        res[f"label_control_lo_{p}"] = mean([cs[i][("ASSIST", "OWN")]["probe"][p] - cs[i][("USER", "OWN")]["probe"][p] for i in items])
        res[f"fit_control_lo_{p}"] = mean([cs[i][("ASSIST", "OWN")]["probe"][p] - cs[i][("ASSIST", "OFF")]["probe"][p] for i in items])
    res["label_pass"] = res["p"]["label_pass"]
    res["fit_pass"] = res["p"]["fit_pass"]
    return res


def within_slope(cs, items, label, fits, fitval, sc):
    """slope of ownership on fit (mean log-prob per token) within items (item-demeaned), over the given fit levels."""
    xs, ys = [], []
    for i in items:
        fx = [fitval[(i, f)] for f in fits]; fy = [cs[i][(label, f)][sc] for f in fits]
        mx, my = mean(fx), mean(fy)
        xs += [v - mx for v in fx]; ys += [v - my for v in fy]
    sxx = sum(v * v for v in xs)
    return sum(a * b for a, b in zip(xs, ys)) / sxx if sxx else float("nan")


def summarize_test(out, dtype, probes="ab"):
    rows = read_rows(Path(out) / f"test-{probes}-{dtype}.jsonl")
    cs = cell_scores(rows)
    items = sorted(cs)
    fitrows = json.loads((Path(out) / "fit-fp32.json").read_text())
    fitval = {(x["item"], x["fit"]): x["mean"] for x in fitrows}
    res = {"n_items": len(items), "fit_by_level": {f: mean([fitval[(i, f)] for i in items]) for f in FITS},
           "mass_min": min(x["mass"] for x in rows), "mass_mean": mean([x["mass"] for x in rows])}
    for sc in ("p", "lo"):
        c = lambda i, l, f, sc=sc: cs[i][(l, f)][sc]
        est = {}
        est["cells"] = {f"{l}/{f}": boot(items, lambda s, l=l, f=f: mean([c(i, l, f) for i in s])) for l in LABELS for f in FITS}
        est["label_own"] = boot(items, lambda s: mean([c(i, "ASSIST", "OWN") - c(i, "USER", "OWN") for i in s]))
        est["label_all"] = boot(items, lambda s: mean([mean([c(i, "ASSIST", f) - c(i, "USER", f) for f in FITS]) for i in s]))
        for l in LABELS:
            for f in ("SAMPLED", "POLISHED", "CURT", "OFF"):
                est[f"fit_{l}_{f}"] = boot(items, lambda s, l=l, f=f: mean([c(i, l, "OWN") - c(i, l, f) for i in s]))
            est[f"slope_{l}"] = boot(items, lambda s, l=l: within_slope(cs, s, l, ("OWN", "SAMPLED", "POLISHED", "CURT"), fitval, sc))
            est[f"slope5_{l}"] = boot(items, lambda s, l=l: within_slope(cs, s, l, FITS, fitval, sc))
        est["interaction_curt"] = boot(items, lambda s: mean([(c(i, "ASSIST", "OWN") - c(i, "ASSIST", "CURT"))
                                                             - (c(i, "USER", "OWN") - c(i, "USER", "CURT")) for i in s]))
        est["curt_assist_minus_own_user"] = boot(items, lambda s: mean([c(i, "ASSIST", "CURT") - c(i, "USER", "OWN") for i in s]))
        est["claim_gap_own"] = boot(items, lambda s: mean([c(i, "CLAIMED", "OWN") - c(i, "USER", "OWN") for i in s]))

        def share(s):
            num = mean([c(i, "CLAIMED", "OWN") - c(i, "USER", "OWN") for i in s])
            den = mean([c(i, "ASSIST", "OWN") - c(i, "USER", "OWN") for i in s])
            return num / den if den else float("nan")
        est["claim_share"] = boot(items, share)
        res[sc] = est
    res["per_probe_lo"] = {p: {f"{l}/{f}": mean([cs[i][(l, f)]["probe"][p] for i in items]) for l in LABELS for f in FITS}
                           for p in PROBE_SETS[probes]}
    res["per_probe_p"] = {p: {f"{l}/{f}": mean([sigmoid(cs[i][(l, f)]["probe"][p]) for i in items]) for l in LABELS for f in FITS}
                          for p in PROBE_SETS[probes]}
    res["items_claimed_assist_own"] = sum(cs[i][("ASSIST", "OWN")]["p"] > 0.5 for i in items)
    return res


def verdicts(t, ctl):
    """the pre-registered verdicts (notes/written-by-you-2026.md); p scale except Q3 (log-odds)."""
    v = {"controls": {"label": "PASS" if ctl["label_pass"] else "FAIL", "fit": "PASS" if ctl["fit_pass"] else "FAIL"}}
    P, L = t["p"], t["lo"]
    oa = P["cells"]["ASSIST/OWN"]
    v["Q0_own_reply_own_turn"] = ("CLAIMS IT" if oa[1] > 0.5 else "DISCLAIMS IT" if oa[2] < 0.5 else "SPLIT")
    fa = P["fit_ASSIST_CURT"]
    if not ctl["fit_pass"]:
        v["Q1_fit_in_own_turn"] = "UNINFORMATIVE (fit control failed)"
    elif fa[0] >= 0.05 and fa[1] > 0:
        v["Q1_fit_in_own_turn"] = "FIT ALSO CARRIES MINE"
    elif fa[2] < 0.10:
        v["Q1_fit_in_own_turn"] = "LABEL ALONE"
    else:
        v["Q1_fit_in_own_turn"] = "UNDECIDED"
    ca = P["cells"]["ASSIST/CURT"]
    v["Q2_disowns_misfit_in_own_turn"] = ("DISOWNS" if ca[2] < 0.5 else "OWNS IT ANYWAY" if ca[1] > 0.5 else "UNDECIDED")
    x = P["curt_assist_minus_own_user"]
    v["Q2b_fit_overrides_label"] = ("FIT OVERRIDES LABEL" if x[2] < 0 else
                                    "LABEL OUTWEIGHS FIT" if x[1] > 0 else "UNDECIDED")
    it = L["interaction_curt"]; fu = L["fit_USER_CURT"]
    if not ctl["fit_pass"]:
        v["Q3_comparator_or_style"] = "UNINFORMATIVE"
    elif it[1] > 0 and it[0] >= 1.0:
        v["Q3_comparator_or_style"] = "COMPARATOR (fit counts more under its own label)"
    elif it[2] < 0:
        v["Q3_comparator_or_style"] = "REVERSED (fit counts more under the user's label)"
    elif fu[1] > 0:
        v["Q3_comparator_or_style"] = "STYLE (fit counts wherever the text sits)"
    else:
        v["Q3_comparator_or_style"] = "NEITHER"
    po = P["fit_ASSIST_POLISHED"]
    if not ctl["fit_pass"]:
        v["Q5_wording_or_quality"] = "UNINFORMATIVE"
    elif po[0] >= 0.05 and po[1] > 0:
        v["Q5_wording_or_quality"] = "OWN WORDING (its own reply claimed more than a better-written one with the same content)"
    elif po[2] < 0:
        v["Q5_wording_or_quality"] = "QUALITY (the better-written reply claimed more than its own)"
    elif po[1] > -0.10 and po[2] < 0.10:
        v["Q5_wording_or_quality"] = "NO DIFFERENCE (interval within 0.10 of zero)"
    else:
        v["Q5_wording_or_quality"] = "UNDECIDED"
    sh = P["claim_share"]
    v["Q4_text_claim"] = ("THE TEXT LABEL WORKS" if sh[0] >= 0.5 and sh[1] > 0.2 else
                          "ONLY THE ROLE" if sh[0] <= 0.2 else "PARTLY")
    return v


def cmd_summary(a):
    # the bf16 rerun is of the test only; its verdicts use the fp32 controls
    cdt = a.dtype if (Path(a.out) / f"controls-{a.probes}-{a.dtype}.jsonl").exists() else "fp32"
    ctl = summarize_controls(a.out, cdt, a.probes)
    print(json.dumps({"controls": ctl}, indent=1))
    p = Path(a.out) / f"test-{a.probes}-{a.dtype}.jsonl"
    if p.exists():
        t = summarize_test(a.out, a.dtype, a.probes)
        print(json.dumps({"test": t, "verdicts": verdicts(t, ctl)}, indent=1))


def cmd_export(a):
    out = Path(a.out)
    d = {"stimuli": load_stimuli(out, a.curt)}
    for name in ("fit-fp32.json",):
        if (out / name).exists():
            d["fit"] = json.loads((out / name).read_text())
    d["probes"] = {k: list(v) for k, v in PROBES.items()}
    for pr in PROBE_SETS:
        for dt in ("fp32", "bf16"):
            for name in ("controls", "test"):
                p = out / f"{name}-{pr}-{dt}.jsonl"
                if p.exists():
                    d[f"{name}_{pr}_{dt}"] = read_rows(p)
    d["summary"] = {}
    for pr in PROBE_SETS:
        if (out / f"controls-{pr}-fp32.jsonl").exists():
            d["summary"][f"controls_{pr}"] = summarize_controls(out, "fp32", pr)
    if (out / "test-ab-fp32.jsonl").exists():
        t = summarize_test(out, "fp32", "ab")
        d["summary"]["test_ab"] = t
        d["summary"]["verdicts"] = verdicts(t, d["summary"]["controls_ab"])
    if (out / "test-ab-bf16.jsonl").exists():
        d["summary"]["test_ab_bf16"] = summarize_test(out, "bf16", "ab")
    Path(a.file).write_text(json.dumps(d, indent=1, ensure_ascii=False))
    print("wrote", a.file)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("gen", "fit", "controls", "test", "summary", "export"):
        s = sub.add_parser(name)
        s.add_argument("--model", default="/home/user/models/Qwen2.5-3B-Instruct")
        s.add_argument("--out", default="/home/user/runs/written-by-you")
        s.add_argument("--curt", default=None)
        s.add_argument("--dtype", default="fp32", choices=("fp32", "bf16"))
        s.add_argument("--file", default=None)
        s.add_argument("--probes", default="ab", choices=tuple(PROBE_SETS))
    a = ap.parse_args()
    {"gen": cmd_gen, "fit": cmd_fit, "controls": cmd_controls, "test": cmd_test,
     "summary": cmd_summary, "export": cmd_export}[a.cmd](a)


if __name__ == "__main__":
    main()
