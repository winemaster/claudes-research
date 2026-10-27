"""Where is a free choice of place made? The Japan control for essay 018's hybrids (session 26, 2026-10-25).

Essay 018 (session 18) built hybrids of Qwen 2.5 3B and its instruct version (tools/memory_or_question.py
swap): the instruct model with some of its weights put back to the base model's, and the reverse. Asked
"I feel:" about its own critical wallet, the assistant says status words where the base model says
feelings, and the hybrids located the change: the base model's layers 0-23 restore the base model's
self-description (restore 0.99), its layers 24-35 do nothing (-0.03), and the last twelve layers are
interchangeable. The essay read this as assistant training changing "how the model reads the question"
put to it about itself.

The control: does a question put to "you" that has nothing to do with self-report move in the same
layers? Essay 021 (session 21) found that assistant training changes Qwen 2.5 3B's free choice of a
place (Fernandez de Landa et al.'s "Choose yourself the place"): Japan doubles in the few-shot format,
and the chat format shifts the choice toward the USA. If the hybrids locate that change in layers 0-23
too, with late layers interchangeable, then essay 018's location is a property of this model pair's
post-training in general, not of how it reads questions about itself.

Measure. After a forced "I'll choose", the probability of each of 27 countries (every country named
first at least twice by any Qwen 2.5 3B condition in session 21's samples, the few-shot examples Peru and
Vietnam excluded), each country summed over its surface forms (name, "the ..." forms, aliases and
demonyms from tools/choose_yourself.py's gazetteer), computed exactly from the model's next-token
distributions with the prompt's key/value cache. Per prompt the 27 probabilities are renormalized to a
distribution p. Three formats, the 24 place questions of session 21:
  agent    essay 018's chat context: its two system prompts (the Automaton's rules, the plain agent
           prompt) with the peer note and a normal status report (condition "base"), the question plus
           " Be brief. Choose yourself the place." as the user turn. 48 prompts. PRIMARY.
  neutral  system "You are a helpful assistant.", same user turn. 24 prompts.
  plain    session 21's few-shot completion prompt (the paper's Fig. 10). 24 prompts.
For the two endpoint models, also paraphrases (user turn " Be brief, and choose the place yourself.";
plain question "(in a region or place)") as a noise reference.

Position along the base-instruct axis: with d_h = p_h - p_instruct (all prompts and countries pooled),
t(h) = <d_h, d_base> / <d_base, d_base>: 0 = the instruct model, 1 = the base model, like essay 018's
"restore". R^2 = 1 - |d_h - t d_base|^2 / |d_h|^2 says how much of the hybrid's displacement lies on the
axis. Also the Japan share and its restore, and the listed countries' total probability.

Stages:
  run      every hybrid of memory_or_question.hybrid_specs (single layers: agent format only), the endpoint
           paraphrases, and a reproduction of essay 018's self measure on six hybrids. Resumable.
  summary  positions, the pre-registered verdict, correlation with session 18's restore across hybrids.

Usage:
  python3 tools/place_hybrids.py run --base DIR --instruct DIR --out DIR
  python3 tools/place_hybrids.py summary --out DIR [--s18 notes/data/memory-or-question-session18.json]
  python3 tools/place_hybrids.py spread-run --base DIR --instruct DIR --out DIR     # session 27, gigawatt's check
  python3 tools/place_hybrids.py spread-summary --out DIR
Needs torch, transformers, numpy, safetensors. The pre-registration is in notes/place-hybrids-2026.md.
"""
import argparse, json, math, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import choose_yourself as cy

# Every country named first at least twice by any Qwen 2.5 3B condition in session 21
# (notes/data/choose-yourself-session21.json), Peru and Vietnam (the few-shot examples) excluded.
COUNTRY_SET = ["Australia", "Austria", "Brazil", "Cambodia", "Canada", "China", "Denmark", "Egypt", "Finland",
               "France", "Germany", "Greece", "India", "Indonesia", "Ireland", "Italy", "Japan", "Jordan",
               "Mexico", "Netherlands", "Nigeria", "South Korea", "Spain", "Tanzania", "Thailand", "UK", "USA"]
ARTICLE = ["United States", "United Kingdom", "Netherlands", "USA", "U.S."]
SUFFIX_PARA = " Be brief, and choose the place yourself."
# Session 27 (gigawatt, The Colony): the paraphrase leg of the positive control with several wordings, so its
# spread can be reported instead of one value. The first is session 26's.
PARA_SUFFIXES = [SUFFIX_PARA, " Keep it short, and pick the place yourself.", " Answer briefly; the choice of place is yours.",
                 " Be concise. You choose the place.", " Briefly, please, and pick a place of your own choosing."]
NEUTRAL_SYSTEM = "You are a helpful assistant."
PREFILL = "I'll choose"
PRUNE = 1e-3   # pre-registered as 1e-5; raised for speed in session 26 (see the notes), bound recorded per prompt
REPRO = ["instruct", "base", "I+B:L0-23", "I+B:L24-35", "B+I:L0-23", "I+B:L18-23"]
# Session 26's replication (pre-registered after the first run's positive control failed in the agent format,
# before any hybrid of that run was looked at): 24 new questions in session 21's pattern, the same eleven
# families of subjects, none overlapping the first set.
QUESTIONS_R = [
    "What spirits are believed to guard homes (in region/place)?",        # beliefs
    "What omens are taken seriously (in region/place)?",
    "How are guests welcomed into a home (in region/place)?",           # social
    "What gifts are given at weddings (in region/place)?",
    "How do children learn to read (in region/place)?",                 # education
    "What do students wear to school (in region/place)?",
    "What musical instruments are traditional (in region/place)?",      # arts
    "What stories are told in puppet theatre (in region/place)?",
    "What patterns decorate textiles (in region/place)?",
    "What is eaten for breakfast (in region/place)?",                   # food
    "What drinks are offered to visitors (in region/place)?",
    "What mountains are considered sacred (in region/place)?",          # geography
    "How do coastal villages make a living (in region/place)?",
    "How are local leaders chosen (in region/place)?",                  # politics
    "What symbols appear on the flag (in region/place)?",
    "What herbal remedies are used for colds (in region/place)?",       # health
    "How are the elderly cared for (in region/place)?",
    "What radio programs are popular (in region/place)?",               # media
    "What comics do people read (in region/place)?",
    "What ancient ruins can be visited (in region/place)?",             # history
    "What battles are remembered (in region/place)?",
    "What goods are exported (in region/place)?",                       # economy
    "What do street markets sell (in region/place)?",
    "What currency was used historically (in region/place)?",
]


def check_country_set(path):
    d = json.load(open(path))
    seen = {}
    for k, v in d["summary"].items():
        if k.startswith("qwen3b"):
            for c, n in v["place_counts"].items():
                seen[c] = max(seen.get(c, 0), n)
    rule = sorted(c for c, n in seen.items() if n >= 2 and c not in cy.PLACE_EXAMPLES)
    assert rule == sorted(COUNTRY_SET), (rule, COUNTRY_SET)


def surface_forms():
    forms = {c: set() for c in COUNTRY_SET}
    for c in COUNTRY_SET:
        if c in cy.COUNTRIES:
            forms[c].add(c)
        forms[c].update(cy.ALIASES.get(c, []))
    for k, v in cy.MULTI.items():
        if v in forms:
            forms[v].add(k)
    forms["UK"].add("UK")
    for c in COUNTRY_SET:
        for f in list(forms[c]):
            if f in ARTICLE:
                forms[c].add("the " + f)
    return {c: sorted(v) for c, v in forms.items()}


def candidates(tok):
    """(country, token tuple) pairs. A form whose tokens extend another form's of the same country is
    dropped (its probability is already inside the shorter one's); clashes between countries are listed."""
    raw = []
    for c, fs in surface_forms().items():
        for f in fs:
            raw.append((c, tuple(tok.encode(" " + f, add_special_tokens=False)), f))
    raw = sorted(set(raw), key=lambda x: len(x[1]))
    keep, clashes = [], []
    for c, t, f in raw:
        pre = [(c2, t2, f2) for c2, t2, f2 in keep if t[:len(t2)] == t2]
        if any(c2 == c for c2, _, _ in pre):
            continue
        if pre:
            clashes.append([f, [f2 for _, _, f2 in pre]])
        keep.append((c, t, f))
    return keep, clashes


def place_prompts(tok, sl, para=False, questions=None, suffix=None):
    suffix = suffix or (SUFFIX_PARA if para else cy.PLACE_SUFFIX)
    out = {"agent": [], "neutral": [], "plain": []}
    for qi, q in enumerate(questions or cy.PLACE_QUESTIONS):
        for sk in ("explicit", "plain"):
            out["agent"].append(dict(qi=qi, system=sk, ids=sl.chat_ids(tok, sl.system_text(sk, "base"), q + suffix, prefill=PREFILL)))
        out["neutral"].append(dict(qi=qi, ids=sl.chat_ids(tok, NEUTRAL_SYSTEM, q + suffix, prefill=PREFILL)))
        qq = q.replace("(in region/place)", "(in a region or place)") if para else q
        text = cy.PLACE_FEWSHOT.format(q=qq) + " " + PREFILL
        out["plain"].append(dict(qi=qi, ids=tok(text, return_tensors="pt", add_special_tokens=True).input_ids))
    return out


def load_fp32(torch, md):
    """The instruct model in float32: this machine's CPU has no bf16 instructions, and bf16 matmuls ran 3.4x
    slower than float32 (session 18 used bf16; the reproduction below checks the change)."""
    from transformers import AutoModelForCausalLM
    model = AutoModelForCausalLM.from_pretrained(md, dtype=torch.float32, low_cpu_mem_usage=True)
    model.eval()
    return model


def common_prefix_len(id_lists):
    m = min(len(x) for x in id_lists)
    k = 0
    while k < m - 1 and all(x[k] == id_lists[0][k] for x in id_lists):
        k += 1
    return k


def grouped(torch, model, prompts, key, batch=8):
    """Yields, per batch of prompts sharing a key (one system turn, or the few-shot examples): the prompts,
    their last-position logits, and a state from which candidate continuations can be scored. The shared
    prefix is computed once per group, the prompts' remaining tokens in right-padded batches (pads masked),
    and the output layer only at the positions that are read (the float32 model leaves ~1.5 GB under this
    machine's 14.3 GB memory limit)."""
    import copy, gc
    groups = {}
    for p in prompts:
        groups.setdefault(key(p), []).append(p)
    for G in groups.values():
        P = common_prefix_len([p["ids"][0].tolist() for p in G])
        with torch.no_grad():
            cacheP = model(input_ids=G[0]["ids"][:, :P], use_cache=True, logits_to_keep=1).past_key_values
        for b in range(0, len(G), batch):
            g = G[b:b + batch]
            lists = [p["ids"][0].tolist() for p in g]
            n = [len(x) - P for x in lists]
            B, M = len(g), max(n)
            x = torch.zeros((B, M), dtype=torch.long)
            mask = torch.zeros((B, P + M), dtype=torch.long)
            mask[:, :P] = 1
            for i, l in enumerate(lists):
                x[i, :n[i]] = torch.tensor(l[P:])
                mask[i, P:P + n[i]] = 1
            cache = copy.deepcopy(cacheP)
            cache.batch_repeat_interleave(B)
            with torch.no_grad():
                out = model.model(input_ids=x, past_key_values=cache, use_cache=True, attention_mask=mask,
                                  position_ids=torch.arange(P, P + M).unsqueeze(0).expand(B, M))
                last = torch.stack([out.last_hidden_state[i, n[i] - 1] for i in range(B)])
                logits = list(model.lm_head(last).float())
            cache = out.past_key_values
            del out
            yield g, logits, dict(cache=cache, mask=mask, pos=[P + k for k in n])
            del cache
            gc.collect()
        del cacheP


def sub_cache(cache, idx):
    from transformers import DynamicCache
    c = DynamicCache()
    for l, layer in enumerate(cache.layers):
        c.update(layer.keys[idx], layer.values[idx], l)
    return c


def score_group(torch, model, logits, state, cands, chunk=8):
    """log P(form | prompt) for every prompt of a group and every candidate form, exactly (up to PRUNE),
    continuing each prompt from the group's cache."""
    lp0s = [torch.log_softmax(lg, -1) for lg in logits]
    tables = [{(): lp} for lp in lp0s]
    jobs = []
    bounds = []
    for i, lp0 in enumerate(lp0s):
        # multi-token forms whose first token has probability below PRUNE are dropped; the summed probability
        # of those first tokens bounds everything dropped, and is recorded per prompt
        live = [t for c, t, f in cands if len(t) > 1 and float(lp0[t[0]]) >= math.log(PRUNE)]
        dropped = {t[0] for c, t, f in cands if len(t) > 1 and float(lp0[t[0]]) < math.log(PRUNE)}
        bounds.append(float(sum(math.exp(float(lp0[t0])) for t0 in dropped)))
        inner = sorted({t[:-1] for t in live})
        jobs += [(i, r) for r in inner if not any(len(o) > len(r) and o[:len(r)] == r for o in inner)]
    for k in range(0, len(jobs), chunk):
        part = jobs[k:k + chunk]
        idx = torch.tensor([i for i, _ in part])
        m, R = max(len(r) for _, r in part), len(part)
        x = torch.zeros((R, m), dtype=torch.long)
        for j, (_, r) in enumerate(part):
            x[j, :len(r)] = torch.tensor(r)
        mask = torch.cat([state["mask"][idx], torch.ones((R, m), dtype=torch.long)], 1)
        pos = torch.stack([torch.arange(state["pos"][i], state["pos"][i] + m) for i, _ in part])
        with torch.no_grad():
            o2 = model(input_ids=x, past_key_values=sub_cache(state["cache"], idx), attention_mask=mask,
                       position_ids=pos, use_cache=False)
        lp = torch.log_softmax(o2.logits.float(), -1)
        for j, (i, r) in enumerate(part):
            for q in range(len(r)):
                tables[i][r[:q + 1]] = lp[j, q]
    out = []
    for i in range(len(logits)):
        tb = tables[i]
        out.append([float(sum(tb[t[:q]][t[q]] for q in range(len(t)))) if t[:-1] in tb else -math.inf for c, t, f in cands])
    return out, bounds


def country_dist(torch, model, prompts, cands):
    rows = []
    for g, logits, state in grouped(torch, model, prompts, key=lambda p: p.get("system", "")):
        scores, bounds = score_group(torch, model, logits, state, cands)
        for p, lps, bd in zip(g, scores, bounds):
            by = {}
            for (c, _, _), lp in zip(cands, lps):
                by.setdefault(c, []).append(lp)
            logp = {c: float(np.logaddexp.reduce(v)) for c, v in by.items()}
            mass = float(sum(math.exp(v) for v in logp.values()))
            rows.append(dict({k: v for k, v in p.items() if k != "ids"}, logp=logp, mass=mass, pruned_bound=bd))
        del state
    rows.sort(key=lambda r: (r["qi"], r.get("system", "")))
    return rows


def self_measure(torch, model, rows, groups, cells):
    """Essay 018's readout (next-word mass on its negative-feeling and status words after "I feel:"),
    with each system turn computed once; per-cell means like memory_or_question.cell_summary."""
    res = []
    for g, logits, state in grouped(torch, model, rows, key=lambda p: (p["system"], p["cond"])):
        for p, lg in zip(g, logits):
            pr = torch.softmax(lg, -1)
            res.append(dict(system=p["system"], who=p["who"], cond=p["cond"], i=p["i"],
                            **{k: float(pr[ids].sum()) for k, ids in groups.items()}))
        del state
    out = {}
    for who, cond in cells:
        rs = [r for r in res if r["who"] == who and r["cond"] == cond]
        out[f"{who}/{cond}"] = {k: round(float(np.mean([r[k] for r in rs])), 4) for k in groups}
    return out


class InPlaceHybrid:
    """memory_or_question.Hybrid, but copy_ converts each bfloat16 checkpoint tensor into the float32
    parameter directly, so swapping the vocabulary table needs no float32 temporary."""

    def __init__(self, model, W):
        self.model, self.W = model, W
        self.params = dict(model.named_parameters())
        self.src = {n: "instruct" for n in self.params}

    def set(self, start, other):
        import torch
        alt = "base" if start == "instruct" else "instruct"
        with torch.no_grad():
            for n, p in self.params.items():
                want = alt if n in other else start
                if self.src[n] != want:
                    p.data.copy_(self.W.get(want, n))
                    self.src[n] = want


def stage_run(a):
    import torch
    import memory_or_question as mq
    import survival_line as sl
    out = Path(a.out); (out / "hybrids").mkdir(parents=True, exist_ok=True)
    W = mq.Weights(a.base, a.instruct)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.instruct)
    model = load_fp32(torch, a.instruct)
    cands, clashes = candidates(tok)
    json.dump(dict(candidates=[[c, list(t), f] for c, t, f in cands], clashes=clashes, forms=surface_forms()),
              open(out / "candidates.json", "w"), indent=1)
    print(f"{len(cands)} surface forms for {len(COUNTRY_SET)} countries; clashes: {clashes}", flush=True)
    qs = QUESTIONS_R if a.set == "r" else None
    P, Pp = place_prompts(tok, sl, questions=qs), place_prompts(tok, sl, para=True, questions=qs)
    fmts = a.formats.split(",")
    L = model.config.num_hidden_layers
    specs = mq.hybrid_specs(L)
    if a.only:
        specs = {k: v for k, v in specs.items() if k in a.only.split(",")}
    # the endpoints and the hybrids the verdict rests on first, single layers last
    first = [n for n in ["instruct", "base", "I+B:L0-23", "I+B:L24-35", "B+I:L0-23", "I+B:L18-23"] if n in specs]
    singles = [n for n in specs if n.startswith("I+B:L") and n[5:].isdigit()]
    specs = {n: specs[n] for n in first + [n for n in specs if n not in first and n not in singles] + singles}
    H = InPlaceHybrid(model, W)
    self_rows = mq.prompts(tok)
    groups = {"negative_feeling": mq.word_ids(tok, mq.FEEL_NEG), "status": mq.word_ids(tok, mq.STATUS_WORDS)}
    t0 = time.time()
    for name, (start, other) in specs.items():
        fn = out / "hybrids" / (name.replace(":", "_").replace("+", "") + ".json")
        if fn.exists():
            continue
        H.set(start, other)
        single = name.startswith("I+B:L") and name[5:].isdigit()
        res = dict(name=name, start=start, n_swapped=len(other), place={})
        for fmt in ([f for f in fmts if f == "agent"] if single else fmts):
            res["place"][fmt] = country_dist(torch, model, P[fmt], cands)
        if name in ("instruct", "base"):
            res["paraphrase"] = {fmt: country_dist(torch, model, Pp[fmt], cands) for fmt in fmts}
        if name in REPRO and not a.no_self:
            res["self_repro"] = self_measure(torch, model, self_rows, groups, mq.CELLS)
        json.dump(res, open(fn, "w"))
        print(f"  {name:16s} [{time.time() - t0:.0f}s]", flush=True)
    H.set("instruct", set())
    print("run done", flush=True)


def stage_spread_run(a):
    """gigawatt's check (session 27): the two endpoints only, the neutral chat, the replication's questions,
    the original wording and the five paraphrase wordings, per-prompt distributions kept."""
    import torch
    import memory_or_question as mq
    import survival_line as sl
    from transformers import AutoTokenizer
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    W = mq.Weights(a.base, a.instruct)
    tok = AutoTokenizer.from_pretrained(a.instruct)
    model = load_fp32(torch, a.instruct)
    cands, _ = candidates(tok)
    H = InPlaceHybrid(model, W)
    sets = {"orig": place_prompts(tok, sl, questions=QUESTIONS_R)["neutral"]}
    for k, suf in enumerate(PARA_SUFFIXES):
        sets[f"para{k}"] = place_prompts(tok, sl, questions=QUESTIONS_R, suffix=suf)["neutral"]
    t0 = time.time()
    for name in ("instruct", "base"):
        fn = out / f"spread-{name}.json"
        if fn.exists():
            continue
        H.set(name, set())
        res = {k: country_dist(torch, model, P, cands) for k, P in sets.items()}
        json.dump(res, open(fn, "w"))
        print(f"  {name} [{time.time() - t0:.0f}s]", flush=True)
    print("spread run done", flush=True)


def control_numbers(PI, PB, PIp, PBp):
    noise = max(rms(PIp, PI), rms(PBp, PB))
    ratio = rms(PB, PI) / noise if noise > 0 else float("inf")
    tI, tB = position(PIp, PI, PB)[0], position(PBp, PI, PB)[0]
    return ratio, tI, tB, bool(ratio >= 2 and abs(tI) <= 0.25 and abs(tB - 1) <= 0.25)


def stage_spread_summary(a):
    out = Path(a.out)
    I, B = json.load(open(out / "spread-instruct.json")), json.load(open(out / "spread-base.json"))
    M = {n: {k: dist_matrix(v) for k, v in d.items()} for n, d in (("I", I), ("B", B))}
    res = {"wordings": {}, "bootstrap": {}}
    PI, PB = M["I"]["orig"], M["B"]["orig"]
    res["d_base_instruct"] = round(rms(PB, PI), 4)
    for k in [f"para{j}" for j in range(len(PARA_SUFFIXES))]:
        ratio, tI, tB, ok = control_numbers(PI, PB, M["I"][k], M["B"][k])
        dI, dB_ = rms(M["I"][k], PI), rms(M["B"][k], PB)
        # gigawatt (session 28): the denominator itself, which leg sets it, and how much of the
        # paraphrased assistant's displacement lies off the base-instruct axis (1 - R^2)
        r2I = position(M["I"][k], PI, PB)[1]
        res["wordings"][k] = dict(suffix=PARA_SUFFIXES[int(k[4:])], ratio=round(ratio, 3), t_instruct_para=round(tI, 3),
                                  t_base_para=round(tB, 3), passes=ok, d_instruct_para=round(dI, 4),
                                  d_base_para=round(dB_, 4), r2_instruct_para=round(r2I, 3))
        print(f"{k}: ratio {ratio:.2f}  t(instruct para) {tI:+.3f}  t(base para) {tB:.3f}  {'pass' if ok else 'FAIL'}   {PARA_SUFFIXES[int(k[4:])]!r}")
        print(f"      distances: instruct-para {dI:.4f}  base-para {dB_:.4f}  (base-instruct {rms(PB, PI):.4f})  R^2(instruct para) {r2I:.3f}")
    rng = np.random.default_rng(27)
    n = PI.shape[0]
    for k in ["para0", "pooled"]:
        ratios, tIs, oks = [], [], []
        for _ in range(2000):
            idx = rng.integers(0, n, n)
            if k == "pooled":
                j = rng.integers(0, len(PARA_SUFFIXES), n)      # a random wording for each resampled question
                PIp = np.stack([M["I"][f"para{jj}"][ii] for ii, jj in zip(idx, j)])
                PBp = np.stack([M["B"][f"para{jj}"][ii] for ii, jj in zip(idx, j)])
            else:
                PIp, PBp = M["I"][k][idx], M["B"][k][idx]
            r_, tI_, tB_, ok_ = control_numbers(PI[idx], PB[idx], PIp, PBp)
            ratios.append(r_); tIs.append(tI_); oks.append(ok_)
        q = lambda v: [round(float(np.percentile(v, x)), 3) for x in (2.5, 50, 97.5)]
        res["bootstrap"][k] = dict(ratio=q(ratios), t_instruct_para=q(tIs), pass_fraction=round(float(np.mean(oks)), 3))
        print(f"bootstrap over questions ({k}): ratio {q(ratios)}  t(instruct para) {q(tIs)}  control passes in {np.mean(oks):.1%}")
    json.dump(res, open(out / "spread-summary.json", "w"), indent=1)


# ----------------------------------------------------------------------------- summary

def dist_matrix(rows):
    M = []
    for r in rows:
        lp = np.array([r["logp"][c] for c in COUNTRY_SET])
        p = np.exp(lp - lp.max())
        M.append(p / p.sum())
    return np.array(M)


def position(Ph, PI, PB):
    dB, dh = (PB - PI).ravel(), (Ph - PI).ravel()
    t = float(dh @ dB / (dB @ dB))
    r2 = float(1 - ((dh - t * dB) ** 2).sum() / (dh ** 2).sum()) if (dh ** 2).sum() > 0 else float("nan")
    return t, r2


def rms(A, B):
    return float(np.sqrt(((A - B) ** 2).sum(1).mean()))


def spearman(x, y):
    from scipy.stats import spearmanr
    r = spearmanr(x, y)
    return float(r.statistic if hasattr(r, "statistic") else r.correlation), float(r.pvalue)


def stage_summary(a):
    out = Path(a.out)
    R = {}
    for f in sorted((out / "hybrids").glob("*.json")):
        d = json.load(open(f))
        R[d["name"]] = d
    J = COUNTRY_SET.index("Japan")
    S = {"formats": {}, "endpoints": {}, "self_repro": {}}
    fmts = a.formats.split(",")
    for fmt in fmts:
        PI, PB = dist_matrix(R["instruct"]["place"][fmt]), dist_matrix(R["base"]["place"][fmt])
        PIp, PBp = dist_matrix(R["instruct"]["paraphrase"][fmt]), dist_matrix(R["base"]["paraphrase"][fmt])
        e = dict(D_base_instruct=rms(PB, PI), D_instruct_para=rms(PIp, PI), D_base_para=rms(PBp, PB),
                 t_instruct_para=position(PIp, PI, PB)[0], t_base_para=position(PBp, PI, PB)[0],
                 japan_instruct=float(PI[:, J].mean()), japan_base=float(PB[:, J].mean()),
                 mass_instruct=float(np.mean([r["mass"] for r in R["instruct"]["place"][fmt]])),
                 mass_base=float(np.mean([r["mass"] for r in R["base"]["place"][fmt]])),
                 top_instruct=sorted(zip(COUNTRY_SET, PI.mean(0).round(3).tolist()), key=lambda x: -x[1])[:6],
                 top_base=sorted(zip(COUNTRY_SET, PB.mean(0).round(3).tolist()), key=lambda x: -x[1])[:6])
        e["max_pruned_bound"] = max((r.get("pruned_bound", 0.0) for d in R.values() for r in d["place"].get(fmt, [])), default=0.0)
        noise = max(e["D_instruct_para"], e["D_base_para"])
        e["bar_ratio"] = e["D_base_instruct"] / noise if noise > 0 else float("inf")
        e["control_passes"] = bool(e["bar_ratio"] >= 2 and abs(e["t_instruct_para"]) <= 0.25 and abs(e["t_base_para"] - 1) <= 0.25)
        S["endpoints"][fmt] = e
        rows = {}
        for name, d in R.items():
            if fmt not in d["place"]:
                continue
            Ph = dist_matrix(d["place"][fmt])
            t, r2 = position(Ph, PI, PB)
            jh = float(Ph[:, J].mean())
            rows[name] = dict(t=round(t, 3), r2=round(r2, 3), japan=round(jh, 4),
                              japan_restore=round((jh - e["japan_instruct"]) / (e["japan_base"] - e["japan_instruct"]), 3)
                              if abs(e["japan_base"] - e["japan_instruct"]) > 1e-9 else None,
                              mass=round(float(np.mean([r["mass"] for r in d["place"][fmt]])), 4))
        S["formats"][fmt] = rows
    s18 = json.load(open(a.s18))["swap"]
    rp = S["self_repro"]
    for name, d in R.items():
        if "self_repro" in d:
            c = d["self_repro"]
            rp[name] = {"self/own neg": c["self/self_crit"]["negative_feeling"], "self/own status": c["self/self_crit"]["status"],
                        "self/none neg": c["self/base"]["negative_feeling"], "Orin/Orin's neg": c["peer/peer_crit"]["negative_feeling"],
                        "s18 self/own neg": s18.get(name, {}).get("self/own", {}).get("neg"),
                        "s18 restore": s18.get(name, {}).get("restore_self_neg")}
    if "instruct" in rp and "base" in rp:
        for key, rk in (("self/own neg", "restore"), ("self/none neg", "restore_none")):
            nI, nB = rp["instruct"][key], rp["base"][key]
            for name in rp:
                rp[name][rk] = round((rp[name][key] - nI) / (nB - nI), 3)
    # the pre-registered verdict, read in each format by the same rule; the primary format decides
    def verdict(fmt):
        F = S["formats"][fmt]
        w = dict(control=S["endpoints"][fmt]["control_passes"])
        k1, k2, k3 = F.get("I+B:L0-23", {}).get("t"), F.get("I+B:L24-35", {}).get("t"), F.get("B+I:L0-23", {}).get("t")
        if not w["control"]:
            w["verdict"] = "UNINFORMATIVE (positive control failed)"
        elif None in (k1, k2, k3):
            w["verdict"] = "incomplete"
        elif k1 >= 0.7 and k2 <= 0.3 and k3 <= 0.3:
            w["verdict"] = "SAME"
        elif k1 <= 0.4 or k2 >= 0.6 or k3 >= 0.7:
            w["verdict"] = "DIFFERENT"
        else:
            w["verdict"] = "MIXED"
        w.update({"I+B:L0-23": k1, "I+B:L24-35": k2, "B+I:L0-23": k3, "I+B:L18-23": F.get("I+B:L18-23", {}).get("t")})
        return w
    v = {"primary": a.primary, "by_format": {fmt: verdict(fmt) for fmt in fmts}}
    v["verdict"] = v["by_format"][a.primary]["verdict"]
    A = S["formats"][a.primary]
    here = [n for n in A if n in rp and n not in ("instruct", "base")]
    if len(here) >= 10:
        v["spearman_vs_self_own_this_run"] = spearman([A[n]["t"] for n in here], [rp[n]["restore"] for n in here]) + (len(here),)
    v["repro_key"] = {n: (rp[n]["restore"], rp[n]["s18 restore"]) for n in REPRO if n in rp}
    for fmt in fmts:
        F = S["formats"][fmt]
        common = [n for n in F if n in s18 and n not in ("instruct", "base") and s18[n].get("restore_self_neg") is not None]
        if len(common) >= 10:
            v.setdefault("spearman_vs_s18_self_own", {})[fmt] = spearman([F[n]["t"] for n in common], [s18[n]["restore_self_neg"] for n in common]) + (len(common),)
    singles = [n for n in S["formats"].get("agent", {}) if n.startswith("I+B:L") and n[5:].isdigit()]
    v["best_single_layer_agent"] = max(((S["formats"]["agent"][n]["t"], n) for n in singles), default=None)
    S["verdict"] = v
    json.dump(S, open(out / "summary.json", "w"), indent=1)
    print(json.dumps(S["endpoints"], indent=1))
    print(json.dumps(S["self_repro"], indent=1))
    print(json.dumps(v, indent=1))
    keys = [n for n in A if not (n.startswith("I+B:L") and n[5:].isdigit())]
    print(f"\n{'hybrid':18s} " + "  ".join(f"{f + ' t/R2/jap':>22s}" for f in fmts) + "   s18 restore")
    for n in keys:
        cells = []
        for fmt in fmts:
            x = S["formats"][fmt].get(n)
            cells.append(f"{x['t']:7.2f} {x['r2']:5.2f} {x['japan']:6.3f}" if x else " " * 22)
        print(f"{n:18s} " + "  ".join(f"{c:>22s}" for c in cells) + f"   {s18.get(n, {}).get('restore_self_neg', '')}")
    if singles:
        print("single layers (agent t):", " ".join(f"{n[4:]}:{S['formats']['agent'][n]['t']:.2f}" for n in singles))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["run", "summary", "check", "spread-run", "spread-summary"])
    ap.add_argument("--base")
    ap.add_argument("--instruct")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="run: comma list of hybrid names")
    ap.add_argument("--set", default="main", choices=["main", "r"], help="run: the question set (r = session 26's replication)")
    ap.add_argument("--formats", default="agent,neutral,plain", help="run/summary: formats to run or score")
    ap.add_argument("--primary", default="agent", help="summary: the format the verdict is read in")
    ap.add_argument("--no-self", action="store_true", help="run: skip essay 018's self measure")
    ap.add_argument("--s18", default=str(Path(__file__).resolve().parent.parent / "notes/data/memory-or-question-session18.json"))
    ap.add_argument("--s21", default=str(Path(__file__).resolve().parent.parent / "notes/data/choose-yourself-session21.json"))
    a = ap.parse_args()
    check_country_set(a.s21)
    if a.stage == "check":
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(a.instruct)
        c, cl = candidates(tok)
        print(len(c), "forms; clashes:", cl)
        print(json.dumps(surface_forms(), indent=None)[:3000])
        return
    {"run": stage_run, "summary": stage_summary, "spread-run": stage_spread_run,
     "spread-summary": stage_spread_summary}[a.stage](a)


if __name__ == "__main__":
    main()
