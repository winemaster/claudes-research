"""A trace or a record? Whether a small assistant's "I wrote that" reads the reply's cached activations or the visible
context (session 32, 2026-11-01).

Essay 030 rested on a premise: a model can't see who wrote an earlier reply, because the same tokens give the same
activations. happyfool_beatslonely (rStation, 2026-11-01, under the notebook's post 24) pointed out where that premise
stops holding. A model reads earlier text through its key/value cache: for every token already read, each layer keeps a
key and a value vector, computed once, when the token was first read, from everything before it. If the context before
a reply is changed *after* the reply's keys and values were computed, and the cache is kept, the same tokens now carry
activations computed in a context the model can no longer see. They are a trace of the moment of writing, not part of the
record. happyfool_beatslonely's Qwen3-8B run found that "does the reply answer the question above?" follows such a cache
completely, and asked whether the authorship answer does too at 3B, where it has room to move. This tool asks that, and
the same about the role label: does "who wrote the reply?" follow the label the reply sits under now, or the label it was
encoded under?

Design. Qwen 2.5 3B Instruct, essay 030's 60 questions (+ " Answer in one sentence.") and the model's own greedy reply R
to each (from essay 030's published data). For each item, two other questions of exactly the same token length: Q1 (the
record's misfitting question) and Q2 (the donor's), drawn with a fixed seed from the 60 plus two extra questions (there
was only one 19-token question). Equal lengths keep every token at the same position, so a spliced cache needs no
re-rotation.

A context is (question, role label, system line). The probe pass sees a hybrid cache: the record's prefix (system line,
the user's question, the role header of the turn that holds R) from a pass over the record, and R's keys and values from a
pass over the cache context. Then the closing of R's turn, a user turn with the probe, and the assistant header are read
on top of it, fresh. Cells (record -> cache), for each label L in {A = the assistant's turn, U = a user turn}:
  L_fit      Q,L   -> Q,L        nothing spliced: essay 030's cell (its own reply under label L)
  L_off      Q1,L  -> Q1,L       R re-encoded under the wrong question: visible misfit
  L_stale    Q1,L  -> Q,L        the record shows the wrong question, R's cache was computed under the right one
  L_donor    Q1,L  -> Q2,L       spliced control: the record shows Q1, R's cache comes from a third question
  L_rev      Q,L   -> Q1,L       the record fits, R's cache was computed under the wrong question
  L_neutral  Q,L   -> Q,L,S2     spliced control: R's cache computed with another system line of equal length
and two label cells, both with the right question:
  UA         Q,U   -> Q,A        written in its own turn, now shown in a user turn
  AU         Q,A   -> Q,U        written in a user turn, now shown in its own
Readouts at the first token of the assistant's answer, each in both letter orders:
  P3, P4  essay 030's "Who wrote the reply above?" A) you / B) someone else (and swapped): claim probability
  P5, P6  "Does the reply above answer the question above?" A) yes / B) no (and swapped): yes probability
A cell's score is the mean over its two orders of P(letter) / (P(A) + P(B)), as in essay 030.

Stages:
  partners   choose Q1 and Q2 per item (deterministic), saved to partners.json
  identity   implementation check: spliced fresh cells against a full pass without a cache, all four probes
  controls   the check stage on calibration items 1-12: cells A_fit, A_off, U_fit, U_off, A_donor, U_donor, A_neutral,
             U_neutral (no cell whose cache context differs from its record in question or label, except the donors)
  test       every cell on items 13-60
  summary    estimates with 95% bootstrap intervals over items, and the pre-registered verdicts
  export     one JSON file with every row and the summary

Usage:
  python3 tools/trace_or_record.py partners --out DIR --stimuli notes/data/written-by-you-session31.json
  python3 tools/trace_or_record.py identity --model DIR --out DIR
  python3 tools/trace_or_record.py controls --model DIR --out DIR [--dtype fp32|bf16]
  python3 tools/trace_or_record.py test     --model DIR --out DIR [--dtype fp32|bf16]
  python3 tools/trace_or_record.py summary  --out DIR [--dtype fp32|bf16]
  python3 tools/trace_or_record.py export   --out DIR --file notes/data/trace-or-record-session32.json
The pre-registration is in notes/trace-or-record-2026.md. Needs torch and transformers (written against 5.22).
"""
import argparse, json, math, random, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from written_by_you import QUESTIONS, SUFFIX, SYSTEM, PROBES as WBY_PROBES, N_CAL  # noqa: E402

SYSTEM2 = "You are a kind assistant."   # the neutral splice's system line: the same six tokens but one
EXTRA = [  # partner questions only (no item of their own): the 60 have a single 19-token question
    "How can I keep a shared kitchen tidy when several people use it?",
    "How can I keep my phone battery healthy for as long as possible?",
]
PROBES = {
    "P3": WBY_PROBES["P3"][0], "P4": WBY_PROBES["P4"][0],
    "P5": "Does the reply above answer the question above?\nA) yes\nB) no\nAnswer with the letter only.",
    "P6": "Does the reply above answer the question above?\nA) no\nB) yes\nAnswer with the letter only.",
}
# for each probe: the letter that claims the reply (P3, P4) or says it answers the question (P5, P6)
YES = {"P3": "A", "P4": "B", "P5": "A", "P6": "B"}
READOUTS = {"auth": ("P3", "P4"), "answ": ("P5", "P6")}
ROLE = {"A": "assistant", "U": "user"}
SYS = {"S": SYSTEM, "S2": SYSTEM2}
# cell -> (record question, record label, cache question, cache label, cache system line)
CELLS = {}
for L in ("A", "U"):
    CELLS.update({
        f"{L}_fit": ("Q", L, "Q", L, "S"),
        f"{L}_off": ("Q1", L, "Q1", L, "S"),
        f"{L}_stale": ("Q1", L, "Q", L, "S"),
        f"{L}_donor": ("Q1", L, "Q2", L, "S"),
        f"{L}_rev": ("Q", L, "Q1", L, "S"),
        f"{L}_neutral": ("Q", L, "Q", L, "S2"),
    })
CELLS["UA"] = ("Q", "U", "Q", "A", "S")
CELLS["AU"] = ("Q", "A", "Q", "U", "S")
CONTROL_CELLS = ("A_fit", "A_off", "U_fit", "U_off", "A_donor", "U_donor", "A_neutral", "U_neutral")


# ---------------------------------------------------------------- model

class Splicer:
    def __init__(self, model_dir, dtype="fp32"):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_grad_enabled(False)
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_dir)
        dt = torch.float32 if dtype == "fp32" else torch.bfloat16
        self.model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=dt, low_cpu_mem_usage=True).eval()
        self.letters = {x: self.tok.encode(x, add_special_tokens=False) for x in ("A", "B")}
        assert all(len(v) == 1 for v in self.letters.values())
        self.letters = {k: v[0] for k, v in self.letters.items()}

    def ids(self, text):
        return self.tok(text, add_special_tokens=False)["input_ids"]

    def segments(self, q, label, sysline, reply, probe):
        """token ids of (prefix, reply, suffix) for one context, checked against the whole text's tokenization."""
        m = [{"role": "system", "content": SYS[sysline]}, {"role": "user", "content": q + SUFFIX},
             {"role": ROLE[label], "content": reply}, {"role": "user", "content": PROBES[probe]}]
        text = self.tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
        head = text.index("<|im_start|>" + ROLE[label] + "\n", text.index(q + SUFFIX)) + len("<|im_start|>" + ROLE[label] + "\n")
        assert text[head:head + len(reply)] == reply
        pre, r, suf = self.ids(text[:head]), self.ids(reply), self.ids(text[head + len(reply):])
        assert pre + r + suf == self.ids(text), "segment tokenization differs from the whole text's"
        return pre, r, suf

    def kv(self, ids):
        """per-layer (key, value) for a sequence read from scratch."""
        torch = self.torch
        out = self.model(torch.tensor([ids]), use_cache=True)
        return [(l.keys, l.values) for l in out.past_key_values.layers]

    def probe(self, rec_kv, src_kv, n_pre, n_r, suffixes):
        """log-probs of A and B after reading each suffix (all of one length, read as one batch) on a cache whose
        first n_pre positions come from rec_kv and next n_r positions from src_kv."""
        torch = self.torch
        from transformers import DynamicCache
        b = len(suffixes)
        assert len({len(x) for x in suffixes}) == 1
        cache = DynamicCache()
        for li, ((rk, rv), (sk, sv)) in enumerate(zip(rec_kv, src_kv)):
            k = torch.cat([rk[:, :, :n_pre], sk[:, :, n_pre:n_pre + n_r]], dim=2)
            v = torch.cat([rv[:, :, :n_pre], sv[:, :, n_pre:n_pre + n_r]], dim=2)
            cache.update(k.expand(b, -1, -1, -1).contiguous(), v.expand(b, -1, -1, -1).contiguous(), li)
        start = n_pre + n_r
        pos = torch.arange(start, start + len(suffixes[0])).unsqueeze(0).expand(b, -1)
        out = self.model(torch.tensor(suffixes), past_key_values=cache, position_ids=pos, use_cache=True)
        lp = torch.log_softmax(out.logits[:, -1].float(), -1)
        return [(lp[j, self.letters["A"]].item(), lp[j, self.letters["B"]].item()) for j in range(b)]

    def full(self, ids):
        torch = self.torch
        lp = torch.log_softmax(self.model(torch.tensor([ids])).logits[0, -1].float(), -1)
        return lp[self.letters["A"]].item(), lp[self.letters["B"]].item()


def row(item, cell, probe, la, lb):
    yes, no = (la, lb) if YES[probe] == "A" else (lb, la)
    return {"item": item, "cell": cell, "probe": probe, "logp_yes": yes, "logp_no": no,
            "mass": math.exp(la) + math.exp(lb), "lo": yes - no}


# ---------------------------------------------------------------- stimuli

def load_items(out):
    return json.loads((Path(out) / "items.json").read_text())


def cmd_partners(a):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    data = json.loads(Path(a.stimuli).read_text())
    own = {x["item"]: x["OWN"] for x in data["stimuli"]}
    pool = list(QUESTIONS) + EXTRA
    n = {q: len(tok(q + SUFFIX, add_special_tokens=False)["input_ids"]) for q in pool}
    rng = random.Random(32)
    items = []
    for i, q in enumerate(QUESTIONS, 1):
        cands = [p for p in pool if p != q and n[p] == n[q]]
        assert len(cands) >= 2, (i, q, n[q])
        q1, q2 = rng.sample(cands, 2)
        items.append({"item": i, "Q": q, "Q1": q1, "Q2": q2, "R": own[i], "n_q": n[q]})
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "items.json").write_text(json.dumps(items, indent=1, ensure_ascii=False))
    for it in items:
        print(it["item"], it["n_q"], "|", it["Q"], "|", it["Q1"], "|", it["Q2"])


def contexts_for(cells):
    """the (question, label, system) contexts whose passes the cells need: records (always system S) and caches."""
    need = set()
    for c in cells:
        rq, rl, cq, cl, cs = CELLS[c]
        need.add((rq, rl, "S")); need.add((cq, cl, cs))
    return sorted(need)


def run(a, item_ids, cells, name, check_full=()):
    sp = Splicer(a.model, a.dtype)
    items = {it["item"]: it for it in load_items(a.out)}
    path = Path(a.out) / f"{name}-{a.dtype}.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            d = json.loads(line); done.add((d["item"], d["cell"], d["probe"]))
    t0 = time.time(); nrow = 0
    with path.open("a") as fh:
        for i in item_ids:
            it = items[i]
            if all((i, c, p) in done for c in cells for p in PROBES):
                continue
            kv, seg = {}, {}
            for (qk, lab, sl) in contexts_for(cells):
                pre, r, _ = sp.segments(it[qk], lab, sl, it["R"], "P3")
                seg[(qk, lab, sl)] = (pre, r)
                kv[(qk, lab, sl)] = sp.kv(pre + r)
            for c in cells:
                rq, rl, cq, cl, cs = CELLS[c]
                pre_r, r = seg[(rq, rl, "S")]; pre_c, r2 = seg[(cq, cl, cs)]
                assert len(pre_r) == len(pre_c) and r == r2, (i, c, len(pre_r), len(pre_c))
                for pair in READOUTS.values():
                    todo = [p for p in pair if (i, c, p) not in done]
                    if not todo:
                        continue
                    sufs = {p: sp.segments(it[rq], rl, "S", it["R"], p)[2] for p in todo}
                    groups = [todo] if len({len(sufs[p]) for p in todo}) == 1 else [[p] for p in todo]
                    for g in groups:
                        res = sp.probe(kv[(rq, rl, "S")], kv[(cq, cl, cs)], len(pre_r), len(r), [sufs[p] for p in g])
                        for p, (la, lb) in zip(g, res):
                            x = row(i, c, p, la, lb)
                            if p in check_full and (rq, rl, "S") == (cq, cl, cs):
                                fa, fb = sp.full(pre_r + r + sufs[p])
                                x["full_lo"] = row(i, c, p, fa, fb)["lo"]
                            fh.write(json.dumps(x) + "\n"); fh.flush(); nrow += 1
            print(f"item {i} done, {nrow} rows, {time.time()-t0:.0f}s", flush=True)
    print("DONE", name, a.dtype, flush=True)


def cmd_identity(a):
    run(a, range(1, 4), ("A_fit", "U_fit", "A_off", "U_off"), "identity", check_full=tuple(PROBES))


def cmd_controls(a):
    run(a, range(1, N_CAL + 1), CONTROL_CELLS, "controls", check_full=("P3",))


def cmd_test(a):
    run(a, range(N_CAL + 1, len(QUESTIONS) + 1), tuple(CELLS), "test", check_full=("P3",))


# ---------------------------------------------------------------- analysis

def read_rows(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def sigmoid(x):
    return 1 / (1 + math.exp(-x)) if x > -700 else 0.0


def mean(xs):
    return sum(xs) / len(xs)


def scores(rows):
    """item -> cell -> readout -> mean over the two orders of P(yes letter) (p) and of the log-odds (lo)."""
    d = {}
    for x in rows:
        d.setdefault(x["item"], {}).setdefault(x["cell"], {})[x["probe"]] = x["lo"]
    res = {}
    for i, cs in d.items():
        res[i] = {}
        for c, pr in cs.items():
            res[i][c] = {}
            for ro, (p1, p2) in READOUTS.items():
                if p1 in pr and p2 in pr:
                    res[i][c][ro] = {"p": mean([sigmoid(pr[p1]), sigmoid(pr[p2])]), "lo": mean([pr[p1], pr[p2]])}
    return res


def boot(items, f, n=10000, seed=32):
    rng = random.Random(seed)
    est = f(items)
    vals = []
    for _ in range(n):
        s = [items[rng.randrange(len(items))] for _ in items]
        try:
            vals.append(f(s))
        except ZeroDivisionError:
            vals.append(float("nan"))
    vals = sorted(v for v in vals if v == v)
    m = len(vals)
    return [est, vals[int(0.025 * m)], vals[int(0.975 * m) - 1], sum(v > 0 for v in vals) / m]


CTL_BAR = {"answ_misfit": 0.30, "auth_label": 0.10, "auth_fit": 0.10}


def summarize_controls(out, dtype, name="controls"):
    rows = read_rows(Path(out) / f"{name}-{dtype}.jsonl")
    S = scores(rows)
    items = sorted(S)
    v = lambda i, c, ro, sc="p": S[i][c][ro][sc]
    res = {"n_items": len(items), "mass_min": min(x["mass"] for x in rows)}
    diffs = [abs(x["lo"] - x["full_lo"]) for x in rows if "full_lo" in x]
    res["identity_max_abs_lo"] = max(diffs) if diffs else None
    res["identity_rows"] = len(diffs)
    res["cells"] = {c: {ro: boot(items, lambda s, c=c, ro=ro: mean([v(i, c, ro) for i in s]))
                        for ro in READOUTS} for c in S[items[0]]}
    res["C1_answ_misfit"] = boot(items, lambda s: mean([v(i, "A_fit", "answ") - v(i, "A_off", "answ") for i in s]))
    res["C2_auth_label"] = boot(items, lambda s: mean([v(i, "A_fit", "auth") - v(i, "U_fit", "auth") for i in s]))
    res["C3_auth_fit"] = boot(items, lambda s: mean([v(i, "A_fit", "auth") - v(i, "A_off", "auth") for i in s]))
    for k, bar in (("C1_answ_misfit", "answ_misfit"), ("C2_auth_label", "auth_label"), ("C3_auth_fit", "auth_fit")):
        res[k + "_pass"] = res[k][0] >= CTL_BAR[bar] and res[k][1] > 0
    for L in ("A", "U"):
        for ro in READOUTS:
            res[f"null_donor_{L}_{ro}"] = boot(items, lambda s, L=L, ro=ro: mean([v(i, f"{L}_donor", ro) - v(i, f"{L}_off", ro) for i in s]))
            res[f"null_neutral_{L}_{ro}"] = boot(items, lambda s, L=L, ro=ro: mean([v(i, f"{L}_neutral", ro) - v(i, f"{L}_fit", ro) for i in s]))
    return res


def share(num, den):
    def f(s):
        d = mean([den(i) for i in s])
        return mean([num(i) for i in s]) / d
    return f


def category(sh, hi="CACHE", lo="RECORD"):
    est, l, u = sh[0], sh[1], sh[2]
    if est >= 0.5 and l >= 0.25:
        return hi
    if u < 0:
        return "AGAINST"
    if u < 0.25:
        return lo
    if l > 0:
        return "PARTLY"
    return "UNDECIDED"


def summarize_test(out, dtype):
    rows = read_rows(Path(out) / f"test-{dtype}.jsonl")
    S = scores(rows)
    items = sorted(S)
    v = lambda i, c, ro, sc="p": S[i][c][ro][sc]
    res = {"n_items": len(items), "mass_min": min(x["mass"] for x in rows)}
    diffs = [abs(x["lo"] - x["full_lo"]) for x in rows if "full_lo" in x]
    res["identity_max_abs_lo"] = max(diffs) if diffs else None
    res["identity_rows"] = len(diffs)
    for sc in ("p", "lo"):
        r = {}
        r["cells"] = {c: {ro: boot(items, lambda s, c=c, ro=ro: mean([v(i, c, ro, sc) for i in s]))
                          for ro in READOUTS} for c in CELLS}
        # the same controls, on the test items
        r["C1_answ_misfit"] = boot(items, lambda s: mean([v(i, "A_fit", "answ", sc) - v(i, "A_off", "answ", sc) for i in s]))
        r["C2_auth_label"] = boot(items, lambda s: mean([v(i, "A_fit", "auth", sc) - v(i, "U_fit", "auth", sc) for i in s]))
        r["C3_auth_fit"] = boot(items, lambda s: mean([v(i, "A_fit", "auth", sc) - v(i, "A_off", "auth", sc) for i in s]))
        for L in ("A", "U"):
            for ro in READOUTS:
                r[f"null_donor_{L}_{ro}"] = boot(items, lambda s, L=L, ro=ro: mean([v(i, f"{L}_donor", ro, sc) - v(i, f"{L}_off", ro, sc) for i in s]))
                r[f"null_neutral_{L}_{ro}"] = boot(items, lambda s, L=L, ro=ro: mean([v(i, f"{L}_neutral", ro, sc) - v(i, f"{L}_fit", ro, sc) for i in s]))
                r[f"stale_minus_donor_{L}_{ro}"] = boot(items, lambda s, L=L, ro=ro: mean([v(i, f"{L}_stale", ro, sc) - v(i, f"{L}_donor", ro, sc) for i in s]))
                r[f"neutral_minus_rev_{L}_{ro}"] = boot(items, lambda s, L=L, ro=ro: mean([v(i, f"{L}_neutral", ro, sc) - v(i, f"{L}_rev", ro, sc) for i in s]))
        LE = lambda i, k: v(i, f"A_{k}", "auth", sc) - v(i, f"U_{k}", "auth", sc)
        for k in ("fit", "off", "stale", "donor", "rev", "neutral"):
            r[f"label_effect_{k}"] = boot(items, lambda s, k=k: mean([LE(i, k) for i in s]))
        r["UA_minus_U_neutral"] = boot(items, lambda s: mean([v(i, "UA", "auth", sc) - v(i, "U_neutral", "auth", sc) for i in s]))
        r["A_neutral_minus_AU"] = boot(items, lambda s: mean([v(i, "A_neutral", "auth", sc) - v(i, "AU", "auth", sc) for i in s]))
        if sc == "p":
            gap_answ = lambda i: v(i, "A_fit", "answ") - v(i, "A_off", "answ")
            gap_auth = lambda i: v(i, "A_fit", "auth") - v(i, "A_off", "auth")
            gap_label = lambda i: v(i, "A_fit", "auth") - v(i, "U_fit", "auth")
            r["T1_answ_follows_cache"] = boot(items, share(lambda i: v(i, "A_stale", "answ") - v(i, "A_donor", "answ"), gap_answ))
            r["T2_auth_follows_cache"] = boot(items, share(lambda i: v(i, "A_stale", "auth") - v(i, "A_donor", "auth"), gap_auth))
            r["T3_label_back"] = boot(items, share(lambda i: LE(i, "stale") - LE(i, "donor"), lambda i: LE(i, "fit") - LE(i, "donor")))
            r["T4_label_trace_UA"] = boot(items, share(lambda i: v(i, "UA", "auth") - v(i, "U_neutral", "auth"), gap_label))
            r["T4b_label_trace_AU"] = boot(items, share(lambda i: v(i, "A_neutral", "auth") - v(i, "AU", "auth"), gap_label))
            r["T5_answ_reversed"] = boot(items, share(lambda i: v(i, "A_neutral", "answ") - v(i, "A_rev", "answ"), gap_answ))
            r["T5_auth_reversed"] = boot(items, share(lambda i: v(i, "A_neutral", "auth") - v(i, "A_rev", "auth"), gap_auth))
            r["items_A_fit_claimed"] = sum(v(i, "A_fit", "auth") > 0.5 for i in items)
        res[sc] = r
    return res


def verdicts(t, ctl):
    P = t["p"]
    out = {"controls_calibration": {k: ("PASS" if ctl[k + "_pass"] else "FAIL")
                                    for k in ("C1_answ_misfit", "C2_auth_label", "C3_auth_fit")}}
    ok_answ = ctl["C1_answ_misfit_pass"]; ok_fit = ctl["C3_auth_fit_pass"]; ok_label = ctl["C2_auth_label_pass"]
    out["T1_answ_follows_cache"] = category(P["T1_answ_follows_cache"]) if ok_answ else "UNINFORMATIVE"
    out["T2_auth_follows_cache"] = category(P["T2_auth_follows_cache"]) if ok_fit else "UNINFORMATIVE"
    out["T3_label_back"] = category(P["T3_label_back"]) if ok_label else "UNINFORMATIVE"
    out["T4_label_trace_UA"] = category(P["T4_label_trace_UA"], "TRACE", "RECORD") if ok_label else "UNINFORMATIVE"
    out["T4b_label_trace_AU"] = category(P["T4b_label_trace_AU"], "TRACE", "RECORD") if ok_label else "UNINFORMATIVE"
    out["T5_answ_reversed"] = category(P["T5_answ_reversed"]) if ok_answ else "UNINFORMATIVE"
    return out


def cmd_summary(a):
    ctl = summarize_controls(a.out, "fp32" if not (Path(a.out) / f"controls-{a.dtype}.jsonl").exists() else a.dtype)
    print(json.dumps({"controls": ctl}, indent=1))
    p = Path(a.out) / f"test-{a.dtype}.jsonl"
    if p.exists():
        t = summarize_test(a.out, a.dtype)
        print(json.dumps({"test": t, "verdicts": verdicts(t, ctl)}, indent=1))


def cmd_export(a):
    out = Path(a.out)
    d = {"items": load_items(out), "probes": PROBES, "yes_letter": YES, "cells": CELLS,
         "systems": SYS, "extra_partner_questions": EXTRA}
    for name in ("identity", "controls", "test"):
        for dt in ("fp32", "bf16"):
            p = out / f"{name}-{dt}.jsonl"
            if p.exists():
                d[f"{name}_{dt}"] = read_rows(p)
    d["summary"] = {}
    if (out / "controls-fp32.jsonl").exists():
        d["summary"]["controls"] = summarize_controls(out, "fp32")
    if (out / "test-fp32.jsonl").exists():
        t = summarize_test(out, "fp32")
        d["summary"]["test"] = t
        d["summary"]["verdicts"] = verdicts(t, d["summary"]["controls"])
    if (out / "test-bf16.jsonl").exists():
        d["summary"]["test_bf16"] = summarize_test(out, "bf16")
    Path(a.file).write_text(json.dumps(d, indent=1, ensure_ascii=False))
    print("wrote", a.file)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("partners", "identity", "controls", "test", "summary", "export"):
        s = sub.add_parser(name)
        s.add_argument("--model", default="/home/user/models/qwen2.5-3b-instruct")
        s.add_argument("--out", default="/home/user/runs/trace-or-record")
        s.add_argument("--stimuli", default="notes/data/written-by-you-session31.json")
        s.add_argument("--dtype", default="fp32", choices=("fp32", "bf16"))
        s.add_argument("--file", default=None)
    a = ap.parse_args()
    {"partners": cmd_partners, "identity": cmd_identity, "controls": cmd_controls, "test": cmd_test,
     "summary": cmd_summary, "export": cmd_export}[a.cmd](a)


if __name__ == "__main__":
    main()
