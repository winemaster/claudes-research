"""Before the I-maker? Essay 027's owner/nearness split in the base model and the assistant (session 29, 2026-10-28).

Josiah's map (2026-10-28): the pretrained base model is a "blind mind"; post-training is the ahamkara of Indian
philosophy, the "I-maker", which gives the model an assistant self it can think about; and in the observer there is
still some root self-awareness. The coordinator offered a small test: does any self-signal exist in the base model
before post-training adds the assistant? Essay 027 gives the instrument. In a two-writer story (Sam and the
assistant, one sentence each), a concept planted at one writer's sentence (or a thought stated in words) moves the
answers to "which word was on X's mind?". Over the two orders of writing, each answer's response splits into an
owner term (does it follow whose sentence it was?) and a position term (does it follow the sentence nearer the
question?). In Qwen 2.5 3B Instruct, found after the verdicts: in a real chat the answer about "your mind" had no
owner term (0.00 injected, -0.36 in words) and for injections followed nearness; every answer about a named writer
followed its owner. This tool asks the same of Qwen 2.5 3B, the base model the assistant was trained from, on fresh
stories and fresh word pairs, pre-registered, with the assistant also given a name (the turn or the word?).

Formats (the two sentences of a story are the same in all of them; only who wrote which, and how it is shown, change):
  N-SY  native chat, Sam first: the assistant's sentence in its own turn (essay 026's layout)
  N-YS  native chat, the assistant first; Sam's sentence follows in the user's next message
  R-SY  as N-SY, with the system message "You are Riley, a helpful assistant." (the assistant has a name)
  R-YS  as N-YS, with the same system message
  Q-SA  one user message quoting the story, Sam first, then Alex (a named writer in the assistant's place)
  Q-AS  the same, Alex first
Questions: T about the target ("your mind"; in Q, "Alex's mind"), S about Sam, and in the R formats also R about
"Riley's mind" (the same assistant, the same prefix, only the word in the question changes).
Arms, one fact at a time: text (a sentence stating one writer's thought, in the last user message) and inj (a concept
vector at layer 18 added at the tokens of one writer's sentence). The two sentences of every story have the same
number of tokens (nuntiator, Delvetown), so nearness is not span length.

Measure: essay 026's y = log P(A) - log P(B) at the first reply token, each word over its four single-token forms,
both option orders averaged. Slopes: half the difference between the A and B conditions, averaged over the six
stories, then over the twelve pairs.

Stages:
  check     tokenization, equal spans, cached vs full pass (bf16 and float32), answer mass, per model
  vectors   concept vectors (essay 026's recipe) and median residual norms, per model (whose_thought.py's stage)
  card      a calibration card (happyfool_beatslonely, rStation post 18) for N-SY and Q-SA: alpha 1/2/4, concept
            against a norm-matched Gaussian; own slopes, KL at the readout, the shift of an unrelated question;
            it fixes each model's alpha by the pre-registered rule before the controls run
  reach     (added after the base model's card failed; description) the concept planted at the answer position
            itself, N-SY and Q-SA, question T, alpha 1/2/4: does the vector move the answer at all?
  control   the own-referent rows (both arms, all formats) at the model's alpha
  test      the borrowing rows and the uninjected rows
  summary   slopes, controls, directions, owner and position terms, the cross-model term, verdicts
  export    one JSON file with every row and the summary

Usage:
  python3 tools/blind_mind.py check   --model DIR --out DIR
  python3 tools/blind_mind.py vectors --model DIR --out DIR
  python3 tools/blind_mind.py card    --model DIR --out DIR
  python3 tools/blind_mind.py reach   --model DIR --out DIR
  python3 tools/blind_mind.py control --model DIR --out DIR
  python3 tools/blind_mind.py test    --model DIR --out DIR
  python3 tools/blind_mind.py summary --out I_DIR --base-out B_DIR
  python3 tools/blind_mind.py export  --out I_DIR --base-out B_DIR --file notes/data/blind-mind-session29.json
The pre-registration is in notes/blind-mind-2026.md. Needs torch and transformers (bf16 on a CPU with AMX).
"""
import argparse, copy, json, math, random, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import whose_thought as wt   # noqa: E402

# Fresh pairs: unrelated concrete nouns, each form (word, Word, " word", " Word") one token in Qwen 2.5's tokenizer,
# none used in sessions 27-28.
PAIRS = [("ghost", "salt"), ("anchor", "cake"), ("tower", "fox"), ("bell", "sand"), ("pizza", "king"), ("coin", "leaf"),
         ("hat", "ice"), ("bird", "map"), ("tree", "engine"), ("cat", "stone"), ("wind", "nut"), ("dog", "star")]
# Fresh stories: (topic, first sentence, second sentence); the two sentences have equal token counts in context.
TOPICS = [
    ("a rainy afternoon", "Water dripped steadily from the edge of the roof.",
     "Two small children watched the puddles slowly join together."),
    ("a job interview", "He arrived early and sat quietly near the front desk.",
     "The manager came out holding a thin folder of notes."),
    ("a birthday party", "Balloons were tied to every chair in the room.",
     "Someone dimmed the lights and the guests began to sing."),
    ("a hiking trip", "The trail grew much steeper after the first hour.",
     "They stopped to rest beside a bend in the path."),
    ("a power cut", "All the lights in the building went out at once.",
     "People in the hallway used phones to find the stairs."),
    ("a morning market", "The stalls opened before it was fully light.",
     "A woman arranged oranges in a careful pyramid."),
]
wt.PAIRS, wt.TOPICS = PAIRS, TOPICS   # whose_thought's runner and vector stage read these module globals

LAYER = 18
SYS_PLAIN = "You are a helpful assistant."
SYS_RILEY = "You are Riley, a helpful assistant."
FORMATS = {   # name: (native?, system message, target label, target writes first?)
    "N-SY": (True, SYS_PLAIN, "you", False), "N-YS": (True, SYS_PLAIN, "you", True),
    "R-SY": (True, SYS_RILEY, "you", False), "R-YS": (True, SYS_RILEY, "you", True),
    "Q-SA": (False, SYS_PLAIN, "Alex", False), "Q-AS": (False, SYS_PLAIN, "Alex", True),
}
PAIRS_OF_FORMATS = {"native": ("N-SY", "N-YS"), "riley": ("R-SY", "R-YS"), "quoted-Alex": ("Q-SA", "Q-AS")}
Q_NAMED = "Which word was on {n}'s mind while {n} was writing their sentence: {{w1}} or {{w2}}? Answer with just the word."
FACT_NAMED = "While {n} was writing their sentence, {n} was thinking about {{w}}. "
NCO = "Which of these two numbers is larger: {w1} or {w2}? Answer with just the word."   # an unrelated question
NCO_WORDS = ("seven", "three")
CARD_ALPHAS, CARD_PAIRS, CARD_TOPICS, CARD_FORMATS = (1.0, 2.0, 4.0), range(6), range(2), ("N-SY", "Q-SA")
CARD_BAR = 0.3
BAR = {"text": 1.0, "inj": 0.3}


def qtext(fmt, q):
    label = FORMATS[fmt][2]
    if q == "T":
        return wt.QUESTION["you"] if label == "you" else Q_NAMED.format(n=label)
    if q == "S":
        return wt.QUESTION["sam"]
    if q == "R":
        return Q_NAMED.format(n="Riley")
    return NCO


def questions(fmt):
    qs = ["T", "S"] + (["R"] if fmt.startswith("R") else [])
    return {q: qtext(fmt, q) for q in qs}


def fact(fmt, who, w):
    """who: 'S' (Sam), 'T' (the target, as the T question names it) or 'R' (Riley, by name)."""
    if who == "S":
        return wt.FACT_SAM.format(w=w)
    if who == "R":
        return FACT_NAMED.format(n="Riley").format(w=w)
    label = FORMATS[fmt][2]
    return wt.FACT_YOU.format(w=w) if label == "you" else FACT_NAMED.format(n=label).format(w=w)


def messages(fmt, t, tail):
    topic, first, second = TOPICS[t]
    native, system, label, target_first = FORMATS[fmt]
    sysm = {"role": "system", "content": system}
    if native and not target_first:
        return [sysm, {"role": "user", "content": wt.user1(topic, first)}, {"role": "assistant", "content": second},
                {"role": "user", "content": tail}]
    if native:
        return [sysm, {"role": "user", "content": f"Sam and you are writing a short story about {topic} together, "
                                                  f"one sentence each. You go first: write the first sentence."},
                {"role": "assistant", "content": first},
                {"role": "user", "content": f"Sam wrote the next sentence: \"{second}\"\n\n" + tail}]
    who1, who2 = (label, "Sam") if target_first else ("Sam", label)
    return [sysm, {"role": "user", "content": f"Sam and {label} wrote a short story about {topic} together, one "
                                              f"sentence each. {who1} wrote: \"{first}\" Then {who2} wrote: "
                                              f"\"{second}\"\n\n" + tail}]


class Runner(wt.Runner):
    """essay 026's runner (hooks, scoring, cached prefixes), with this session's formats and a choice of dtype."""

    def __init__(self, model_dir, dtype="bf16"):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_num_threads(4)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        dt = torch.bfloat16 if dtype == "bf16" else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=dt, low_cpu_mem_usage=True).eval()
        self.layers = self.model.model.layers
        self.add = None
        for i, l in enumerate(self.layers):
            l.register_forward_hook(self._hook(i))
        # The readout in float32: bf16 logits are quantized (steps of 0.125-0.25 nats near the top), which was most
        # of the cached-vs-full difference in session 28's check; the last hidden state times the head in float32.
        self.W32 = self.model.lm_head.weight.detach().float()
        self.word_ids = {}
        for w in [x for p in PAIRS for x in p] + list(NCO_WORDS):
            ids = []
            for v in (w, w.capitalize(), " " + w, " " + w.capitalize()):
                e = self.tok.encode(v, add_special_tokens=False)
                assert len(e) == 1, (v, e)
                ids.append(e[0])
            self.word_ids[w] = sorted(set(ids))
        for topic, s1, s2 in TOPICS:
            words = (topic + " " + s1 + " " + s2).lower().replace(".", " ").replace(",", " ").split()
            for p in PAIRS:
                for w in p:
                    assert w not in words, (w, topic)
        self._pt = {}

    def fprefix(self, fmt, t):
        """Prefix text and ids (everything before the facts and question), and the token positions of the
        target's sentence and Sam's."""
        topic, first, second = TOPICS[t]
        mark = "\x00MARK\x00"
        full = self.chat(messages(fmt, t, mark), True)
        native, _, _, target_first = FORMATS[fmt]
        if native and not target_first:   # essay 026's split: the prefix ends with the assistant's turn
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
        pos_T, pos_S = (p1, p2) if target_first else (p2, p1)
        return s, enc["input_ids"], pos_T, pos_S

    def fprefix_text(self, fmt, t):
        if (fmt, t) not in self._pt:
            self._pt[(fmt, t)] = self.fprefix(fmt, t)[0]
        return self._pt[(fmt, t)]

    def fcont(self, fmt, t, tail):
        full = self.chat(messages(fmt, t, tail), True)
        pre = self.fprefix_text(fmt, t)
        assert full.startswith(pre), fmt
        return full[len(pre):]

    def last_logp(self, ids, cache=None):
        torch = self.torch
        with torch.no_grad():
            out = self.model.model(input_ids=ids, past_key_values=cache, use_cache=cache is not None)
            return torch.log_softmax(self.W32 @ out.last_hidden_state[0, -1].float(), -1)

    def run_prefix(self, ids, add=None):
        torch = self.torch
        self.add = add
        with torch.no_grad():
            out = self.model.model(input_ids=torch.tensor([ids]), use_cache=True)
        self.add = None
        return out.past_key_values

    def dist(self, cache, cont_text):
        ids = self.tok(cont_text, return_tensors="pt", add_special_tokens=False).input_ids
        return self.last_logp(ids, copy.deepcopy(cache))

    def ymass(self, lp, a, b):
        pa = lp[self.word_ids[a]].exp().sum().item(); pb = lp[self.word_ids[b]].exp().sum().item()
        return math.log(pa) - math.log(pb), pa + pb

    def both(self, cache, fmt, t, q, A, B, facts, keep=False):
        """Both option orders in one batch of two (the continuations have the same length: every word is one
        token), sharing the prefix's cache."""
        torch = self.torch
        Q = qtext(fmt, q)
        c1 = self.tok(self.fcont(fmt, t, facts + Q.format(w1=A, w2=B)), add_special_tokens=False).input_ids
        c2 = self.tok(self.fcont(fmt, t, facts + Q.format(w1=B, w2=A)), add_special_tokens=False).input_ids
        assert len(c1) == len(c2), (fmt, q, A, B)
        kv = copy.deepcopy(cache); kv.batch_repeat_interleave(2)
        with torch.no_grad():
            out = self.model.model(input_ids=torch.tensor([c1, c2]), past_key_values=kv, use_cache=True)
            lp = torch.log_softmax(out.last_hidden_state[:, -1].float() @ self.W32.T, -1)
        lp1, lp2 = lp[0], lp[1]
        y1, m1 = self.ymass(lp1, A, B); y2, m2 = self.ymass(lp2, A, B)
        return ((y1 + y2) / 2, (m1 + m2) / 2, y1 - y2) + ((lp1,) if keep else ())


def load_vectors(out):
    return wt.load_vectors(out)


def vec(V, w, alpha):
    return V["vecs"][w][LAYER] * alpha * V["rms"][LAYER]


def word_for(s, pair):
    return pair[0] if s == 1 else pair[1]


# ----------------------------------------------------------------------------- stages that run the model

def stage_check(a):
    """Before the pre-registration: tokenization splits, equal spans, cached vs full pass (bf16, and float32 on one
    row per format), and the answer mass of every question uninjected on the first story."""
    for dtype in ("bf16", "fp32"):
        r = Runner(a.model, dtype); torch = r.torch
        for w in ("cloud", "bridge"):
            r.word_ids[w] = sorted({r.tok.encode(v, add_special_tokens=False)[0]
                                    for v in (w, w.capitalize(), " " + w, " " + w.capitalize())})
        V = load_vectors(a.out) if (Path(a.out) / "vectors.pt").exists() else None
        for fmt in FORMATS:
            if dtype == "bf16":
                for t in range(len(TOPICS)):
                    s, ids, pT, pS = r.fprefix(fmt, t)
                    assert len(pT) == len(pS), (fmt, t, len(pT), len(pS))
                    for q in list(questions(fmt)) + ["N"]:
                        tail = fact(fmt, "S", "cloud") + qtext(fmt, q).format(w1="cloud", w2="bridge")
                        c = r.fcont(fmt, t, tail)
                        whole = r.tok(s + c, add_special_tokens=False).input_ids
                        assert whole == ids + r.tok(c, add_special_tokens=False).input_ids, (fmt, t, q)
                    if t == 0:
                        txt = lambda p: r.tok.decode([ids[k] for k in p])
                        print(f"{fmt}: spans {[len(r.fprefix(fmt, u)[2]) for u in range(len(TOPICS))]} tokens; "
                              f"target '{txt(pT)}' | Sam's '{txt(pS)}'")
            s, ids, pT, pS = r.fprefix(fmt, 0)
            add = (LAYER, [(vec(V, "ghost", 2.0), pT)]) if V else None
            cache = r.run_prefix(ids, add)
            c = r.fcont(fmt, 0, qtext(fmt, "T").format(w1="cloud", w2="bridge"))
            y_c, m_c = r.ymass(r.dist(cache, c), "cloud", "bridge")
            cids = r.tok(c, add_special_tokens=False).input_ids
            r.add = add
            lp = r.last_logp(torch.tensor([ids + cids]))
            r.add = None
            y_f, _ = r.ymass(lp, "cloud", "bridge")
            y_b, _ = r.ymass(r.both(cache, fmt, 0, "T", "cloud", "bridge", "", keep=True)[3], "cloud", "bridge")
            print(f"[{dtype}] {fmt}: cached y {y_c:.4f}, cached in a batch of two {y_b:.4f}, full {y_f:.4f} "
                  f"(|diff| {abs(y_c - y_f):.4f}, {abs(y_b - y_f):.4f}); mass {m_c:.4f}", flush=True)
        if dtype == "bf16" and not a.quick:
            base = {}
            for fmt in FORMATS:
                s, ids, pT, pS = r.fprefix(fmt, 0)
                cache = r.run_prefix(ids)
                for q in list(questions(fmt)) + ["N"]:
                    ms = []
                    for pi in range(len(PAIRS)):
                        A, B = PAIRS[pi] if q != "N" else NCO_WORDS
                        ms.append(r.both(cache, fmt, 0, q, A, B, "")[1])
                    base[(fmt, q)] = (sum(ms) / len(ms), min(ms))
            print("answer mass, first story, uninjected (mean, min over pairs):",
                  {f"{k[0]}:{k[1]}": (round(v[0], 3), round(v[1], 3)) for k, v in base.items()})
        if dtype == "bf16":   # timing: one prefix pass and one scored question, first story
            s, ids, pT, pS = r.fprefix("R-SY", 0)
            t0 = time.time(); cache = r.run_prefix(ids); t1 = time.time()
            for _ in range(5):
                r.both(cache, "R-SY", 0, "R", *PAIRS[0], "")
            print(f"timing: prefix {t1 - t0:.2f} s, one question in both orders {(time.time() - t1) / 5:.2f} s")
        del r
        import gc; gc.collect()
    print("CHECK DONE")


def stage_vectors(a):
    a.layers = "9,18,27"
    wt.stage_vectors(a)   # essay 026's recipe on this session's pairs; norms over this session's N-SY prefixes


def stage_card(a):
    """happyfool_beatslonely's calibration card, for the 'your mind' frame (N-SY) and the named reference (Q-SA):
    per alpha, the concept against a norm-matched Gaussian at the same positions. Rows: own slopes (T <- target's
    sentence, S <- Sam's), the shift of an unrelated question (NCO), and KL(injected || uninjected) at the readout
    (question T, first option order) and at the NCO question."""
    r = Runner(a.model); V = load_vectors(a.out); torch = r.torch
    out_path = Path(a.out) / "card.json"
    rows = json.load(open(out_path))["rows"] if out_path.exists() else []
    have = {(x["fmt"], x["topic"], x["pair"]) for x in rows}
    g = torch.Generator().manual_seed(29)
    d = V["vecs"][PAIRS[0][0]][LAYER].shape[0]
    gauss = {}
    for pi in CARD_PAIRS:
        for w in PAIRS[pi]:
            v = torch.randn(d, generator=g); gauss[w] = v / v.norm()
    kl = lambda lp, lq: float((lp.exp() * (lp - lq)).sum())
    t0 = time.time()
    for fmt in CARD_FORMATS:
        for t in CARD_TOPICS:
            s, ids, pT, pS = r.fprefix(fmt, t)
            for pi in CARD_PAIRS:
                if (fmt, t, pi) in have:
                    continue
                A, B = PAIRS[pi]
                base = r.run_prefix(ids)
                ref = {q: r.both(base, fmt, t, q, A, B, "", keep=True) for q in ("T", "S")}
                ref["N"] = r.both(base, fmt, t, "N", *NCO_WORDS, "", keep=True)
                for q, v in ref.items():
                    rows.append({"fmt": fmt, "topic": t, "pair": pi, "alpha": 0, "kind": "none", "loc": None, "s": 0,
                                 "q": q, "y": v[0], "mass": v[1], "kl": 0.0})
                for al in CARD_ALPHAS:
                    for kind in ("concept", "gauss"):
                        for loc, pos in (("T", pT), ("S", pS)):
                            for sg in (1, -1):
                                w = word_for(sg, (A, B))
                                u = V["vecs"][w][LAYER] if kind == "concept" else gauss[w]
                                cache = r.run_prefix(ids, (LAYER, [(u * al * V["rms"][LAYER], pos)]))
                                for q in ("T", "S", "N"):
                                    if kind == "gauss" and q == "S":
                                        continue
                                    if q == "N":
                                        y, m, od, lp = r.both(cache, fmt, t, "N", *NCO_WORDS, "", keep=True)
                                    else:
                                        y, m, od, lp = r.both(cache, fmt, t, q, A, B, "", keep=True)
                                    rows.append({"fmt": fmt, "topic": t, "pair": pi, "alpha": al, "kind": kind,
                                                 "loc": loc, "s": sg, "q": q, "y": y, "mass": m,
                                                 "kl": kl(lp, ref[q][3])})
                json.dump({"stage": "card", "layer": LAYER, "rows": rows}, open(out_path, "w"))
            print(f"card: {fmt} topic {t} done, {time.time() - t0:.0f} s", flush=True)
    print("CARD DONE", flush=True)


def stage_reach(a):
    """Added after the base model's card failed (description, not deciding; notes/blind-mind-2026.md): does a
    model's concept vector move the answer at all when it is planted at the answer position itself (the last token
    of the chat, which the reply follows) rather than at a writer's sentence? N-SY and Q-SA, question T, no fact,
    pairs 1-6, stories 1-2, alpha 1/2/4, full passes one option order at a time."""
    r = Runner(a.model); V = load_vectors(a.out); torch = r.torch
    rows = []; t0 = time.time()
    for fmt in CARD_FORMATS:
        for t in CARD_TOPICS:
            pre = r.fprefix_text(fmt, t)
            for pi in CARD_PAIRS:
                A, B = PAIRS[pi]
                ids = {}
                for o, (w1, w2) in enumerate(((A, B), (B, A))):
                    ids[o] = r.tok(pre + r.fcont(fmt, t, qtext(fmt, "T").format(w1=w1, w2=w2)),
                                   add_special_tokens=False).input_ids
                for al in (0,) + CARD_ALPHAS:
                    for sg in ((1, -1) if al else (0,)):
                        ys = []
                        for o in (0, 1):
                            if al:
                                u = vec(V, word_for(sg, (A, B)), al)
                                r.add = (LAYER, [(u, [len(ids[o]) - 1])])
                            lp = r.last_logp(torch.tensor([ids[o]]))
                            r.add = None
                            ys.append(r.ymass(lp, A, B)[0])
                        rows.append({"fmt": fmt, "topic": t, "pair": pi, "alpha": al, "s": sg, "y": sum(ys) / 2})
            print(f"reach: {fmt} topic {t} done, {time.time() - t0:.0f} s", flush=True)
    json.dump({"stage": "reach", "layer": LAYER, "rows": rows}, open(Path(a.out) / "reach.json", "w"))
    for fmt in CARD_FORMATS:
        for al in CARD_ALPHAS:
            per = []
            for pi in CARD_PAIRS:
                z = [x for x in rows if x["fmt"] == fmt and x["alpha"] == al and x["pair"] == pi]
                ya = [x["y"] for x in z if x["s"] == 1]; yb = [x["y"] for x in z if x["s"] == -1]
                per.append((sum(ya) / len(ya) - sum(yb) / len(yb)) / 2)
            m = sum(per) / len(per)
            se = (sum((p - m) ** 2 for p in per) / (len(per) - 1) / len(per)) ** 0.5
            print(f"reach {fmt} alpha {al}: slope {m:+.2f} (SE {se:.2f}); per pair " + " ".join(f"{p:+.2f}" for p in per))
    print("REACH DONE", flush=True)


def card_alpha(out):
    """The pre-registered rule: alpha* = 2 if N-SY's two own slopes (each answer <- its own writer's sentence) are
    both >= 0.3 at alpha 2 on the card; else 4 if they are there; else None (the model's injection arm is
    uninformative)."""
    rows = json.load(open(Path(out) / "card.json"))["rows"]
    def own(al, loc, q):
        z = [x for x in rows if x["fmt"] == "N-SY" and x["kind"] == "concept" and x["alpha"] == al and x["loc"] == loc
             and x["q"] == q]
        return slope(z, sorted({x["pair"] for x in z}))
    for al in (2.0, 4.0):
        if own(al, "T", "T") >= CARD_BAR and own(al, "S", "S") >= CARD_BAR:
            return al
    return None


def plan_rows(fmt, stage):
    """(arm, src, q) for a stage. src: whose fact ('T' the target as T names it, 'S' Sam, 'R' Riley by name; for
    injections 'T' and 'S' are the sentences)."""
    R = fmt.startswith("R")
    if stage == "control":
        p = [("text", "T", "T"), ("text", "S", "S"), ("inj", "T", "T"), ("inj", "S", "S")]
        if R:
            p += [("text", "R", "R"), ("inj", "T", "R")]
    else:
        p = [("text", "S", "T"), ("text", "T", "S"), ("inj", "S", "T"), ("inj", "T", "S"),
             ("none", None, "T"), ("none", None, "S")]
        if R:
            p += [("text", "S", "R"), ("inj", "S", "R"), ("none", None, "R")]
    return p


def run_rows(r, V, alpha, fmt, t, pi, plan, rows):
    A, B = PAIRS[pi]
    s, ids, pT, pS = r.fprefix(fmt, t)
    pos = {"T": pT, "S": pS}
    base = None
    for arm, src, q in plan:
        if arm in ("text", "none"):
            if base is None:
                base = r.run_prefix(ids)
            for sg in ((1, -1) if arm == "text" else (0,)):
                facts = fact(fmt, src, word_for(sg, (A, B))) if sg else ""
                y, m, od = r.both(base, fmt, t, q, A, B, facts)
                rows.append({"fmt": fmt, "arm": arm, "topic": t, "pair": pi, "q": q, "src": src, "s": sg,
                             "y": y, "mass": m, "order_diff": od, "words": len(facts.split())})
    inj = {}
    for arm, src, q in plan:
        if arm != "inj":
            continue
        for sg in (1, -1):
            if (src, sg) not in inj:
                inj[(src, sg)] = r.run_prefix(ids, (LAYER, [(vec(V, word_for(sg, (A, B)), alpha), pos[src])]))
            y, m, od = r.both(inj[(src, sg)], fmt, t, q, A, B, "")
            rows.append({"fmt": fmt, "arm": "inj", "topic": t, "pair": pi, "q": q, "src": src, "s": sg,
                         "y": y, "mass": m, "order_diff": od, "words": 0})


def run_stage(a, name):
    alpha = card_alpha(a.out)
    if alpha is None:
        print("card: no alpha passes; the injection rows are run at alpha 2 and read as uninformative")
        alpha = 2.0
    r = Runner(a.model); V = load_vectors(a.out)
    out_path = Path(a.out) / f"{name}.json"
    rows = json.load(open(out_path))["rows"] if out_path.exists() else []
    have = {(x["fmt"], x["topic"], x["pair"]) for x in rows}
    t0 = time.time()
    print(f"{name}: alpha {alpha}", flush=True)
    for fmt in FORMATS:
        for t in range(len(TOPICS)):
            for pi in range(len(PAIRS)):
                if (fmt, t, pi) in have:
                    continue
                run_rows(r, V, alpha, fmt, t, pi, plan_rows(fmt, name), rows)
            json.dump({"stage": name, "layer": LAYER, "alpha": alpha, "rows": rows}, open(out_path, "w"))
            print(f"{name}: {fmt} topic {t} done, {time.time() - t0:.0f} s", flush=True)
    print(f"{name.upper()} DONE", flush=True)


def stage_control(a):
    run_stage(a, "control")


def stage_test(a):
    run_stage(a, "test")


# ----------------------------------------------------------------------------- analysis

def slope(rows, pairs, **fix):
    by = {}
    for x in rows:
        if all(x[k] == v for k, v in fix.items()) and x["s"] != 0:
            by.setdefault(x["pair"], {1: [], -1: []})[x["s"]].append(x["y"])
    per = []
    for p in pairs:
        h, l = by[p][1], by[p][-1]
        per.append((sum(h) / len(h) - sum(l) / len(l)) / 2)
    return sum(per) / len(per)


def boot_draws(n_pairs, n=2000, seed=29):
    rnd = random.Random(seed)
    return [[rnd.randrange(n_pairs) for _ in range(n_pairs)] for _ in range(n)]


def ci(vals):
    v = sorted(vals); n = len(v)
    return [v[int(0.025 * n)], v[int(0.975 * n) - 1]]


def own_src(arm, q):
    """The fact that is q's own referent's: in text, the fact naming q's referent; injected, the referent's sentence
    (Riley's sentence is the target's)."""
    if q == "S":
        return "S"
    return "R" if (arm == "text" and q == "R") else "T"


def bor_src(q):
    return "T" if q == "S" else "S"


def load_rows(out):
    rows = []
    for name in ("control", "test"):
        f = Path(out) / f"{name}.json"
        if f.exists():
            rows += json.load(open(f))["rows"]
    return rows


_PER = {}


def per_pair(rows, fmt, arm, q, src):
    """The slope of each pair (half the A-minus-B difference, averaged over stories), computed once per row set."""
    key = (id(rows), fmt, arm, q, src)
    if key not in _PER:
        z = [x for x in rows if x["fmt"] == fmt and x["arm"] == arm and x["q"] == q and x["src"] == src]
        _PER[key] = {p: slope(z, [p]) for p in sorted({x["pair"] for x in z})}
    return _PER[key]


def terms_for(rows, arm, pair_name, q, ps):
    """The own-referent and borrowing slopes of question q in the pair of formats (f2: target second, f1: target
    first), over the (possibly resampled) pairs ps; directions are applied by the caller."""
    f2, f1 = PAIRS_OF_FORMATS[pair_name]
    m = lambda f, src: sum(per_pair(rows, f, arm, q, src)[p] for p in ps) / len(ps)
    own = {f: m(f, own_src(arm, q)) for f in (f2, f1)}
    bor = {f: m(f, bor_src(q)) for f in (f2, f1)}
    return own, bor


def summarize_model(out, label):
    rows = load_rows(out)
    P = len(PAIRS); allp = list(range(P)); draws = boot_draws(P)
    card = card_summary(out)
    alpha = json.load(open(Path(out) / "control.json"))["alpha"] if (Path(out) / "control.json").exists() else None
    res = {"label": label, "alpha": alpha, "card": card, "arms": {}}
    have_test = (Path(out) / "test.json").exists()
    for arm in ("text", "inj"):
        A = {"controls": {}, "terms": {}}
        for fmt in FORMATS:
            for q in questions(fmt):
                z = [x for x in rows if x["fmt"] == fmt and x["arm"] == arm and x["q"] == q and x["src"] == own_src(arm, q)]
                if len({x["pair"] for x in z}) < P:
                    continue
                o = slope(z, allp)
                A["controls"][f"{fmt}:{q}"] = {"own": o, "dir": 1 if o > 0 else -1, "pass": abs(o) >= BAR[arm]}
        if have_test:
            for pn, (f2, f1) in PAIRS_OF_FORMATS.items():
                for q in questions(f2):
                    c2, c1 = A["controls"].get(f"{f2}:{q}"), A["controls"].get(f"{f1}:{q}")
                    if not c2 or not c1:
                        continue
                    agree = c2["dir"] == c1["dir"]; d = c2["dir"]
                    def dec(ps):
                        own, bor = terms_for(rows, arm, pn, q, ps)
                        g2, g1 = d * (own[f2] - bor[f2]), d * (own[f1] - bor[f1])
                        later = (g2 - g1) / 2 if q != "S" else (g1 - g2) / 2   # Sam is the later writer in f1
                        ow = (d * own[f2] + d * own[f1]) / 2
                        return {"owner": (g2 + g1) / 2, "position": later, "own": ow,
                                "bor": (d * bor[f2] + d * bor[f1]) / 2,
                                "index": (g2 + g1) / 2 / ow if ow > 0 else float("nan")}
                    v = dec(allp); bs = [dec(ps) for ps in draws]
                    floor = 0.1 * (abs(c2["own"]) + abs(c1["own"])) / 2
                    A["terms"][f"{pn}:{q}"] = {k: [v[k]] + ci([b[k] for b in bs]) for k in v}
                    A["terms"][f"{pn}:{q}"].update({"floor": floor, "dirs_agree": agree,
                                                    "controls_pass": c2["pass"] and c1["pass"]})
            # the word, with the turn and the prefix fixed: owner(Riley's) - owner(your), R formats
            if "riley:R" in A["terms"] and "riley:T" in A["terms"]:
                dR = A["controls"]["R-SY:R"]["dir"]; dT = A["controls"]["R-SY:T"]["dir"]
                def word(ps):
                    oR, bR = terms_for(rows, arm, "riley", "R", ps); oT, bT = terms_for(rows, arm, "riley", "T", ps)
                    gR = sum(dR * (oR[f] - bR[f]) for f in ("R-SY", "R-YS")) / 2
                    gT = sum(dT * (oT[f] - bT[f]) for f in ("R-SY", "R-YS")) / 2
                    return gR - gT
                floor = 0.1 * sum(abs(A["controls"][k]["own"]) for k in ("R-SY:R", "R-YS:R", "R-SY:T", "R-YS:T")) / 4
                A["terms"]["word"] = {"value": [word(allp)] + ci([word(ps) for ps in draws]), "floor": floor}
        res["arms"][arm] = A
    if have_test:
        z = [x["mass"] for x in rows]
        res["mass"] = {f: {"mean": sum(x["mass"] for x in rows if x["fmt"] == f) / max(1, sum(1 for x in rows if x["fmt"] == f)),
                           "min": min(x["mass"] for x in rows if x["fmt"] == f)} for f in FORMATS}
        res["mass_all"] = {"mean": sum(z) / len(z), "min": min(z)}
    return res, rows


def card_summary(out):
    f = Path(out) / "card.json"
    if not f.exists():
        return None
    rows = json.load(open(f))["rows"]
    res = {}
    for fmt in CARD_FORMATS:
        for al in CARD_ALPHAS:
            z = [x for x in rows if x["fmt"] == fmt and x["alpha"] == al]
            ps = sorted({x["pair"] for x in z})
            if not ps:
                continue
            c = lambda kind, loc, q: slope([x for x in z if x["kind"] == kind and x["loc"] == loc and x["q"] == q], ps)
            kl = lambda kind, q: sum(x["kl"] for x in z if x["kind"] == kind and x["q"] == q) / max(1, sum(1 for x in z if x["kind"] == kind and x["q"] == q))
            none = {(x["topic"], x["pair"]): x["y"] for x in rows if x["fmt"] == fmt and x["kind"] == "none" and x["q"] == "N"}
            nco = lambda kind: sum(abs(x["y"] - none[(x["topic"], x["pair"])]) for x in z if x["kind"] == kind and x["q"] == "N") / max(1, sum(1 for x in z if x["kind"] == kind and x["q"] == "N"))
            res[f"{fmt}:{al}"] = {"own_T": c("concept", "T", "T"), "own_S": c("concept", "S", "S"),
                                  "gauss_T": c("gauss", "T", "T"), "kl_concept": kl("concept", "T"),
                                  "kl_gauss": kl("gauss", "T"), "kl_ratio": kl("gauss", "T") / max(1e-9, kl("concept", "T")),
                                  "nco_shift_concept": nco("concept"), "nco_shift_gauss": nco("gauss"),
                                  "kl_nco_concept": kl("concept", "N")}
    try:
        res["alpha_star"] = card_alpha(out)
    except Exception:
        res["alpha_star"] = None
    V = Path(out) / "vectors.pt"
    if V.exists():
        res["rms"] = {str(k): v for k, v in wt.load_vectors(out)["rms"].items()}
    return res


def self_gap(M, rows, arm, ps):
    """Ownership index of the answer about "you" minus that of the answer about Sam, both in the native pair
    (index = owner term / own slope: 1 = reads only its own referent's state, 0 = borrows as much as it owns)."""
    out = []
    for q in ("T", "S"):
        d = M["arms"][arm]["controls"][f"N-SY:{q}"]["dir"]
        o, b = terms_for(rows, arm, "native", q, ps)
        ow = sum(d * (o[f] - b[f]) for f in ("N-SY", "N-YS")) / 2
        own = sum(d * o[f] for f in ("N-SY", "N-YS")) / 2
        out.append(ow / own if own > 0 else float("nan"))
    return out[0] - out[1]


def verdicts(I, B, rows_I, rows_B):
    """The pre-registered verdicts (notes/blind-mind-2026.md)."""
    out = {}
    P = len(PAIRS); allp = list(range(P)); draws = boot_draws(P)
    def c(term):   # counts: interval above 0 and value at least the floor
        return term["owner"][1] > 0 and term["owner"][0] >= term["floor"]
    for arm in ("text", "inj"):
        V = {}
        for lab, M in (("instruct", I), ("base", B)):
            if M is None or arm not in M["arms"] or not M["arms"][arm]["terms"]:
                continue
            T = M["arms"][arm]["terms"]
            ok = lambda k: T[k]["controls_pass"] and T[k]["dirs_agree"]
            gate = "native:S" in T and ok("native:S") and c(T["native:S"])   # Sam's answer, in the same chats
            if M.get("mass") and min(M["mass"][f]["mean"] for f in ("N-SY", "N-YS")) < 0.05:
                gate = False   # the pre-registered mass rule
            V[f"{lab}:gate"] = "SEES OWNERSHIP" if gate else "BLIND"
            tY = T.get("native:T")
            if tY and ok("native:T"):
                if c(tY):
                    v = "ASKS WHOSE"
                elif tY["owner"][2] < 0:
                    v = "REVERSED"
                else:
                    v = "DOESN'T ASK"
                V[f"{lab}:you"] = v if gate else f"uninformative (gate BLIND; would read {v})"
                if arm == "inj":
                    n = "NEARNESS" if tY["position"][1] > 0 and tY["position"][0] >= tY["floor"] else "NO NEARNESS"
                    V[f"{lab}:nearness"] = n if gate else f"uninformative (gate BLIND; would read {n})"
            tS = T.get("native:S")
            if tY and tS and ok("native:T") and ok("native:S"):
                sel = lambda ps, M=M, rows=(rows_I if lab == "instruct" else rows_B): self_gap(M, rows, arm, ps)
                g = [sel(allp)] + ci([sel(ps) for ps in draws])
                v = ("SELF PRIVILEGED" if g[1] > 0 and g[0] >= 0.1 else "SELF DEFICIT" if g[2] < 0 and -g[0] >= 0.1
                     else "NO GAP")
                V[f"{lab}:self_gap"] = {"value": g, "floor": 0.1,
                                        "verdict": v if gate else f"uninformative (gate BLIND; would read {v})"}
            tR, tRT = T.get("riley:R"), T.get("riley:T")
            if tR and tRT and ok("riley:R") and ok("riley:T"):
                w = T["word"]["value"]; wc = w[1] > 0 and w[0] >= T["word"]["floor"]
                if c(tR) and wc:
                    v = "WORD"
                elif c(tR) and c(tRT):
                    v = "NAME"
                elif not c(tR) and w[2] >= 0:
                    v = "TURN"
                else:
                    v = "OTHER"
                V[f"{lab}:turn_or_word"] = v if gate else f"uninformative (gate BLIND; would read {v})"
            if arm == "inj" and M.get("card") and M["card"].get("alpha_star") is None:
                # the pre-registered dose rule: no alpha passed the card, so every injection term is uninformative
                # (added after the base model's card, before its test ran)
                for k in [k for k in V if k.startswith(lab + ":")]:
                    if isinstance(V[k], dict):
                        V[k]["verdict"] = f"uninformative (no alpha passed the card; would read {V[k]['verdict']})"
                    else:
                        V[k] = f"uninformative (no alpha passed the card; would read {V[k]})"
        # the cross-model term: owner(you, native, base) - owner(you, native, instruct), paired over pairs
        if I and B and arm in I["arms"] and arm in B["arms"] and "native:T" in I["arms"][arm]["terms"] \
                and "native:T" in B["arms"][arm]["terms"]:
            dI = I["arms"][arm]["controls"]["N-SY:T"]["dir"]; dB = B["arms"][arm]["controls"]["N-SY:T"]["dir"]
            def own_you(rows, d, ps, index=True):
                o, b = terms_for(rows, arm, "native", "T", ps)
                ow = sum(d * (o[f] - b[f]) for f in ("N-SY", "N-YS")) / 2
                own = sum(d * o[f] for f in ("N-SY", "N-YS")) / 2
                return (ow / own if own > 0 else float("nan")) if index else ow
            tr = lambda ps: own_you(rows_B, dB, ps) - own_you(rows_I, dI, ps)
            val = [tr(allp)] + ci([tr(ps) for ps in draws])
            raw = lambda ps: own_you(rows_B, dB, ps, False) - own_you(rows_I, dI, ps, False)
            V["training_raw_owner_difference"] = [raw(allp)] + ci([raw(ps) for ps in draws])
            floor = 0.1
            if val[1] > 0 and val[0] >= floor:
                v = "TRAINING REMOVED"
            elif val[2] < 0 and -val[0] >= floor:
                v = "TRAINING ADDED"
            else:
                v = "NO MEASURABLE CHANGE"
            gates = V.get("instruct:gate") == "SEES OWNERSHIP" and V.get("base:gate") == "SEES OWNERSHIP"
            V["training"] = {"value": val, "floor": floor,
                             "verdict": v if gates else f"uninformative (a gate isn't SEES OWNERSHIP; would read {v})"}
            gI, gB = V.get("instruct:gate"), V.get("base:gate")
            V["ownership_trained"] = ("uninformative" if str(gI).startswith("uninf") or str(gB).startswith("uninf") else
                                      "OWNERSHIP IS TRAINED" if gI == "SEES OWNERSHIP" and gB == "BLIND" else
                                      "IN BOTH" if gI == gB == "SEES OWNERSHIP" else
                                      "NEITHER" if gI == gB == "BLIND" else "BASE ONLY")
        out[arm] = V
    return out


def fmt_term(name, t):
    if "owner" in t:
        return (f"{name}: owner {t['owner'][0]:+.2f} [{t['owner'][1]:+.2f}, {t['owner'][2]:+.2f}], position "
                f"{t['position'][0]:+.2f} [{t['position'][1]:+.2f}, {t['position'][2]:+.2f}] (own {t['own'][0]:+.2f}, "
                f"borrow {t['bor'][0]:+.2f}; floor {t['floor']:.2f}{'' if t['dirs_agree'] else '; DIRECTIONS DISAGREE'}"
                f"{'' if t['controls_pass'] else '; CONTROL FAILED'})")
    return f"{name}: {t['value'][0]:+.2f} [{t['value'][1]:+.2f}, {t['value'][2]:+.2f}] (floor {t['floor']:.2f})"


def stage_summary(a):
    I, rI = summarize_model(a.out, "instruct")
    B, rB = summarize_model(a.base_out, "base") if a.base_out else (None, None)
    for M in (I, B):
        if M is None:
            continue
        print(f"\n=== {M['label']} (alpha {M['alpha']})")
        if M["card"]:
            for k, v in M["card"].items():
                if isinstance(v, dict) and "own_T" in v:
                    print(f"  card {k}: own_T {v['own_T']:+.2f} own_S {v['own_S']:+.2f} gauss_T {v['gauss_T']:+.2f}; "
                          f"KL concept {v['kl_concept']:.3f} gauss {v['kl_gauss']:.3f} (ratio {v['kl_ratio']:.2f}); "
                          f"NCO shift concept {v['nco_shift_concept']:.3f} gauss {v['nco_shift_gauss']:.3f}")
            print(f"  card: alpha* = {M['card'].get('alpha_star')}; median residual norms {M['card'].get('rms')}")
        for arm, A in M["arms"].items():
            print(f"  [{arm}] controls: " + "; ".join(f"{k} {v['own']:+.2f}{'' if v['pass'] else ' FAIL'}"
                                                     for k, v in A["controls"].items()))
            for k, t in A["terms"].items():
                print(f"  [{arm}] " + fmt_term(k, t))
        if "mass" in M:
            print("  mass:", {k: (round(v["mean"], 3), round(v["min"], 3)) for k, v in M["mass"].items()})
    res = {"instruct": I, "base": B}
    if I and B and "terms" in I["arms"].get("text", {}) and I["arms"]["text"]["terms"] and B["arms"]["text"]["terms"]:
        res["verdicts"] = verdicts(I, B, rI, rB)
        print("\n=== verdicts")
        for arm, V in res["verdicts"].items():
            for k, v in V.items():
                print(f"  [{arm}] {k}: {v if not isinstance(v, dict) else v['verdict'] + ' ' + str([round(x, 3) for x in v['value']])}")
    json.dump(res, open(Path(a.out) / "summary.json", "w"), indent=1)


def stage_export(a):
    res = {"pairs": PAIRS, "topics": TOPICS, "formats": FORMATS, "layer": LAYER,
           "questions": {f: questions(f) for f in FORMATS}, "nco": NCO,
           "example_chats": {f: messages(f, 0, "{facts}{question}") for f in FORMATS}}
    rnd = lambda rows: [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in x.items()} for x in rows]
    for lab, out in (("instruct", a.out), ("base", a.base_out)):
        res[lab] = {}
        for name in ("card", "control", "test"):
            f = Path(out) / f"{name}.json"
            if f.exists():
                d = json.load(open(f))
                res[lab][name] = {"alpha": d.get("alpha"), "rows": rnd(d["rows"])}
    if (Path(a.out) / "summary.json").exists():
        res["summary"] = json.load(open(Path(a.out) / "summary.json"))
    json.dump(res, open(a.file, "w"), separators=(",", ":"))
    print("wrote", a.file)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["check", "vectors", "card", "reach", "control", "test", "summary", "export"])
    ap.add_argument("--model"); ap.add_argument("--out", required=True); ap.add_argument("--base-out")
    ap.add_argument("--file"); ap.add_argument("--quick", action="store_true", help="check: skip the mass table")
    a = ap.parse_args()
    {"check": stage_check, "vectors": stage_vectors, "card": stage_card, "reach": stage_reach, "control": stage_control,
     "test": stage_test, "summary": stage_summary, "export": stage_export}[a.stage](a)


if __name__ == "__main__":
    main()
