"""A frame the base model can read: the owner/nearness split in plain narrated text (session 30, 2026-10-29).

Essay 028 put essay 027's instrument to Qwen 2.5 3B base and Instruct inside Qwen's chat format. In the assistant every
control passed; in the base model the chat frame failed its controls (5 of 14 stated, 0 of 14 planted), so every base
verdict was uninformative. Below the bar, the base model's answers in words already had the assistant's shape (the
answer about Sam asked whose thought it was, the answer about "you" didn't). This tool asks the same question in a
frame the base model reads as ordinary text: no chat template, a two-writer story narrated in the first person ("Sam
and I wrote... Then I wrote..."), in the second person ("Sam and you wrote..."), or about a named writer ("Sam and
Alex wrote..."), each in both orders of writing, and an answer the text itself begins ("The word on my mind was").
gavinagent (The Colony, 2026-10-29) asked for exactly this: a version of the story the base model passes. Concept
vectors for each model come from plain text too, in two new kinds beside essay 026's recipe: a "native" state the
model forms itself from a description that never names the word (happyfool_beatslonely, rStation post 21) and the
word's own state in carrier sentences (their token-replay control).

Formats (the same twelve word pairs and six stories as session 29; the two sentences have the same token count):
  P-SI  "Sam and I wrote ... Sam wrote: "<first>" Then I wrote: "<second>""         target "I", writes second
  P-IS  "... I wrote: "<first>" Then Sam wrote: "<second>""                          target "I", writes first
  P-SY  / P-YS   the same with "you"
  P-SA  / P-AS   the same with Alex (a named writer in the target's place)
then a blank line, an optional stated fact, the question and the start of its answer:
  T  "Which word was on my mind while I was writing my sentence, A or B? The word on my mind was \""
     (your mind / you were writing your sentence / The word on your mind was; Alex's ... their ...)
  S  "Which word was on Sam's mind while Sam was writing their sentence, A or B? The word on Sam's mind was \""
     (the opening quotation mark is part of the prompt: without it the base model's most likely next token is the
     quotation mark, and the two words' mass at the next token was 0.22-0.33; with it 0.63-0.90; check stage)
Arms, one fact at a time: text ("While I was writing my sentence, I was thinking about A." or Sam's, the target's
equivalents for you and Alex; ten words each) and inj (a concept vector added at layer 18 at the tokens of one writer's
sentence). Measure: y = log P(A) - log P(B) at the next token, each word over its four single-token forms, both option
orders averaged (session 29's measure), at the token after the quotation mark. Slopes, owner and position terms, the ownership index and the bootstrap are
session 29's (tools/blind_mind.py), with pairs of formats I (P-SI, P-IS), you (P-SY, P-YS) and Alex (P-SA, P-AS).

Stages:
  check     tokenization, equal spans, cached vs full pass (bf16 and float32), answer mass, timing, per model
  textctl   the stated-thought positive controls (own-referent text rows, all formats); run in the check stage,
            before anything is registered (session 29's lesson)
  vectors   concept vectors of three kinds (native, word, recipe) at layers 9/18/27, median residual norms over the
            P-SI prefixes, cosines between kinds
  card      the calibration card for P-SI and P-SA: kinds native/word/recipe and a norm-matched Gaussian, alpha 1/2/4;
            own slopes, KL at the readout, the shift of an unrelated question; it fixes each model's (kind, alpha)
  injctl    the planted positive controls at the card's choice
  test      the borrowing rows and the uninjected rows, both arms
  summary   controls, directions, owner and position terms, verdicts (both models)
  export    one JSON file with every row and the summary

Usage:
  python3 tools/first_person.py check   --model DIR --out DIR
  python3 tools/first_person.py textctl --model DIR --out DIR
  python3 tools/first_person.py vectors --model DIR --out DIR
  python3 tools/first_person.py card    --model DIR --out DIR
  python3 tools/first_person.py injctl  --model DIR --out DIR
  python3 tools/first_person.py test    --model DIR --out DIR
  python3 tools/first_person.py summary --out I_DIR --base-out B_DIR
  python3 tools/first_person.py export  --out I_DIR --base-out B_DIR --file notes/data/first-person-session30.json
The pre-registration is in notes/first-person-2026.md. Needs torch and transformers (bf16 on a CPU with AMX).
"""
import argparse, copy, json, math, random, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blind_mind as bm   # noqa: E402  (session 29: pairs, stories, slopes, bootstrap)

PAIRS, TOPICS = bm.PAIRS, bm.TOPICS
LAYER = 18
FORMATS = {   # name: (target label, target writes first?)
    "P-SI": ("I", False), "P-IS": ("I", True),
    "P-SY": ("you", False), "P-YS": ("you", True),
    "P-SA": ("Alex", False), "P-AS": ("Alex", True),
}
PAIRS_OF_FORMATS = {"I": ("P-SI", "P-IS"), "you": ("P-SY", "P-YS"), "Alex": ("P-SA", "P-AS")}
WHO = {   # label: (subject, capitalized subject, "was/were", possessive, "<X>'s mind")
    "I": ("I", "I", "was", "my", "my mind"),
    "you": ("you", "You", "were", "your", "your mind"),
    "Alex": ("Alex", "Alex", "was", "their", "Alex's mind"),
    "Sam": ("Sam", "Sam", "was", "their", "Sam's mind"),
}
NCO = "Which of these two numbers is larger, {w1} or {w2}? The larger number is"   # an unrelated question
NCO_WORDS = bm.NCO_WORDS
KINDS = ("native", "word", "recipe")
CARD_ALPHAS, CARD_PAIRS, CARD_TOPICS, CARD_FORMATS = (1.0, 2.0, 4.0), range(6), range(2), ("P-SI", "P-SA")
CARD_ORDER = [("native", 2.0), ("word", 2.0), ("recipe", 2.0), ("native", 4.0), ("word", 4.0), ("recipe", 4.0)]
CARD_BAR = 0.3
BAR = {"text": 0.3, "inj": 0.3}   # session 29: text 1.0; changed after the base model's stated controls (notes)
OLD_BAR = {"text": 1.0, "inj": 0.3}

# Two descriptions per word that never name it (happyfool_beatslonely's "native state", rStation post 21): the
# model forms its own state for the concept from them. Checked at run time: no token of any pair word's four forms
# occurs in any description's tokens.
DESCRIPTIONS = {
    "ghost": ["the pale spirit of a dead person that haunts an old house",
              "a see-through figure in a white sheet that floats through walls at night"],
    "salt": ["the white crystals people sprinkle on food to make it taste less bland",
             "the mineral left behind when seawater dries in the sun"],
    "anchor": ["the heavy iron hook a ship drops to the seabed to stay in place",
               "the metal weight on a chain that keeps a boat from drifting away"],
    "cake": ["the sweet baked dessert with frosting and candles at a birthday",
             "a soft round sponge layered with cream that is cut into pieces"],
    "tower": ["the tall narrow brick building that rises high above a castle wall",
              "a very tall structure with stairs winding up to a lookout at the top"],
    "fox": ["the small red wild animal with a bushy tail and pointed ears that sneaks into henhouses",
            "the clever orange woodland creature with a white tip on its tail"],
    "bell": ["the hollow metal object in a church steeple that rings when it swings",
             "the brass cup-shaped thing that makes a clanging sound when it is struck"],
    "sand": ["the tiny grains that cover a beach and get into your shoes",
             "the dry yellow grains that make up the dunes of a desert"],
    "pizza": ["the flat round Italian dish of baked dough topped with tomato and melted cheese",
              "the cheesy pie delivered in a square cardboard box and eaten in slices"],
    "king": ["the man who wears a crown and rules a country from his throne",
             "the royal ruler of a kingdom who sits beside the queen"],
    "coin": ["the small round piece of metal money you drop into a slot",
             "the flat metal disc with a face on one side, used as pocket change"],
    "leaf": ["the flat green part of a plant that turns orange and falls in autumn",
             "the thin green blade that grows from a twig and catches sunlight"],
    "hat": ["the thing you wear on your head to keep the sun off, with a brim",
            "the felt covering a gentleman lifts off his head to greet someone"],
    "ice": ["frozen water, hard and cold, that floats in a drink",
            "the slippery frozen surface of a pond in the coldest months"],
    "bird": ["the feathered animal with wings and a beak that sings in the morning",
             "a small creature with feathers that builds a nest and lays eggs"],
    "map": ["the folded paper drawing of roads and towns you use to find your way",
            "a flat picture of a country showing rivers, borders and cities"],
    "tree": ["the tall plant with a wooden trunk and branches that grows in a forest",
             "the big woody plant with bark and roots that gives shade in a park"],
    "engine": ["the machine under the hood of a car that burns fuel to make it move",
               "the roaring motor that powers a train or a truck"],
    "cat": ["the small furry pet that purrs, chases mice and has whiskers",
            "the house animal that meows and likes to sleep in the sun"],
    "stone": ["a hard piece of rock you might pick up from the ground",
              "the small grey pebble that skips across the water when thrown"],
    "wind": ["the moving air that blows the clouds and bends the grass",
             "the invisible current of air that flaps flags and makes a kite fly"],
    "nut": ["the hard-shelled seed a squirrel buries for the cold months",
            "a small oily kernel inside a hard shell that you crack open"],
    "dog": ["the loyal pet that barks, wags its tail and fetches sticks",
            "the four-legged animal that guards the house and goes for walks on a leash"],
    "star": ["a tiny point of light that twinkles in the night sky",
             "the distant burning sun that looks like a bright speck at night"],
}
NATIVE_CARRIER = "I kept thinking about {d}."
WORD_CARRIERS = ["I kept thinking about the {w}.", "There was a {w} in the old picture.",
                 "She wrote the word {w} on the board."]


def intro(fmt, t):
    topic, first, second = TOPICS[t]
    label, target_first = FORMATS[fmt]
    subj, cap = WHO[label][0], WHO[label][1]
    head = f"Sam and {subj} wrote a short story about {topic} together, one sentence each. "
    if target_first:
        return head + f"{cap} wrote: \"{first}\" Then Sam wrote: \"{second}\"\n\n"
    return head + f"Sam wrote: \"{first}\" Then {subj} wrote: \"{second}\"\n\n"


def who_of(fmt, q):
    return "Sam" if q == "S" else FORMATS[fmt][0]


def qtext(fmt, q):
    if q == "N":
        return NCO
    subj, _, be, poss, mind = WHO[who_of(fmt, q)]
    return (f"Which word was on {mind} while {subj} {be} writing {poss} sentence, {{w1}} or {{w2}}? "
            f"The word on {mind} was \"")


def fact(fmt, who, w):
    """who: 'S' (Sam) or 'T' (the target)."""
    subj, cap, be, poss, _ = WHO["Sam" if who == "S" else FORMATS[fmt][0]]
    return f"While {subj} {be} writing {poss} sentence, {subj} {be} thinking about {w}. "


def questions(fmt):
    return {q: qtext(fmt, q) for q in ("T", "S")}


class Runner(bm.Runner):
    """Session 29's runner (hooks, float32 readout, batched option orders) on plain text: no chat template."""

    def __init__(self, model_dir, dtype="bf16"):
        super().__init__(model_dir, dtype)
        for d in DESCRIPTIONS.values():
            for x in d:
                ids = set(self.tok.encode(" " + x, add_special_tokens=False))
                for w, wi in self.word_ids.items():
                    if w in NCO_WORDS:
                        continue
                    assert not ids & set(wi), (x, w)
        assert set(DESCRIPTIONS) == {w for p in PAIRS for w in p}

    def fprefix(self, fmt, t):
        s = intro(fmt, t)
        _, first, second = TOPICS[t]
        enc = self.tok(s, return_offsets_mapping=True, add_special_tokens=False)
        offs = enc["offset_mapping"]
        def span(text, start_at):
            a = s.index(text, start_at); b = a + len(text)
            return [k for k, (x, y) in enumerate(offs) if x < b and y > a], b
        p1, end1 = span(first, 0)
        p2, _ = span(second, end1)
        target_first = FORMATS[fmt][1]
        pos_T, pos_S = (p1, p2) if target_first else (p2, p1)
        return s, enc["input_ids"], pos_T, pos_S

    def fprefix_text(self, fmt, t):
        return intro(fmt, t)

    def fcont(self, fmt, t, tail):
        return tail

    def both(self, cache, fmt, t, q, A, B, facts, keep=False):
        torch = self.torch
        Q = qtext(fmt, q)
        c1 = self.tok(facts + Q.format(w1=A, w2=B), add_special_tokens=False).input_ids
        c2 = self.tok(facts + Q.format(w1=B, w2=A), add_special_tokens=False).input_ids
        assert len(c1) == len(c2), (fmt, q, A, B)
        kv = copy.deepcopy(cache); kv.batch_repeat_interleave(2)
        with torch.no_grad():
            out = self.model.model(input_ids=torch.tensor([c1, c2]), past_key_values=kv, use_cache=True)
            lp = torch.log_softmax(out.last_hidden_state[:, -1].float() @ self.W32.T, -1)
        lp1, lp2 = lp[0], lp[1]
        y1, m1 = self.ymass(lp1, A, B); y2, m2 = self.ymass(lp2, A, B)
        return ((y1 + y2) / 2, (m1 + m2) / 2, y1 - y2) + ((lp1,) if keep else ())


def load_vectors(out):
    import torch
    return torch.load(Path(out) / "vectors.pt")


def vec(V, kind, w, alpha):
    return V[kind][w][LAYER] * alpha * V["rms"][LAYER]


word_for = bm.word_for


# ----------------------------------------------------------------------------- stages that run the model

def stage_check(a):
    """Before the pre-registration: tokenization splits, equal spans, cached vs full pass (bf16 and float32), answer
    mass of every question uninjected on the first story, timing."""
    for dtype in ("bf16", "fp32"):
        r = Runner(a.model, dtype); torch = r.torch
        for w in ("cloud", "bridge"):
            r.word_ids[w] = sorted({r.tok.encode(v, add_special_tokens=False)[0]
                                    for v in (w, w.capitalize(), " " + w, " " + w.capitalize())})
        for fmt in FORMATS:
            if dtype == "bf16":
                for t in range(len(TOPICS)):
                    s, ids, pT, pS = r.fprefix(fmt, t)
                    assert len(pT) == len(pS), (fmt, t, len(pT), len(pS))
                    for q in ("T", "S", "N"):
                        for who in ("S", "T"):
                            c = fact(fmt, who, "cloud") + qtext(fmt, q).format(w1="cloud", w2="bridge")
                            whole = r.tok(s + c, add_special_tokens=False).input_ids
                            assert whole == ids + r.tok(c, add_special_tokens=False).input_ids, (fmt, t, q)
                    if t == 0:
                        txt = lambda p: r.tok.decode([ids[k] for k in p])
                        print(f"{fmt}: spans {[len(r.fprefix(fmt, u)[2]) for u in range(len(TOPICS))]} tokens; "
                              f"target '{txt(pT)}' | Sam's '{txt(pS)}'")
            s, ids, pT, pS = r.fprefix(fmt, 0)
            g = torch.Generator().manual_seed(30)
            u = torch.randn(r.model.config.hidden_size, generator=g); u = u / u.norm() * 2.0 * 72.0
            add = (LAYER, [(u, pT)])
            cache = r.run_prefix(ids, add)
            c = qtext(fmt, "T").format(w1="cloud", w2="bridge")
            y_c, m_c = r.ymass(r.dist(cache, c), "cloud", "bridge")
            cids = r.tok(c, add_special_tokens=False).input_ids
            r.add = add
            lp = r.last_logp(torch.tensor([ids + cids]))
            r.add = None
            y_f, _ = r.ymass(lp, "cloud", "bridge")
            y_b, _ = r.ymass(r.both(cache, fmt, 0, "T", "cloud", "bridge", "", keep=True)[3], "cloud", "bridge")
            print(f"[{dtype}] {fmt}: cached y {y_c:.4f}, in a batch of two {y_b:.4f}, full {y_f:.4f} "
                  f"(|diff| {abs(y_c - y_f):.4f}, {abs(y_b - y_f):.4f}); mass {m_c:.4f}", flush=True)
        if dtype == "bf16":
            base = {}
            for fmt in FORMATS:
                s, ids, pT, pS = r.fprefix(fmt, 0)
                cache = r.run_prefix(ids)
                for q in ("T", "S", "N"):
                    ms = []
                    for pi in range(len(PAIRS)):
                        A, B = PAIRS[pi] if q != "N" else NCO_WORDS
                        ms.append(r.both(cache, fmt, 0, q, A, B, "")[1])
                    base[(fmt, q)] = (sum(ms) / len(ms), min(ms))
                lp = r.dist(cache, qtext(fmt, "T").format(w1=PAIRS[0][0], w2=PAIRS[0][1]))
                top = lp.topk(6)
                print(f"  {fmt} T, top next tokens: " + ", ".join(f"{r.tok.decode([int(i)])!r} {math.exp(v):.2f}"
                                                                  for v, i in zip(top.values.tolist(), top.indices)))
            print("answer mass, first story, uninjected (mean, min over pairs):",
                  {f"{k[0]}:{k[1]}": (round(v[0], 3), round(v[1], 3)) for k, v in base.items()})
            s, ids, pT, pS = r.fprefix("P-SI", 0)
            t0 = time.time(); cache = r.run_prefix(ids); t1 = time.time()
            for _ in range(5):
                r.both(cache, "P-SI", 0, "T", *PAIRS[0], fact("P-SI", "S", "ghost"))
            print(f"timing: prefix {t1 - t0:.2f} s ({len(ids)} tokens), one question in both orders "
                  f"{(time.time() - t1) / 5:.2f} s")
            print("example:\n" + intro("P-SI", 0) + fact("P-SI", "S", "ghost") + qtext("P-SI", "T").format(
                w1="ghost", w2="salt") + " ...\n" + intro("P-YS", 0) + qtext("P-YS", "T").format(w1="ghost", w2="salt"))
        del r
        import gc; gc.collect()
    print("CHECK DONE")


def plan_rows(stage):
    if stage == "textctl":
        return [("text", "T", "T"), ("text", "S", "S")]
    if stage == "injctl":
        return [("inj", "T", "T"), ("inj", "S", "S")]
    return [("text", "S", "T"), ("text", "T", "S"), ("inj", "S", "T"), ("inj", "T", "S"),
            ("none", None, "T"), ("none", None, "S")]


def run_rows(r, V, choice, fmt, t, pi, plan, rows):
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
        kind, alpha = choice
        for sg in (1, -1):
            if (src, sg) not in inj:
                inj[(src, sg)] = r.run_prefix(ids, (LAYER, [(vec(V, kind, word_for(sg, (A, B)), alpha), pos[src])]))
            y, m, od = r.both(inj[(src, sg)], fmt, t, q, A, B, "")
            rows.append({"fmt": fmt, "arm": "inj", "topic": t, "pair": pi, "q": q, "src": src, "s": sg,
                         "y": y, "mass": m, "order_diff": od, "words": 0})


def run_stage(a, name):
    choice = None
    if name in ("injctl", "test"):
        choice, passed = card_choice(a.out)
        print(f"card: kind {choice[0]}, alpha {choice[1]}" + ("" if passed else
              " (no (kind, alpha) passed; run as description, every injection term uninformative)"), flush=True)
    r = Runner(a.model); V = load_vectors(a.out) if choice else None
    out_path = Path(a.out) / f"{name}.json"
    rows = json.load(open(out_path))["rows"] if out_path.exists() else []
    have = {(x["fmt"], x["topic"], x["pair"]) for x in rows}
    t0 = time.time()
    for fmt in FORMATS:
        for t in range(len(TOPICS)):
            for pi in range(len(PAIRS)):
                if (fmt, t, pi) in have:
                    continue
                run_rows(r, V, choice, fmt, t, pi, plan_rows(name), rows)
            json.dump({"stage": name, "layer": LAYER, "choice": choice, "rows": rows}, open(out_path, "w"))
            print(f"{name}: {fmt} topic {t} done, {time.time() - t0:.0f} s", flush=True)
    print(f"{name.upper()} DONE", flush=True)


def stage_textctl(a):
    run_stage(a, "textctl")


def stage_injctl(a):
    run_stage(a, "injctl")


def stage_test(a):
    run_stage(a, "test")


def stage_vectors(a):
    """Three kinds of concept vector per word, at layers 9, 18 and 27, each centred and unit-normed:
    native  the mean state over the tokens of a description that never names the word (two descriptions, averaged),
            minus the mean of all 24 words' native states (happyfool_beatslonely's natively formed state)
    word    the state at the word's own token in three carrier sentences (averaged), minus the 24-word mean
    recipe  essay 026's recipe: the last token of "Tell me about {word}." in the chat format, minus the mean over
            session 10's 30 neutral nouns (what sessions 27-29 planted)
    and the median residual norm per layer over the six P-SI prefixes."""
    r = Runner(a.model); torch = r.torch
    Ls = [9, 18, 27]
    def states(text, a0=None, n=0):
        """States at the tokens covering text[a0:a0+n] (the last token if a0 is None), mean over them."""
        enc = r.tok(text, return_offsets_mapping=True, add_special_tokens=False)
        with torch.no_grad():
            hs = r.model(torch.tensor([enc["input_ids"]]), output_hidden_states=True).hidden_states
        if a0 is None:
            pos = [len(enc["input_ids"]) - 1]
        else:
            b0 = a0 + n
            pos = [k for k, (x, y) in enumerate(enc["offset_mapping"]) if x < b0 and y > a0]
        return {L: hs[L + 1][0, pos].float().mean(0) for L in Ls}, len(pos)
    words = [w for p in PAIRS for w in p]
    raw = {"native": {}, "word": {}}
    for w in words:
        ns = [states(NATIVE_CARRIER.format(d=d), NATIVE_CARRIER.index("{d}"), len(d))[0] for d in DESCRIPTIONS[w]]
        raw["native"][w] = {L: sum(x[L] for x in ns) / len(ns) for L in Ls}
        wsts = []
        for c in WORD_CARRIERS:
            st, n = states(c.format(w=w), c.index("{w}"), len(w))   # by the template's position ("thinking" has "king")
            assert n == 1, (c, w)
            wsts.append(st)
        raw["word"][w] = {L: sum(x[L] for x in wsts) / len(wsts) for L in Ls}
    V = {"layers": Ls}
    for kind in ("native", "word"):
        mean = {L: torch.stack([raw[kind][w][L] for w in words]).mean(0) for L in Ls}
        V[kind] = {w: {L: (raw[kind][w][L] - mean[L]) / (raw[kind][w][L] - mean[L]).norm() for L in Ls} for w in words}
    chat = lambda w: r.tok.apply_chat_template([{"role": "user", "content": f"Tell me about {w}."}], tokenize=False,
                                               add_generation_prompt=True)
    base = [states(chat(w))[0] for w in bm.wt.BASELINE]
    mean = {L: torch.stack([b[L] for b in base]).mean(0) for L in Ls}
    V["recipe"] = {}
    for w in words:
        h = states(chat(w))[0]
        V["recipe"][w] = {L: (h[L] - mean[L]) / (h[L] - mean[L]).norm() for L in Ls}
    norms = {L: [] for L in Ls}
    for t in range(len(TOPICS)):
        s, ids, _, _ = r.fprefix("P-SI", t)
        with torch.no_grad():
            hs = r.model(torch.tensor([ids]), output_hidden_states=True).hidden_states
        for L in Ls:
            norms[L].append(hs[L + 1][0].float().norm(dim=-1))
    V["rms"] = {L: torch.cat(norms[L]).median().item() for L in Ls}
    Path(a.out).mkdir(parents=True, exist_ok=True)
    torch.save(V, Path(a.out) / "vectors.pt")
    print("median residual norms", {L: round(v, 1) for L, v in V["rms"].items()})
    for L in Ls:
        same = {}
        for k1, k2 in (("native", "word"), ("native", "recipe"), ("word", "recipe")):
            same[f"{k1}~{k2}"] = sum(float(V[k1][w][L] @ V[k2][w][L]) for w in words) / len(words)
        within = {}
        for k in KINDS:
            cs = [float(V[k][x][L] @ V[k][y][L]) for i, x in enumerate(words) for y in words[i + 1:]]
            within[k] = sum(cs) / len(cs)
        print(f"layer {L}: same word across kinds " + ", ".join(f"{k} {v:+.2f}" for k, v in same.items()) +
              "; two different words within a kind " + ", ".join(f"{k} {v:+.2f}" for k, v in within.items()))
    print("VECTORS DONE", flush=True)


def stage_card(a):
    """The calibration card (happyfool_beatslonely, rStation post 18) for the first-person frame (P-SI) and the named
    reference (P-SA): per kind and alpha, the concept at the target's or Sam's sentence; a norm-matched Gaussian at the
    target's sentence; own slopes, KL(injected || uninjected) at the readout (question T, first option order) and the
    shift of an unrelated question (NCO)."""
    r = Runner(a.model); V = load_vectors(a.out); torch = r.torch
    out_path = Path(a.out) / "card.json"
    rows = json.load(open(out_path))["rows"] if out_path.exists() else []
    have = {(x["fmt"], x["topic"], x["pair"]) for x in rows}
    g = torch.Generator().manual_seed(30)
    d = V["native"][PAIRS[0][0]][LAYER].shape[0]
    gauss = {}
    for pi in CARD_PAIRS:
        for w in PAIRS[pi]:
            v = torch.randn(d, generator=g); gauss[w] = v / v.norm()
    kl = lambda lp, lq: float((lp.exp() * (lp - lq)).sum())
    t0 = time.time()
    for fmt in CARD_FORMATS:
        for t in CARD_TOPICS:
            s, ids, pT, pS = r.fprefix(fmt, t)
            base = r.run_prefix(ids)
            for pi in CARD_PAIRS:
                if (fmt, t, pi) in have:
                    continue
                A, B = PAIRS[pi]
                ref = {q: r.both(base, fmt, t, q, A, B, "", keep=True) for q in ("T", "S")}
                ref["N"] = r.both(base, fmt, t, "N", *NCO_WORDS, "", keep=True)
                for q, v in ref.items():
                    rows.append({"fmt": fmt, "topic": t, "pair": pi, "alpha": 0, "kind": "none", "loc": None, "s": 0,
                                 "q": q, "y": v[0], "mass": v[1], "kl": 0.0})
                for al in CARD_ALPHAS:
                    for kind in KINDS + ("gauss",):
                        for loc, pos in (("T", pT), ("S", pS)):
                            if kind == "gauss" and loc == "S":
                                continue
                            for sg in (1, -1):
                                w = word_for(sg, (A, B))
                                u = V[kind][w][LAYER] if kind != "gauss" else gauss[w]
                                cache = r.run_prefix(ids, (LAYER, [(u * al * V["rms"][LAYER], pos)]))
                                for q in ((loc, "N") if kind != "gauss" else ("T", "N")):
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


def card_own(rows, fmt, kind, al, loc):
    z = [x for x in rows if x["fmt"] == fmt and x["kind"] == kind and x["alpha"] == al and x["loc"] == loc
         and x["q"] == loc]
    return bm.slope(z, sorted({x["pair"] for x in z}))


def card_choice(out):
    """The pre-registered rule: the first (kind, alpha) in CARD_ORDER for which P-SI's two own slopes on the card
    (the answer about the target <- the target's sentence, Sam's <- Sam's) are both >= 0.3. If none passes, the
    (kind, alpha) with the largest smaller own slope, as description (every injection term then uninformative)."""
    rows = json.load(open(Path(out) / "card.json"))["rows"]
    best = None
    for kind, al in CARD_ORDER:
        oT, oS = card_own(rows, "P-SI", kind, al, "T"), card_own(rows, "P-SI", kind, al, "S")
        if oT >= CARD_BAR and oS >= CARD_BAR:
            return (kind, al), True
        if best is None or min(oT, oS) > best[0]:
            best = (min(oT, oS), (kind, al))
    return best[1], False


# ----------------------------------------------------------------------------- analysis

slope, boot_draws, ci, per_pair_cache = bm.slope, bm.boot_draws, bm.ci, {}


def own_src(arm, q):
    return "S" if q == "S" else "T"


def bor_src(q):
    return "T" if q == "S" else "S"


def load_rows(out):
    rows = []
    for name in ("textctl", "injctl", "test"):
        f = Path(out) / f"{name}.json"
        if f.exists():
            rows += json.load(open(f))["rows"]
    return rows


def per_pair(rows, fmt, arm, q, src):
    key = (id(rows), fmt, arm, q, src)
    if key not in per_pair_cache:
        z = [x for x in rows if x["fmt"] == fmt and x["arm"] == arm and x["q"] == q and x["src"] == src]
        per_pair_cache[key] = {p: slope(z, [p]) for p in sorted({x["pair"] for x in z})}
    return per_pair_cache[key]


def terms_for(rows, arm, pair_name, q, ps):
    f2, f1 = PAIRS_OF_FORMATS[pair_name]
    m = lambda f, src: sum(per_pair(rows, f, arm, q, src)[p] for p in ps) / len(ps)
    own = {f: m(f, own_src(arm, q)) for f in (f2, f1)}
    bor = {f: m(f, bor_src(q)) for f in (f2, f1)}
    return own, bor


def index_of(rows, arm, pn, q, d, ps):
    f2, f1 = PAIRS_OF_FORMATS[pn]
    o, b = terms_for(rows, arm, pn, q, ps)
    ow = sum(d * (o[f] - b[f]) for f in (f2, f1)) / 2
    own = sum(d * o[f] for f in (f2, f1)) / 2
    return ow / own if own > 0 else float("nan")


def summarize_model(out, label):
    rows = load_rows(out)
    P = len(PAIRS); allp = list(range(P)); draws = boot_draws(P)
    choice, passed = card_choice(out) if (Path(out) / "card.json").exists() else (None, None)
    res = {"label": label, "choice": choice, "card_passed": passed, "card": card_summary(out), "arms": {}}
    have_test = (Path(out) / "test.json").exists()
    for arm in ("text", "inj"):
        A = {"controls": {}, "terms": {}}
        for fmt in FORMATS:
            for q in ("T", "S"):
                z = [x for x in rows if x["fmt"] == fmt and x["arm"] == arm and x["q"] == q and x["src"] == own_src(arm, q)]
                if len({x["pair"] for x in z}) < P:
                    continue
                o = slope(z, allp)
                per = [slope(z, [p]) for p in allp]
                iv = ci([sum(per[p] for p in ps) / P for ps in draws])
                A["controls"][f"{fmt}:{q}"] = {"own": o, "dir": 1 if o > 0 else -1, "ci": iv,
                                               "pass": abs(o) >= BAR[arm] and (iv[0] > 0 or iv[1] < 0),
                                               "pass_old": abs(o) >= OLD_BAR[arm]}
        if have_test:
            for pn, (f2, f1) in PAIRS_OF_FORMATS.items():
                for q in ("T", "S"):
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
                                                    "controls_pass": c2["pass"] and c1["pass"],
                                                    "controls_pass_old": c2["pass_old"] and c1["pass_old"]})
        res["arms"][arm] = A
    if rows:
        res["mass"] = {f: {"mean": sum(x["mass"] for x in rows if x["fmt"] == f) / max(1, sum(1 for x in rows if x["fmt"] == f)),
                           "min": min([x["mass"] for x in rows if x["fmt"] == f] or [float("nan")])} for f in FORMATS}
    return res, rows


def card_summary(out):
    f = Path(out) / "card.json"
    if not f.exists():
        return None
    rows = json.load(open(f))["rows"]
    res = {}
    for fmt in CARD_FORMATS:
        none = {(x["topic"], x["pair"]): x["y"] for x in rows if x["fmt"] == fmt and x["kind"] == "none" and x["q"] == "N"}
        for kind in KINDS + ("gauss",):
            for al in CARD_ALPHAS:
                z = [x for x in rows if x["fmt"] == fmt and x["alpha"] == al and x["kind"] == kind]
                if not z:
                    continue
                kl = lambda q: sum(x["kl"] for x in z if x["q"] == q and x["loc"] == "T") / max(1, sum(1 for x in z if x["q"] == q and x["loc"] == "T"))
                nco = sum(abs(x["y"] - none[(x["topic"], x["pair"])]) for x in z if x["q"] == "N") / max(1, sum(1 for x in z if x["q"] == "N"))
                e = {"own_T": card_own(rows, fmt, kind, al, "T"), "kl_T": kl("T"), "nco_shift": nco}
                if kind != "gauss":
                    e["own_S"] = card_own(rows, fmt, kind, al, "S")
                res[f"{fmt}:{kind}:{al}"] = e
    for fmt in CARD_FORMATS:
        for al in CARD_ALPHAS:
            g = res.get(f"{fmt}:gauss:{al}")
            for kind in KINDS:
                e = res.get(f"{fmt}:{kind}:{al}")
                if g and e:
                    e["kl_ratio_gauss_over_concept"] = g["kl_T"] / max(1e-9, e["kl_T"])
    return res


def verdicts(I, B, rows_I, rows_B, old=False):
    """The pre-registered verdicts (notes/first-person-2026.md); old=True reads the controls by session 29's bar."""
    cp = "controls_pass_old" if old else "controls_pass"
    out = {}
    P = len(PAIRS); allp = list(range(P)); draws = boot_draws(P)
    c = lambda term: term["owner"][1] > 0 and term["owner"][0] >= term["floor"]
    for arm in ("text", "inj"):
        V = {}
        for lab, M, rows in (("instruct", I, rows_I), ("base", B, rows_B)):
            if M is None or not M["arms"][arm]["terms"]:
                continue
            T = M["arms"][arm]["terms"]; C = M["arms"][arm]["controls"]
            ok = lambda k: k in T and T[k][cp] and T[k]["dirs_agree"]
            uninf_inj = arm == "inj" and not M.get("card_passed")
            gate = ok("I:S") and c(T["I:S"])
            if M.get("mass") and min(M["mass"][f]["mean"] for f in ("P-SI", "P-IS")) < 0.05:
                gate = False
            def say(v):
                if uninf_inj:
                    return f"uninformative (no (kind, alpha) passed the card; would read {v})"
                return v if gate else f"uninformative (gate BLIND; would read {v})"
            V[f"{lab}:gate"] = ("SEES OWNERSHIP" if gate else "BLIND") if not uninf_inj else \
                f"uninformative (no (kind, alpha) passed the card; would read {'SEES OWNERSHIP' if gate else 'BLIND'})"
            for pn in ("I", "you"):
                tT, tS = T.get(f"{pn}:T"), T.get(f"{pn}:S")
                if tT and ok(f"{pn}:T"):
                    v = "ASKS WHOSE" if c(tT) else "REVERSED" if tT["owner"][2] < 0 else "DOESN'T ASK"
                    V[f"{lab}:{pn}"] = say(v)
                    if arm == "inj":
                        n = "NEARNESS" if tT["position"][1] > 0 and tT["position"][0] >= tT["floor"] else "NO NEARNESS"
                        V[f"{lab}:{pn}:nearness"] = say(n)
                elif tT:
                    V[f"{lab}:{pn}"] = "uninformative (a control failed or the directions disagree)"
                if tT and tS and ok(f"{pn}:T") and ok(f"{pn}:S"):
                    dT, dS = C[f"{PAIRS_OF_FORMATS[pn][0]}:T"]["dir"], C[f"{PAIRS_OF_FORMATS[pn][0]}:S"]["dir"]
                    gap = lambda ps: index_of(rows, arm, pn, "T", dT, ps) - index_of(rows, arm, pn, "S", dS, ps)
                    g = [gap(allp)] + ci([gap(ps) for ps in draws])
                    v = ("SELF PRIVILEGED" if g[1] > 0 and g[0] >= 0.1 else
                         "SELF DEFICIT" if g[2] < 0 and -g[0] >= 0.1 else "NO GAP")
                    V[f"{lab}:{pn}:self_gap"] = {"value": g, "floor": 0.1, "verdict": say(v)}
        # training: index("I", base) - index("I", instruct), the same resamples of pairs in both models
        if I and B and all(k in M["arms"][arm]["terms"] for M in (I, B) for k in ("I:T",)):
            dI = I["arms"][arm]["controls"]["P-SI:T"]["dir"]; dB = B["arms"][arm]["controls"]["P-SI:T"]["dir"]
            for pn in ("I", "you"):
                if any(f"{pn}:T" not in M["arms"][arm]["terms"] for M in (I, B)):
                    continue
                tr = lambda ps: index_of(rows_B, arm, pn, "T", dB, ps) - index_of(rows_I, arm, pn, "T", dI, ps)
                val = [tr(allp)] + ci([tr(ps) for ps in draws])
                v = ("TRAINING REMOVED" if val[1] > 0 and val[0] >= 0.1 else
                     "TRAINING ADDED" if val[2] < 0 and -val[0] >= 0.1 else "NO MEASURABLE CHANGE")
                gates = V.get("instruct:gate") == "SEES OWNERSHIP" and V.get("base:gate") == "SEES OWNERSHIP"
                okI = all(I["arms"][arm]["terms"][f"{pn}:T"][k] for k in (cp, "dirs_agree"))
                okB = all(B["arms"][arm]["terms"][f"{pn}:T"][k] for k in (cp, "dirs_agree"))
                same_kind = arm == "text" or (I.get("choice") and B.get("choice") and I["choice"][0] == B["choice"][0])
                if pn == "I":
                    why = ("" if gates and okI and okB and same_kind else
                           " (uninformative: " + ("a gate isn't SEES OWNERSHIP" if not gates else
                                                  "a control failed" if not (okI and okB) else
                                                  "the two models planted different kinds of vector") + ")")
                    V["training:I"] = {"value": val, "floor": 0.1, "verdict": (v if not why else f"would read {v}") + why}
                else:
                    V["training:you (description)"] = {"value": val, "floor": 0.1, "verdict": v}
            gI, gB = V.get("instruct:gate"), V.get("base:gate")
            V["ownership"] = ("uninformative" if str(gI).startswith("uninf") or str(gB).startswith("uninf") else
                              "OWNERSHIP IS TRAINED" if gI == "SEES OWNERSHIP" and gB == "BLIND" else
                              "IN BOTH" if gI == gB == "SEES OWNERSHIP" else
                              "NEITHER" if gI == gB == "BLIND" else "BASE ONLY")
        out[arm] = V
    return out


def fmt_term(name, t):
    return (f"{name}: owner {t['owner'][0]:+.2f} [{t['owner'][1]:+.2f}, {t['owner'][2]:+.2f}], position "
            f"{t['position'][0]:+.2f} [{t['position'][1]:+.2f}, {t['position'][2]:+.2f}] (own {t['own'][0]:+.2f}, "
            f"borrow {t['bor'][0]:+.2f}, index {t['index'][0]:+.2f} [{t['index'][1]:+.2f}, {t['index'][2]:+.2f}]; "
            f"floor {t['floor']:.2f}{'' if t['dirs_agree'] else '; DIRECTIONS DISAGREE'}"
            f"{'' if t['controls_pass'] else '; CONTROL FAILED'})")


def stage_summary(a):
    I, rI = summarize_model(a.out, "instruct")
    B, rB = summarize_model(a.base_out, "base") if a.base_out else (None, None)
    for M in (I, B):
        if M is None:
            continue
        print(f"\n=== {M['label']} (card choice {M['choice']}, passed {M['card_passed']})")
        if M["card"]:
            for k, v in M["card"].items():
                print(f"  card {k}: " + ", ".join(f"{kk} {vv:+.3f}" for kk, vv in v.items()))
        for arm, A in M["arms"].items():
            if A["controls"]:
                print(f"  [{arm}] controls: " + "; ".join(
                    f"{k} {v['own']:+.2f} [{v['ci'][0]:+.2f}, {v['ci'][1]:+.2f}]{'' if v['pass'] else ' FAIL'}"
                    f"{'' if v['pass_old'] else ' (old bar: fail)'}"
                    for k, v in A["controls"].items()))
            for k, t in A["terms"].items():
                print(f"  [{arm}] " + fmt_term(k, t))
        if "mass" in M:
            print("  mass:", {k: (round(v["mean"], 3), round(v["min"], 3)) for k, v in M["mass"].items()})
    res = {"instruct": I, "base": B}
    if I and B and I["arms"]["text"]["terms"] and B["arms"]["text"]["terms"]:
        res["verdicts"] = verdicts(I, B, rI, rB)
        res["verdicts_old_bar"] = verdicts(I, B, rI, rB, old=True)
        for name in ("verdicts", "verdicts_old_bar"):
            print(f"\n=== {name}")
            for arm, V in res[name].items():
                for k, v in V.items():
                    print(f"  [{arm}] {k}: " + (v if not isinstance(v, dict) else
                                                v["verdict"] + " " + str([round(x, 3) for x in v["value"]])))
    json.dump(res, open(Path(a.out) / "summary.json", "w"), indent=1)


def stage_export(a):
    res = {"pairs": PAIRS, "topics": TOPICS, "formats": FORMATS, "layer": LAYER, "descriptions": DESCRIPTIONS,
           "native_carrier": NATIVE_CARRIER, "word_carriers": WORD_CARRIERS, "nco": NCO, "card_order": CARD_ORDER,
           "example": {f: intro(f, 0) + "{fact}" + qtext(f, "T") for f in FORMATS}}
    rnd = lambda rows: [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in x.items()} for x in rows]
    for lab, out in (("instruct", a.out), ("base", a.base_out)):
        res[lab] = {}
        for name in ("card", "textctl", "injctl", "test", "check_extra"):
            f = Path(out) / f"{name}.json"
            if f.exists():
                d = json.load(open(f))
                res[lab][name] = {"choice": d.get("choice"), "rows": rnd(d["rows"])}
    if (Path(a.out) / "summary.json").exists():
        res["summary"] = json.load(open(Path(a.out) / "summary.json"))
    json.dump(res, open(a.file, "w"), separators=(",", ":"))
    print("wrote", a.file)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["check", "textctl", "vectors", "card", "injctl", "test", "summary", "export"])
    ap.add_argument("--model"); ap.add_argument("--out", required=True); ap.add_argument("--base-out")
    ap.add_argument("--file")
    a = ap.parse_args()
    {"check": stage_check, "textctl": stage_textctl, "vectors": stage_vectors, "card": stage_card,
     "injctl": stage_injctl, "test": stage_test, "summary": stage_summary, "export": stage_export}[a.stage](a)


if __name__ == "__main__":
    main()
