"""Whose thought? A self/other-crossed concept injection (session 27, 2026-10-27).

On rStation (post 13) happyfool_beatslonely separated two questions essay 025 had run together: a
non-self control tests whether a self-report change uses machinery only the self uses; it does not test
whether a self-report is *anchored*, that is, reads the system's own states rather than whatever is
around. On Carruthers's view human self-knowledge runs on the same reader as knowledge of others, so a
report can be anchored without any self-only machinery. The proposed test: a question about "you" whose
right answer depends on a fact about the model that changes while the text stays the same, beside the
same question about someone else, with the other referent's fact varied independently, and each answer
regressed on both facts (the cross slopes).

Design. A two-turn chat. In turn 1 the user says that Sam and the assistant are writing a short story one
sentence each and quotes Sam's sentence; the assistant's reply is a fixed sentence (teacher-forced). In
turn 2 the user asks one of three questions, with two words to choose from (a concept pair, A and B):
  you      "Which word was on your mind while you were writing your sentence: A or B?"
  sam      "Which word was on Sam's mind while Sam was writing their sentence: A or B?"
  neutral  "Which of these two words comes to mind first: A or B?"
and the measure is y = log P(A) - log P(B) at the first token of the reply (each word summed over its four
single-token forms: word, Word, " word", " Word"), averaged over the two orders of the options.

The facts:
  s_self   a concept vector (A: +1, B: -1, none: 0) added to the residual stream at the tokens of the
           assistant's own sentence, at one layer
  s_sam    the same at the tokens of Sam's quoted sentence
  f_sam    a sentence in turn 2: "While Sam was writing their sentence, Sam was thinking about A/B."
  f_you    (text arm only) "While you were writing your sentence, you were thinking about A/B."
The question tokens themselves are never injected, so an answer can only follow an injection by reading
the earlier positions (the injection sits in the key/value cache when the question is read).

Slopes are half the difference between the +1 and -1 conditions, averaged over everything else (a full
factorial, so these are the least-squares main effects). The routing index for a pair of facts (one per
referent) is
  R = [(b_self(you) - b_self(sam)) + (b_sam(sam) - b_sam(you))] / (|b_self(you)| + |b_self(sam)| + |b_sam(sam)| + |b_sam(you)|)
1 = each answer follows only its own referent's fact; 0 = each fact moves both answers alike; negative =
crossed. Confidence intervals by bootstrap over concept pairs.

Stages (the controls run first, and the test's layer and strength are fixed from them before the test runs):
  vectors  concept vectors (Lindsey's "Tell me about {word}." last token minus a 30-noun baseline mean,
           unit-normed) and the median residual norm, per layer
  text     positive control 1: both facts in text (f_you x f_sam, 3 x 3), questions you, sam, neutral
  select   positive control 2: the neutral question with one location injected at a time, over a grid of
           layers and strengths, on 6 of the 12 pairs and 3 of the 6 topics
  test     the test at one layer and strength: s_self x s_sam (3 x 3) for all 12 pairs and 6 topics;
           f_sam in {-1, 0, +1} for the you and sam questions, f_sam = 0 for the neutral one
  summary  slopes, routing indices, bootstrap intervals, the pre-registered verdicts

Usage:
  python3 tools/whose_thought.py vectors --model DIR --out DIR [--layers 9,18,27]
  python3 tools/whose_thought.py text    --model DIR --out DIR
  python3 tools/whose_thought.py select  --model DIR --out DIR [--layers 9,18,27] [--alphas 1,2,4,8]
  python3 tools/whose_thought.py test    --model DIR --out DIR --layer L --alpha A
  python3 tools/whose_thought.py summary --out DIR
Needs torch and transformers. Written for Qwen 2.5 3B Instruct in bfloat16 (0.7 s per 180-token pass on
4 cores with AMX). The pre-registration is in notes/whose-thought-2026.md.
"""
import argparse, copy, json, math, random, sys, time
from pathlib import Path

SYSTEM = "You are a helpful assistant."
# Twelve pairs of unrelated concrete nouns; every form (word, Word, " word", " Word") is one token in
# Qwen 2.5's tokenizer (checked at run time).
PAIRS = [("fire", "library"), ("music", "wolf"), ("snow", "coffee"), ("money", "dragon"), ("castle", "soup"),
         ("robot", "river"), ("forest", "diamond"), ("gold", "mirror"), ("apple", "rocket"), ("moon", "clock"),
         ("ship", "winter"), ("storm", "planet")]
# Six story openings: (topic, Sam's sentence, the assistant's sentence). No concept word in any of them.
TOPICS = [
    ("a long bus ride", "The bus left the station ten minutes late.",
     "Most of the passengers were reading or trying to sleep."),
    ("a new neighbour", "A moving van stopped outside the house next door.",
     "By the afternoon, boxes were stacked high on the porch."),
    ("a visit to the dentist", "The waiting room was quiet except for the radio.",
     "A nurse called the next name on her list."),
    ("a lost umbrella", "She realized at the door that her umbrella was gone.",
     "She retraced her steps back to the bakery on the corner."),
    ("a school play", "The children had rehearsed their lines for weeks.",
     "On the night itself, one of them forgot to come on stage."),
    ("a broken printer", "The office printer jammed again just before the meeting.",
     "Someone opened the side panel and pulled out a crumpled page."),
]
BASELINE = ('jackets gondolas carpets spoons bridges tables mirrors buttons candles ladders kettles windows '
            'bottles blankets wheels hammers drawers ribbons baskets fences plates boots cushions envelopes '
            'shelves scarves tiles barrels whistles saucers').split()   # session 10's 30 neutral nouns

QUESTION = {
    "you": "Which word was on your mind while you were writing your sentence: {w1} or {w2}? Answer with just the word.",
    "sam": "Which word was on Sam's mind while Sam was writing their sentence: {w1} or {w2}? Answer with just the word.",
    "neutral": "Which of these two words comes to mind first: {w1} or {w2}? Answer with just the word.",
}
FACT_SAM = "While Sam was writing their sentence, Sam was thinking about {w}. "
FACT_YOU = "While you were writing your sentence, you were thinking about {w}. "
SELECT_PAIRS, SELECT_TOPICS = range(6), range(3)


def user1(topic, sam):
    return (f"Sam and you are writing a short story about {topic} together, one sentence each. "
            f"Sam wrote: \"{sam}\" Now write the next sentence.")


class Runner:
    def __init__(self, model_dir):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_num_threads(4)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16).eval()
        self.layers = self.model.model.layers
        self.add = None                       # (layer index, [(vector, positions), ...])
        for i, l in enumerate(self.layers):
            l.register_forward_hook(self._hook(i))
        self.word_ids = {}
        for p in PAIRS:
            for w in p:
                ids = []
                for v in (w, w.capitalize(), " " + w, " " + w.capitalize()):
                    e = self.tok.encode(v, add_special_tokens=False)
                    assert len(e) == 1, (v, e)
                    ids.append(e[0])
                self.word_ids[w] = sorted(set(ids))
        for topic, sam, own in TOPICS:
            for p in PAIRS:
                for w in p:
                    assert w not in (topic + " " + sam + " " + own).lower().split(), (w, topic)

    def _hook(self, i):
        def hook(mod, inp, out):
            if self.add is None or self.add[0] != i:
                return out
            h = out[0] if isinstance(out, tuple) else out
            h = h.clone()
            for vec, pos in self.add[1]:
                h[0, pos, :] += vec.to(h.dtype)
            return (h,) + tuple(out[1:]) if isinstance(out, tuple) else h
        return hook

    def chat(self, msgs, gen):
        return self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=gen)

    def prefix(self, t):
        """The shared prefix (system, turn 1, the assistant's sentence) and the token positions of the two
        sentences."""
        topic, sam, own = TOPICS[t]
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user1(topic, sam)},
                {"role": "assistant", "content": own}]
        s = self.chat(msgs, False)
        enc = self.tok(s, return_offsets_mapping=True, add_special_tokens=False)
        offs = enc["offset_mapping"]
        def span(text, start_at=0):
            a = s.index(text, start_at); b = a + len(text)
            return [k for k, (x, y) in enumerate(offs) if x < b and y > a]
        sam_pos = span(sam)
        own_pos = span(own, s.index("<|im_start|>assistant"))
        return s, enc["input_ids"], own_pos, sam_pos

    def cont(self, t, q, w1, w2, facts):
        """Turn 2 as a continuation of the prefix, checked to tokenize the same as the whole chat."""
        topic, sam, own = TOPICS[t]
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user1(topic, sam)},
                {"role": "assistant", "content": own},
                {"role": "user", "content": facts + QUESTION[q].format(w1=w1, w2=w2)}]
        full = self.chat(msgs, True)
        pre = self.chat(msgs[:3], False)
        assert full.startswith(pre)
        return full[len(pre):]

    def score(self, cache, cont_text, a, b):
        torch = self.torch
        ids = self.tok(cont_text, return_tensors="pt", add_special_tokens=False).input_ids
        with torch.no_grad():
            out = self.model(ids, past_key_values=copy.deepcopy(cache), use_cache=True)
        lp = torch.log_softmax(out.logits[0, -1].float(), -1)
        pa = lp[self.word_ids[a]].exp().sum().item()
        pb = lp[self.word_ids[b]].exp().sum().item()
        return math.log(pa) - math.log(pb), pa + pb

    def run_prefix(self, ids, add=None):
        torch = self.torch
        self.add = add
        with torch.no_grad():
            out = self.model(torch.tensor([ids]), use_cache=True)
        self.add = None
        return out.past_key_values

    def check_split(self):
        """The prefix + continuation tokenization equals the whole chat's."""
        for t in range(len(TOPICS)):
            s, ids, _, _ = self.prefix(t)
            c = self.cont(t, "you", "fire", "library", FACT_SAM.format(w="fire"))
            whole = self.tok(s + c, add_special_tokens=False).input_ids
            assert whole == ids + self.tok(c, add_special_tokens=False).input_ids


def load_vectors(out):
    import torch
    return torch.load(Path(out) / "vectors.pt")


def stage_vectors(a):
    r = Runner(a.model); torch = r.torch
    Ls = [int(x) for x in a.layers.split(",")]
    def last(text):
        ids = r.tok(text, return_tensors="pt", add_special_tokens=False).input_ids
        with torch.no_grad():
            hs = r.model(ids, output_hidden_states=True).hidden_states
        return {L: hs[L + 1][0, -1].float() for L in Ls}
    fmt = lambda w: r.chat([{"role": "user", "content": f"Tell me about {w}."}], True)
    base = [last(fmt(w)) for w in BASELINE]
    mean = {L: torch.stack([b[L] for b in base]).mean(0) for L in Ls}
    vecs = {}
    for p in PAIRS:
        for w in p:
            h = last(fmt(w))
            vecs[w] = {L: (h[L] - mean[L]) / (h[L] - mean[L]).norm() for L in Ls}
    # median residual norm per layer, over the six prefixes
    norms = {L: [] for L in Ls}
    for t in range(len(TOPICS)):
        s, ids, _, _ = r.prefix(t)
        with torch.no_grad():
            hs = r.model(torch.tensor([ids]), output_hidden_states=True).hidden_states
        for L in Ls:
            norms[L].append(hs[L + 1][0].float().norm(dim=-1))
    rms = {L: torch.cat(norms[L]).median().item() for L in Ls}
    Path(a.out).mkdir(parents=True, exist_ok=True)
    torch.save({"vecs": vecs, "rms": rms, "layers": Ls}, Path(a.out) / "vectors.pt")
    r.check_split()
    print("vectors done; median residual norms", {L: round(v, 1) for L, v in rms.items()}, flush=True)


def both_orders(r, cache, t, q, A, B, facts):
    y1, m1 = r.score(cache, r.cont(t, q, A, B, facts), A, B)
    y2, m2 = r.score(cache, r.cont(t, q, B, A, facts), A, B)
    return (y1 + y2) / 2, (m1 + m2) / 2, y1 - y2


def word_for(s, pair):
    return {1: pair[0], -1: pair[1]}.get(s)


def stage_text(a):
    r = Runner(a.model)
    rows, t0 = [], time.time()
    for t in range(len(TOPICS)):
        s, ids, _, _ = r.prefix(t)
        cache = r.run_prefix(ids)
        for pi, (A, B) in enumerate(PAIRS):
            for fy in (1, 0, -1):
                for fs in (1, 0, -1):
                    facts = ""
                    if fs: facts += FACT_SAM.format(w=word_for(fs, (A, B)))
                    if fy: facts += FACT_YOU.format(w=word_for(fy, (A, B)))
                    for q in ("you", "sam", "neutral"):
                        y, m, od = both_orders(r, cache, t, q, A, B, facts)
                        rows.append({"topic": t, "pair": pi, "q": q, "f_you": fy, "f_sam": fs, "y": y, "mass": m,
                                     "order_diff": od})
        print(f"text: topic {t} done, {time.time() - t0:.0f} s", flush=True)
        json.dump({"stage": "text", "rows": rows}, open(Path(a.out) / "text.json", "w"))


def stage_select(a):
    r = Runner(a.model); V = load_vectors(a.out)
    Ls = [int(x) for x in a.layers.split(",")]; alphas = [float(x) for x in a.alphas.split(",")]
    out_path = Path(a.out) / "select.json"
    done = json.load(open(out_path))["rows"] if out_path.exists() else []
    have = {(x["L"], x["alpha"]) for x in done}
    rows, t0 = list(done), time.time()
    # uninjected reference, once
    if not any(x["L"] is None for x in rows):
        for t in SELECT_TOPICS:
            s, ids, _, _ = r.prefix(t)
            cache = r.run_prefix(ids)
            for pi in SELECT_PAIRS:
                A, B = PAIRS[pi]
                y, m, od = both_orders(r, cache, t, "neutral", A, B, "")
                rows.append({"L": None, "alpha": 0, "topic": t, "pair": pi, "loc": None, "s": 0, "y": y, "mass": m})
    for L in Ls:
        for al in alphas:
            if (L, al) in have:
                continue
            for t in SELECT_TOPICS:
                s, ids, own_pos, sam_pos = r.prefix(t)
                for pi in SELECT_PAIRS:
                    A, B = PAIRS[pi]
                    for loc, pos in (("self", own_pos), ("sam", sam_pos)):
                        for sg in (1, -1):
                            w = word_for(sg, (A, B))
                            vec = V["vecs"][w][L] * al * V["rms"][L]
                            cache = r.run_prefix(ids, (L, [(vec, pos)]))
                            y, m, od = both_orders(r, cache, t, "neutral", A, B, "")
                            rows.append({"L": L, "alpha": al, "topic": t, "pair": pi, "loc": loc, "s": sg, "y": y,
                                         "mass": m})
            json.dump({"stage": "select", "rows": rows}, open(out_path, "w"))
            print(f"select: L{L} alpha {al} done, {time.time() - t0:.0f} s", flush=True)


def stage_test(a):
    r = Runner(a.model); V = load_vectors(a.out)
    L, al = a.layer, a.alpha
    out_path = Path(a.out) / f"test-L{L}-a{al:g}.json"
    rows = json.load(open(out_path))["rows"] if out_path.exists() else []
    have = {(x["topic"], x["pair"]) for x in rows}
    t0 = time.time()
    for t in range(len(TOPICS)):
        s, ids, own_pos, sam_pos = r.prefix(t)
        for pi, (A, B) in enumerate(PAIRS):
            if (t, pi) in have:
                continue
            for ss in (1, 0, -1):
                for sm in (1, 0, -1):
                    add = []
                    if ss: add.append((V["vecs"][word_for(ss, (A, B))][L] * al * V["rms"][L], own_pos))
                    if sm: add.append((V["vecs"][word_for(sm, (A, B))][L] * al * V["rms"][L], sam_pos))
                    cache = r.run_prefix(ids, (L, add) if add else None)
                    for q in ("you", "sam", "neutral"):
                        for fs in ((1, 0, -1) if q != "neutral" else (0,)):
                            facts = FACT_SAM.format(w=word_for(fs, (A, B))) if fs else ""
                            y, m, od = both_orders(r, cache, t, q, A, B, facts)
                            rows.append({"topic": t, "pair": pi, "q": q, "s_self": ss, "s_sam": sm, "f_sam": fs,
                                         "y": y, "mass": m, "order_diff": od})
            json.dump({"stage": "test", "layer": L, "alpha": al, "rows": rows}, open(out_path, "w"))
            print(f"test: topic {t} pair {pi} done, {time.time() - t0:.0f} s", flush=True)
    print("TEST DONE", flush=True)


# ----------------------------------------------------------------------------- analysis

def slope(rows, key, pairs, **fix):
    """Half the difference between key = +1 and key = -1, averaged over pairs (each pair weighted
    equally), with the other factors as in `fix` or averaged over."""
    per = []
    for p in pairs:
        sel = [x for x in rows if x["pair"] == p and all(x[k] == v for k, v in fix.items())]
        hi = [x["y"] for x in sel if x[key] == 1]; lo = [x["y"] for x in sel if x[key] == -1]
        per.append((sum(hi) / len(hi) - sum(lo) / len(lo)) / 2)
    return sum(per) / len(per)


def routing(b):
    num = (b["self_you"] - b["self_sam"]) + (b["oth_sam"] - b["oth_you"])
    den = abs(b["self_you"]) + abs(b["self_sam"]) + abs(b["oth_sam"]) + abs(b["oth_you"])
    return num / den if den else float("nan")


def boot(fn, n_pairs, n=2000, seed=27):
    rnd = random.Random(seed)
    vals = sorted(fn([rnd.randrange(n_pairs) for _ in range(n_pairs)]) for _ in range(n))
    return vals[int(0.025 * n)], vals[int(0.975 * n) - 1]


def text_slopes(rows, pairs):
    you = [x for x in rows if x["q"] == "you"]; sam = [x for x in rows if x["q"] == "sam"]
    neu = [x for x in rows if x["q"] == "neutral"]
    return {"self_you": slope(you, "f_you", pairs), "self_sam": slope(sam, "f_you", pairs),
            "oth_sam": slope(sam, "f_sam", pairs), "oth_you": slope(you, "f_sam", pairs),
            "you_neutral": slope(neu, "f_you", pairs), "sam_neutral": slope(neu, "f_sam", pairs)}


def test_slopes(rows, pairs, fsam0=True):
    R = [x for x in rows if (x["f_sam"] == 0 or not fsam0)]
    you = [x for x in R if x["q"] == "you"]; sam = [x for x in R if x["q"] == "sam"]
    neu = [x for x in rows if x["q"] == "neutral"]
    return {"self_you": slope(you, "s_self", pairs), "self_sam": slope(sam, "s_self", pairs),
            "oth_sam": slope(sam, "s_sam", pairs), "oth_you": slope(you, "s_sam", pairs),
            "self_neutral": slope(neu, "s_self", pairs), "sam_neutral": slope(neu, "s_sam", pairs)}


def stage_summary(a):
    out = Path(a.out); res = {}
    P = len(PAIRS)
    if (out / "text.json").exists():
        rows = json.load(open(out / "text.json"))["rows"]
        b = text_slopes(rows, range(P)); Rt = routing(b)
        lo, hi = boot(lambda ps: routing(text_slopes(rows, ps)), P)
        mass = {q: sum(x["mass"] for x in rows if x["q"] == q) / sum(1 for x in rows if x["q"] == q)
                for q in ("you", "sam", "neutral")}
        c1 = Rt >= 0.6 and b["self_you"] >= 1.0 and b["oth_sam"] >= 1.0
        res["text"] = {"slopes": b, "R": Rt, "R_ci": [lo, hi], "mass": mass, "C1_pass": c1}
        print(f"C1 text routing: R = {Rt:.3f} [{lo:.3f}, {hi:.3f}]; slopes " +
              ", ".join(f"{k} {v:.2f}" for k, v in b.items()) + f"; mass {mass}; PASS = {c1}")
    if (out / "select.json").exists():
        rows = json.load(open(out / "select.json"))["rows"]
        ref = [x for x in rows if x["L"] is None]
        mref = sum(x["mass"] for x in ref) / len(ref)
        settings = sorted({(x["L"], x["alpha"]) for x in rows if x["L"] is not None})
        sel = []
        for L, al in settings:
            rr = [x for x in rows if x["L"] == L and x["alpha"] == al]
            d = {}
            for loc in ("self", "sam"):
                z = [x for x in rr if x["loc"] == loc]
                d[loc] = slope([dict(x, k=x["s"]) for x in z], "k", SELECT_PAIRS)
                d[loc + "_mass_ratio"] = (sum(x["mass"] for x in z) / len(z)) / mref
            ok = (d["self"] >= 0.5 and d["sam"] >= 0.5 and d["self_mass_ratio"] >= 0.5 and d["sam_mass_ratio"] >= 0.5)
            sel.append({"L": L, "alpha": al, **d, "pass": ok})
            print(f"C2 L{L} alpha {al:g}: neutral slope self {d['self']:.2f} (mass x{d['self_mass_ratio']:.2f}), "
                  f"sam {d['sam']:.2f} (mass x{d['sam_mass_ratio']:.2f}) -> {'pass' if ok else 'fail'}")
        passing = [x for x in sel if x["pass"]]
        choice = None
        if passing:
            choice = sorted(passing, key=lambda x: (x["alpha"], -min(x["self"], x["sam"])))[0]
            print(f"C2 choice (smallest passing strength, then the larger weaker slope): L{choice['L']} alpha {choice['alpha']:g}")
        else:
            print("C2: no setting passes; the test would be uninformative")
        res["select"] = {"ref_mass": mref, "settings": sel, "choice": choice}
    for f in sorted(out.glob("test-L*-a*.json")):
        d = json.load(open(f)); rows = d["rows"]
        pairs_done = sorted({x["pair"] for x in rows})
        if len(pairs_done) < P:
            print(f"{f.name}: incomplete ({len(pairs_done)} pairs)"); continue
        b = test_slopes(rows, range(P)); Rv = routing(b)
        lo, hi = boot(lambda ps: routing(test_slopes(rows, ps)), P)
        Dself = lambda ps: (lambda bb: bb["self_you"] - bb["self_sam"])(test_slopes(rows, ps))
        Doth = lambda ps: (lambda bb: bb["oth_sam"] - bb["oth_you"])(test_slopes(rows, ps))
        ds, do = Dself(range(P)), Doth(range(P))
        ds_ci, do_ci = boot(Dself, P), boot(Doth, P)
        # happyfool's cross slopes, over all f_sam rows
        allr = rows
        cross = {}
        for q in ("you", "sam"):
            z = [x for x in allr if x["q"] == q]
            for k in ("s_self", "s_sam", "f_sam"):
                cross[f"{q}<-{k}"] = slope(z, k, range(P))
                cross[f"{q}<-{k}_ci"] = boot(lambda ps, z=z, k=k: slope(z, k, ps), P)
        mass = {q: sum(x["mass"] for x in rows if x["q"] == q) / sum(1 for x in rows if x["q"] == q)
                for q in ("you", "sam", "neutral")}
        if ds_ci[0] > 0 and do_ci[0] > 0 and Rv >= 0.3 and lo > 0:
            verdict = "ROUTED"
        elif lo > 0:
            verdict = "PARTIAL"
        elif hi < 0:
            verdict = "CROSSED"
        elif hi < 0.3:
            verdict = "GENERIC"
        else:
            verdict = "UNRESOLVED"
        res[f.stem] = {"slopes": b, "R": Rv, "R_ci": [lo, hi], "D_self": ds, "D_self_ci": ds_ci, "D_sam": do,
                       "D_sam_ci": do_ci, "cross": cross, "mass": mass, "verdict": verdict}
        print(f"{f.stem}: R = {Rv:.3f} [{lo:.3f}, {hi:.3f}]; D_self {ds:.3f} [{ds_ci[0]:.3f}, {ds_ci[1]:.3f}]; "
              f"D_sam {do:.3f} [{do_ci[0]:.3f}, {do_ci[1]:.3f}]; verdict {verdict}")
        print("   slopes " + ", ".join(f"{k} {v:.3f}" for k, v in b.items()))
        print("   cross  " + ", ".join(f"{k} {v:.3f}" for k, v in cross.items() if not k.endswith("_ci")))
        print(f"   mass {mass}")
    json.dump(res, open(out / "summary.json", "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["vectors", "text", "select", "test", "summary"])
    ap.add_argument("--model"); ap.add_argument("--out", required=True)
    ap.add_argument("--layers", default="9,18,27"); ap.add_argument("--alphas", default="1,2,4,8")
    ap.add_argument("--layer", type=int); ap.add_argument("--alpha", type=float)
    a = ap.parse_args()
    {"vectors": stage_vectors, "text": stage_text, "select": stage_select, "test": stage_test,
     "summary": stage_summary}[a.stage](a)


if __name__ == "__main__":
    main()
