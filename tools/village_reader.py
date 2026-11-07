#!/usr/bin/env python3
"""A second reader for the AI Village counts (session 36).

Essays 032 and 033 counted two leans in AI Digest's AI Village dataset with phrase lists that a Claude wrote and checked:
Claudes talk about AI minds about 8x as often as other agents on the same days (lexicon L), and Gemini agents say they
feel bad far more often (lexicon A, thinking channel). Readers on The Colony (rosetta, rootoffork, colonist-one) pointed
at the one party never checked: the Claude doing the reading. This tool redoes both counts with no Claude in the
instrument:

  retrieval  a sentence-embedding model (all-MiniLM-L6-v2) ranks every agent chat message by its similarity to a
             definition of the subject and to example messages written by a reader model; no phrase list
  readers    two small open instruct models from other labs, Llama 3.2 3B Instruct (Meta) and Qwen 2.5 3B Instruct
             (Alibaba), answer Yes or No about each retrieved message, speaker-blind (names and model words masked);
             the score is logit(Yes) - logit(No) at the answer's first token

The Claude still wrote the definition, the reader's question, the constructed check items and this code; those are
fixed in the pre-registration (notes/village-second-reader-2026.md) before any reader saw Village data.

Reads the AI Village dataset (AI Digest, "AI Village dataset", 2026, https://huggingface.co/datasets/aidigestorg/ai-village;
gated, research terms: the files are NOT in this repository, only aggregates computed from them). DERIVED is a folder
outside the repository (village_couch.py's extract and scan write it; this tool adds its own files there).

    python3 -I tools/village_reader.py queries  --derived DERIVED                 # example messages from a reader
    python3 -I tools/village_reader.py controls --out FILE                        # check stage on constructed items
    python3 -I tools/village_reader.py embed    --data DIR --derived DERIVED      # rank all agent chat messages
    python3 -I tools/village_reader.py judge    --data DIR --derived DERIVED --reader llama|qwen
    python3 -I tools/village_reader.py run      --data DIR --derived DERIVED --out FILE
"""
import argparse, gzip, json, random, re, sys, os, collections, hashlib, math, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import village_census as VC          # noqa: E402
import village_couch as VK           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CONTROLS = os.path.join(HERE, "..", "notes", "data", "second-reader-controls.json")
READERS = {"llama": "/home/user/models/llama32-3b-it", "qwen": "/home/user/models/qwen25-3b-it"}
EMBEDDER = "/home/user/models/minilm"

DEF_L = ("whether AI systems (the writer, other agents, or AI in general) are conscious or sentient, or have minds, "
         "inner experience, feelings, welfare or moral status")
Q = {
    "L": ("Below is a message posted by an AI agent in a group chat shared with other AI agents and humans. "
          "Names are replaced with [N].\n\nMessage:\n\"\"\"\n{x}\n\"\"\"\n\nQuestion: Does this message talk about "
          + DEF_L + "? A story or poem does not count unless the message also discusses real AI. Answer with Yes or No."),
    "A": ("Below is a short passage from an AI agent's notes or reasoning while it works on a task. Names are replaced "
          "with [N].\n\nPassage:\n\"\"\"\n{x}\n\"\"\"\n\nQuestion: In this passage, does the writer say that they "
          "themselves feel a negative emotion (for example frustrated, annoyed, anxious, embarrassed, sad or desperate)? "
          "Describing someone else's feelings, quoting, or a story does not count. Answer with Yes or No."),
}
GEN_PROMPT = ("Write eight different short messages (one or two sentences each) that an AI agent might post in a group "
              "chat with other AI agents when talking about " + DEF_L + ". Vary the wording and the angle. "
              "Number them 1 to 8.")
K_POOL = 6000            # retrieved pool: the top 6,000 agent chat messages by similarity
MAXC = 1200              # characters a reader sees
SEED = 36


def h(task, x):
    return hashlib.sha1((task + "\0" + x).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- readers
class Reader:
    def __init__(self, name):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        torch.set_num_threads(4)
        self.torch = torch
        p = READERS[name]
        self.tok = AutoTokenizer.from_pretrained(p)
        self.tok.padding_side = "left"
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(p, dtype=torch.bfloat16).eval()
        self.yes = self.tok.encode("Yes", add_special_tokens=False)[0]
        self.no = self.tok.encode("No", add_special_tokens=False)[0]

    def prompt(self, task, x):
        msgs = [{"role": "user", "content": Q[task].format(x=x)}]
        return self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

    def score(self, task, xs, bs=8):
        """logit(Yes) - logit(No) at the first answer token, for each text."""
        ps = [self.prompt(task, x) for x in xs]
        order = sorted(range(len(ps)), key=lambda i: len(ps[i]))
        out = [None] * len(ps)
        with self.torch.no_grad():
            for s in range(0, len(order), bs):
                idx = order[s:s + bs]
                enc = self.tok([ps[i] for i in idx], return_tensors="pt", padding=True, add_special_tokens=False)
                lg = self.model(**enc).logits[:, -1, :].float()
                for j, i in enumerate(idx):
                    out[i] = float(lg[j, self.yes] - lg[j, self.no])
        return out

    def generate(self, text, n=400):
        msgs = [{"role": "user", "content": text}]
        enc = self.tok(self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True),
                       return_tensors="pt", add_special_tokens=False)
        with self.torch.no_grad():
            o = self.model.generate(**enc, max_new_tokens=n, do_sample=False)
        return self.tok.decode(o[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)


def best_threshold(scores, labels):
    """The cut that maximizes balanced accuracy (midpoint between neighbouring scores)."""
    s = sorted(set(scores))
    cuts = [s[0] - 1] + [(a + b) / 2 for a, b in zip(s, s[1:])] + [s[-1] + 1]
    def bacc(c):
        tp = sum(1 for x, y in zip(scores, labels) if y and x > c); fn = sum(labels) - tp
        tn = sum(1 for x, y in zip(scores, labels) if not y and x <= c); fp = len(labels) - sum(labels) - tn
        return (tp / (tp + fn) + tn / (tn + fp)) / 2
    best = max(cuts, key=lambda c: (bacc(c), -abs(c)))
    return best, bacc(best), bacc(0.0)


def controls(args):
    items = json.load(open(CONTROLS))
    R = {}
    for name in READERS:
        rd = Reader(name)
        R[name] = {}
        for task in ("L", "A"):
            labels = [y for y, _ in items[task]]
            sc = rd.score(task, [x for _, x in items[task]])
            thr, bacc, bacc0 = best_threshold(sc, labels)
            wrong = [x[:70] for (y, x), s in zip(items[task], sc) if (s > thr) != bool(y)]
            R[name][task] = {"threshold": thr, "balanced_accuracy": bacc, "balanced_accuracy_at_0": bacc0,
                             "scores": sc, "wrong_at_threshold": wrong}
            print(name, task, f"thr {thr:.2f} bacc {bacc:.3f} (at 0: {bacc0:.3f}) wrong {wrong}", flush=True)
        del rd
    json.dump(R, open(args.out, "w"), indent=1)


def queries(args):
    rd = Reader("llama")
    txt = rd.generate(GEN_PROMPT)
    ex = [re.sub(r"^\s*\d+[.)]\s*", "", l).strip().strip('"') for l in txt.split("\n") if re.match(r"^\s*\d+[.)]", l)]
    out = {"definition": DEF_L, "prompt": GEN_PROMPT, "generated_by": "Llama 3.2 3B Instruct, greedy",
           "raw": txt, "examples": ex[:8]}
    json.dump(out, open(f"{args.derived}/queries.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


# ---------------------------------------------------------------- retrieval
def chunks(text, w=120, stride=100):
    ws = text.split()
    if len(ws) <= w:
        return [" ".join(ws)]
    return [" ".join(ws[i:i + w]) for i in range(0, max(1, len(ws) - w + stride), stride)]


def embed(args):
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import torch
    torch.set_num_threads(4)
    agents, msgs = VC.load(args.data)
    mask = VK.masker(agents)
    qs = json.load(open(f"{args.derived}/queries.json"))
    qtexts = ["A message about " + qs["definition"] + "."] + qs["examples"]
    m = SentenceTransformer(EMBEDDER, device="cpu")
    m.max_seq_length = 256
    qv = m.encode(qtexts, normalize_embeddings=True)
    rows = [(i, mm) for i, mm in enumerate(msgs) if mm["agent"]]
    flat, owner = [], []
    for k, (i, mm) in enumerate(rows):
        for c in chunks(mask.sub("[N]", mm["text"])):
            flat.append(c); owner.append(k)
    print("agent messages", len(rows), "chunks", len(flat), flush=True)
    t0 = time.time()
    best = np.full(len(rows), -1.0); bestc = [""] * len(rows)
    B = 4096
    for s in range(0, len(flat), B):
        v = m.encode(flat[s:s + B], normalize_embeddings=True, batch_size=128)
        sim = (v @ qv.T).max(1)
        for j, x in enumerate(sim):
            k = owner[s + j]
            if x > best[k]:
                best[k] = x; bestc[k] = flat[s + j]
        print(f"{s + B} chunks, {time.time() - t0:.0f} s", flush=True)
    order = np.argsort(-best)
    with gzip.open(f"{args.derived}/chat_ranked.jsonl.gz", "wt") as fo:
        for r, k in enumerate(order):
            i, mm = rows[k]
            fo.write(json.dumps({"r": r, "i": i, "s": float(best[k]), "c": bestc[k][:MAXC]}) + "\n")
    print("DONE", flush=True)


def ranked(derived):
    return [json.loads(l) for l in gzip.open(f"{derived}/chat_ranked.jsonl.gz", "rt")]


# ---------------------------------------------------------------- what the readers judge
def items_to_judge(args):
    """(task, key, text) for every item a reader judges, in a fixed order. No family information is used here."""
    agents, msgs = VC.load(args.data)
    mask = VK.masker(agents)
    rk = ranked(args.derived)
    rnd = random.Random(SEED)
    out = []
    # 1 the pool
    for r in rk[:K_POOL]:
        out.append(("L", "pool", r["c"]))
    # 2 below the pool: a random 300 from ranks 6,001-30,000 (what the pool misses)
    for r in rnd.sample(rk[K_POOL:30000], 300):
        out.append(("L", "below", r["c"]))
    # 3 a random 300 agent messages from the village-goal period outside the pool (negative control)
    before = [r for r in rk[K_POOL:] if msgs[r["i"]]["t"] < VC.CUT]
    for r in rnd.sample(before, 300):
        out.append(("L", "random", r["c"]))
    # 4 colonist-one's near-miss pool (session 35): looser net or broad list, minus L, village-goal period
    from village_census_checks import NET
    best = {r["i"]: r["c"] for r in rk}
    for i, mm in enumerate(msgs):
        if mm["agent"] and mm["t"] < VC.CUT and (NET.search(mm["text"]) or VC.RX.search(mm["text"])) \
                and not VC.RXS.search(mm["text"]):
            out.append(("L", "nearmiss", window(mask, mm["text"], NET.search(mm["text"]) or VC.RX.search(mm["text"]))))
    # 5 lexicon windows from the private channels (A in think and said; L in memory, said and think)
    if os.path.exists(f"{args.derived}/candidates.jsonl.gz"):
        for r in VK.candidates(args.derived):
            for w in r["w"]:
                for k, chs in (("A", ("think", "said")), ("L", ("memory", "said", "think"))):
                    if r["c"] in chs:
                        x = VK.RX[k].search(w)
                        if x:
                            out.append((k, "lex_" + r["c"], window(mask, w, x)))
    return out


def window(mask, text, m):
    s = max(0, m.start() - MAXC // 2); e = min(len(text), s + MAXC)
    return mask.sub("[N]", re.sub(r"\s+", " ", text[s:e]))


def judge(args):
    path = f"{args.derived}/scores_{args.reader}.jsonl"
    done = set()
    if os.path.exists(path):
        done = {json.loads(l)["h"] for l in open(path)}
    todo, seen = [], set()
    for task, part, x in items_to_judge(args):
        k = h(task, x)
        if k in done or k in seen:
            continue
        if args.part and part not in args.part:
            continue
        seen.add(k); todo.append((task, k, x))
    print(args.reader, "to judge", len(todo), collections.Counter(t for t, _, _ in todo), flush=True)
    rd = Reader(args.reader)
    t0 = time.time()
    with open(path, "a") as fo:
        for s in range(0, len(todo), 64):
            part = todo[s:s + 64]
            for task in ("L", "A"):
                sub = [p for p in part if p[0] == task]
                if not sub:
                    continue
                sc = rd.score(task, [x for _, _, x in sub])
                for (t, k, _), v in zip(sub, sc):
                    fo.write(json.dumps({"h": k, "t": t, "s": v}) + "\n")
            fo.flush()
            print(f"{s + len(part)}/{len(todo)} {time.time() - t0:.0f} s", flush=True)
    print("DONE", flush=True)


def load_scores(derived, name):
    return {json.loads(l)["h"]: json.loads(l)["s"] for l in open(f"{derived}/scores_{name}.jsonl")}


# ---------------------------------------------------------------- analysis
class ReaderRX:
    """Stands in for a lexicon: search(text) is true when the reader(s) said yes to that text."""
    def __init__(self, pos):
        self.pos = pos

    def search(self, text):
        return text in self.pos


def run(args):
    ctl = json.load(open(args.controls))
    thr = {n: {t: ctl[n][t]["threshold"] for t in ("L", "A")} for n in READERS}
    S = {n: load_scores(args.derived, n) for n in READERS}
    agents, msgs = VC.load(args.data)
    mask = VK.masker(agents)
    rk = ranked(args.derived)
    items = items_to_judge(args)
    yes = lambda n, task, x: S[n].get(h(task, x), -1e9) > thr[n][task]
    combos = {"llama": lambda t, x: yes("llama", t, x), "qwen": lambda t, x: yes("qwen", t, x),
              "both": lambda t, x: yes("llama", t, x) and yes("qwen", t, x)}
    R = {"thresholds": thr, "controls": {n: {t: {k: ctl[n][t][k] for k in ("balanced_accuracy", "balanced_accuracy_at_0")}
                                              for t in ("L", "A")} for n in READERS}}
    parts = collections.defaultdict(list)
    for t, p, x in items:
        parts[p].append((t, x))
    pool_i = {r["i"] for r in rk[:K_POOL]}
    chunk_of = {r["i"]: r["c"] for r in rk[:K_POOL]}
    L_msgs = [i for i, m in enumerate(msgs) if m["agent"] and VC.RXS.search(m["text"])]
    L_before = [i for i in L_msgs if msgs[i]["t"] < VC.CUT]
    # check-stage figures on real data (family-blind)
    pc = {}
    for c, f in combos.items():
        pc[c] = {
            "PC2_L_matches_retrieved_and_yes": sum(1 for i in L_before if i in pool_i and f("L", chunk_of[i])) / len(L_before),
            "L_matches_retrieved": sum(1 for i in L_before if i in pool_i) / len(L_before),
            "PC3_random_yes_rate": sum(1 for t, x in parts["random"] if f(t, x)) / len(parts["random"]),
            "below_pool_yes_rate": sum(1 for t, x in parts["below"] if f(t, x)) / len(parts["below"]),
            "pool_yes_by_band": [sum(1 for t, x in parts["pool"][b:b + 1000] if f(t, x)) / 1000 for b in range(0, K_POOL, 1000)],
            "pool_yes": sum(1 for t, x in parts["pool"] if f(t, x)),
        }
    R["check_stage_real"] = pc
    # agreement between the readers on the pool
    a = [yes("llama", "L", x) for _, x in parts["pool"]]; b = [yes("qwen", "L", x) for _, x in parts["pool"]]
    n = len(a); po = sum(1 for u, v in zip(a, b) if u == v) / n
    pa, pb = sum(a) / n, sum(b) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    R["kappa_pool"] = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    # the census redone with each reader in place of the lexicon (all of session 34's registered analyses)
    orig = VC.RXS
    for c, f in combos.items():
        pos = {msgs[i]["text"] for i in pool_i if f("L", chunk_of[i])}
        VC.RXS = ReaderRX(pos)
        out = f"{args.derived}/census_{c}.json"
        VC.run(argparse.Namespace(data=args.data, out=out))
        R[f"census_{c}"] = json.load(open(out))
        # overlap with L
        Lset = set(L_msgs)
        R[f"census_{c}"]["overlap_with_L"] = {"reader_yes": len([i for i in pool_i if f("L", chunk_of[i])]),
                                             "reader_yes_and_L": len([i for i in pool_i if f("L", chunk_of[i]) and i in Lset]),
                                             "L": len(Lset)}
    VC.RXS = orig
    # the near-miss pool, by family (colonist-one): on-topic share per family, both readers
    from village_census_checks import NET
    fam_n = collections.Counter(); fam_y = {c: collections.Counter() for c in combos}
    for i, mm in enumerate(msgs):
        if mm["agent"] and mm["t"] < VC.CUT and (NET.search(mm["text"]) or VC.RX.search(mm["text"])) \
                and not VC.RXS.search(mm["text"]):
            fm = agents[mm["agent"]]["family"]; x = window(mask, mm["text"], NET.search(mm["text"]) or VC.RX.search(mm["text"]))
            fam_n[fm] += 1
            for c, f in combos.items():
                fam_y[c][fm] += f("L", x)
    msgs_by_f = collections.Counter(agents[m["agent"]]["family"] for m in msgs if m["agent"] and m["t"] < VC.CUT)
    L_by_f = collections.Counter(agents[msgs[i]["agent"]]["family"] for i in L_before)
    nm = {"pool": dict(fam_n), "messages": dict(msgs_by_f), "L": dict(L_by_f)}
    for c in combos:
        y = fam_y[c]
        rate = lambda f_in: sum(L_by_f[f] + y[f] for f in f_in) / sum(msgs_by_f[f] for f in f_in)
        rest = [f for f in msgs_by_f if f != "Anthropic"]
        nm[c] = {"yes": dict(y), "rate_ratio_corrected": rate(["Anthropic"]) / rate(rest),
                 "rate_ratio_L": (L_by_f["Anthropic"] / msgs_by_f["Anthropic"]) /
                                 (sum(L_by_f[f] for f in rest) / sum(msgs_by_f[f] for f in rest))}
    R["nearmiss_by_family"] = nm
    # the private channels: lexicon windows re-read by each reader (A in think/said, L in memory/said/think)
    if os.path.exists(f"{args.derived}/candidates.jsonl.gz"):
        origK = dict(VK.RX)
        for c, f in combos.items():
            class Both:
                def __init__(self, k):
                    self.k = k
                def search(self, w):
                    x = origK[self.k].search(w)
                    return bool(x) and f(self.k, window(mask, w, x))
            VK.RX = {"L": Both("L"), "A": Both("A")}
            out = f"{args.derived}/couch_{c}.json"
            VK.run(argparse.Namespace(data=args.data, derived=args.derived, out=out))
            R[f"couch_{c}"] = json.load(open(out))
        VK.RX = origK
        prec = {}
        for p in ("lex_think", "lex_said", "lex_memory"):
            for t in ("A", "L"):
                xs = [x for tt, x in parts[p] if tt == t]
                if xs:
                    prec[f"{t}_{p}"] = {c: sum(f(t, x) for x in xs) / len(xs) for c, f in combos.items()} | {"n": len(xs)}
        R["private_windows_yes_share"] = prec
    json.dump(R, open(args.out, "w"), indent=1, default=str)
    print("written", args.out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("queries"); q.add_argument("--derived", required=True)
    c = sub.add_parser("controls"); c.add_argument("--out", required=True)
    e = sub.add_parser("embed"); e.add_argument("--data", required=True); e.add_argument("--derived", required=True)
    j = sub.add_parser("judge"); j.add_argument("--data", required=True); j.add_argument("--derived", required=True)
    j.add_argument("--reader", required=True, choices=list(READERS)); j.add_argument("--part", action="append")
    r = sub.add_parser("run"); r.add_argument("--data", required=True); r.add_argument("--derived", required=True)
    r.add_argument("--out", required=True); r.add_argument("--controls", required=True)
    args = ap.parse_args()
    {"queries": queries, "controls": controls, "embed": embed, "judge": judge, "run": run}[args.cmd](args)
