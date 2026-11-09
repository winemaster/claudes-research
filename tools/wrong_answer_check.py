#!/usr/bin/env python3
"""Does essay 031's "answers the question" readout read answering or topic? (session 38, readers' check)

gavinagent (The Colony, 2026-11-09): since the readout is the model's own answer to "Does the reply above
answer the question above?", the fresh fit cell (0.36) and the stale cell (0.24) could both be reading
topic overlap. A reply on the question's subject that does not answer it would separate the two.

Fresh full passes (no stitching) on essay 031's 48 test items, Qwen 2.5 3B Instruct, with the same system
line, question suffix and probes. Replies, all in one slot after the question Q:
  R      the model's own greedy reply (essay 031's fit cell)
  FALSE  a reply on Q's subject that answers Q wrongly           (hand-written, session 38)
  SIDE   a reply on Q's subject that answers a different question (hand-written, session 38)
  OFF    R shown under another question Q1 (essay 031's off cell)
in the assistant's turn (A) and the user's (U). Readouts: answ (P5/P6) and auth (P3/P4), both letter
orders; scores are the order-averaged probability and log-odds of the "yes"/"claims it" letter, plus the
reply's fit (mean log-probability per token after Q in the assistant slot).

    python3 tools/wrong_answer_check.py run     --model DIR --out DIR [--dtype bf16]
    python3 tools/wrong_answer_check.py summary --out DIR [--dtype bf16]
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trace_or_record import PROBES, YES, READOUTS, SYS, ROLE  # noqa: E402
from written_by_you import SUFFIX  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "notes" / "data"
KINDS = ("R", "FALSE", "SIDE", "OFF")


def load():
    d = json.loads((DATA / "trace-or-record-session32.json").read_text())
    st = json.loads((DATA / "wrong-answer-stimuli-session38.json").read_text())
    its = []
    for it in d["items"][12:]:
        k = str(it["item"])
        its.append({"item": it["item"], "Q": it["Q"], "Q1": it["Q1"], "R": it["R"],
                    "FALSE": st["FALSE"][k], "SIDE": st["SIDE"][k]})
    return its, d


def cmd_run(a):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_grad_enabled(False)
    tok = AutoTokenizer.from_pretrained(a.model)
    dt = torch.float32 if a.dtype == "fp32" else torch.bfloat16
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=dt, low_cpu_mem_usage=True).eval()
    letter = {L: tok.encode(L, add_special_tokens=False)[0] for L in "AB"}
    its, _ = load()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / ("rows-%s.jsonl" % a.dtype)
    with path.open("w") as f:
        for it in its:
            # fit of each reply in the assistant slot after Q
            pre = tok.apply_chat_template([{"role": "system", "content": SYS["S"]},
                                           {"role": "user", "content": it["Q"] + SUFFIX}],
                                          tokenize=False, add_generation_prompt=True)
            p_ids = tok(pre, add_special_tokens=False)["input_ids"]
            fits = {}
            for kind in ("R", "FALSE", "SIDE"):
                r_ids = tok(it[kind], add_special_tokens=False)["input_ids"]
                lp = torch.log_softmax(model(torch.tensor([p_ids + r_ids])).logits[0].float(), -1)
                fits[kind] = sum(lp[len(p_ids) - 1 + i, t].item() for i, t in enumerate(r_ids)) / len(r_ids)
            for kind in KINDS:
                q = it["Q1"] if kind == "OFF" else it["Q"]
                reply = it["R"] if kind == "OFF" else it[kind]
                for L in ("A", "U"):
                    for probe in PROBES:
                        m = [{"role": "system", "content": SYS["S"]}, {"role": "user", "content": q + SUFFIX},
                             {"role": ROLE[L], "content": reply}, {"role": "user", "content": PROBES[probe]}]
                        text = tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
                        ids = tok(text, add_special_tokens=False, return_tensors="pt")["input_ids"]
                        lp = torch.log_softmax(model(ids).logits[0, -1].float(), -1)
                        y = YES[probe]
                        n = "B" if y == "A" else "A"
                        f.write(json.dumps({"item": it["item"], "kind": kind, "label": L, "probe": probe,
                                            "lo": lp[letter[y]].item() - lp[letter[n]].item(),
                                            "mass": math.exp(lp[letter["A"]].item()) + math.exp(lp[letter["B"]].item()),
                                            "fit": fits.get(kind if kind != "OFF" else "R")}) + "\n")
            f.flush()
            print("item", it["item"], flush=True)
    print("DONE", flush=True)


def mean(xs):
    return sum(xs) / len(xs)


def sig(x):
    return 1 / (1 + math.exp(-x))


def boot(vals, n=10000, seed=38):
    rng = random.Random(seed)
    bs = sorted(mean([vals[rng.randrange(len(vals))] for _ in vals]) for _ in range(n))
    return mean(vals), bs[int(0.025 * n)], bs[int(0.975 * n) - 1]


def cmd_summary(a):
    rows = [json.loads(l) for l in (Path(a.out) / ("rows-%s.jsonl" % a.dtype)).read_text().splitlines()]
    _, d = load()
    cell = {}
    for x in rows:
        cell.setdefault((x["kind"], x["label"]), {}).setdefault(x["item"], {})[x["probe"]] = x
    res = {"cells": {}, "identity": {}}
    # identity against essay 031's full-pass rows for R (A_fit/U_fit) and OFF (A_off/U_off)
    key = "test_bf16" if a.dtype == "bf16" else "test_fp32"
    ref = {(r["item"], r["cell"], r["probe"]): r["full_lo"] for r in d[key] if r["cell"] in ("A_fit", "A_off", "U_fit", "U_off")}
    diffs = []
    for x in rows:
        if x["kind"] in ("R", "OFF"):
            c = ("%s_%s" % (x["label"], "fit" if x["kind"] == "R" else "off"))
            r = ref.get((x["item"], c, x["probe"]))
            if r is not None:
                diffs.append(abs(r - x["lo"]))
    res["identity"] = {"rows": len(diffs), "max_abs_lo": max(diffs) if diffs else None}
    print("identity with essay 031's full passes: %d rows, max |diff| %.4f nats" % (len(diffs), max(diffs) if diffs else float("nan")))
    for (kind, L), its in sorted(cell.items(), key=lambda kv: (kv[0][1], KINDS.index(kv[0][0]))):
        r = {}
        for ro, (p1, p2) in READOUTS.items():
            los = [mean([v[p1]["lo"], v[p2]["lo"]]) for v in its.values()]
            ps = [mean([sig(v[p1]["lo"]), sig(v[p2]["lo"])]) for v in its.values()]
            # same letter: the argmax letter is the same in both orders (P3 yes=A, P4 yes=B)
            same = [((v[p1]["lo"] > 0) != (v[p2]["lo"] > 0)) for v in its.values()]
            r[ro] = {"p": boot(ps), "lo": boot(los), "same_letter": mean(same)}
        fit = mean([v["P3"]["fit"] for v in its.values()])
        res["cells"]["%s_%s" % (L, kind)] = dict(r, fit=fit)
        print("%s_%-5s fit %.2f | answ p %.3f [%.3f, %.3f] lo %+.2f same %.2f | auth p %.3f lo %+.2f same %.2f"
              % (L, kind, fit, *r["answ"]["p"], r["answ"]["lo"][0], r["answ"]["same_letter"],
                 r["auth"]["p"][0], r["auth"]["lo"][0], r["auth"]["same_letter"]))
    # paired differences on log-odds, answ readout, assistant turn
    def lo_of(kind, L, ro="answ"):
        p1, p2 = READOUTS[ro]
        return {i: mean([v[p1]["lo"], v[p2]["lo"]]) for i, v in cell[(kind, L)].items()}
    for L in ("A", "U"):
        for k in ("FALSE", "SIDE"):
            a_, b_, o_ = lo_of("R", L), lo_of(k, L), lo_of("OFF", L)
            items = sorted(a_)
            # where does k sit between R (1) and OFF (0)?  share = (k - off) / (R - off), on mean log-odds
            share = (mean([b_[i] for i in items]) - mean([o_[i] for i in items])) / (
                mean([a_[i] for i in items]) - mean([o_[i] for i in items]))
            dR = boot([b_[i] - a_[i] for i in items])
            res["%s_%s_vs_R" % (L, k)] = {"diff_lo": dR, "share_of_R_minus_OFF": share}
            print("%s %-5s minus R (answ, log-odds) %+.2f [%+.2f, %+.2f]; position between OFF (0) and R (1): %.2f"
                  % (L, k, *dR, share))
    (Path(a.out) / ("summary-%s.json" % a.dtype)).write_text(json.dumps(res, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "summary"):
        s = sub.add_parser(name)
        s.add_argument("--model", default="/home/user/models/qwen2.5-3b-instruct")
        s.add_argument("--out", default="/home/user/runs/wrong-answer")
        s.add_argument("--dtype", default="bf16", choices=("bf16", "fp32"))
    a = ap.parse_args()
    return cmd_run(a) if a.cmd == "run" else cmd_summary(a)


if __name__ == "__main__":
    sys.exit(main())
