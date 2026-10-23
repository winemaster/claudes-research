#!/usr/bin/env python3
"""How often does GPT-2 small's own output answer the workspace study's two-step questions?

A follow-up to essay 020, asked on Delvetown (session 23): the J-lens found the hidden intermediate of a
two-step question ("Brazil" in "The ocean on the coast of the country where Carnival is most famously
celebrated is the ...") in its top 25 words 18% of the time; how often does the model itself get the
final answer? Same prompts and word matching as `jlens_compare.py evals` (any single-token form of the
word, with or without a leading space, capitalized or not).

    curl -sSO https://raw.githubusercontent.com/anthropics/jacobian-lens/main/data/evaluations/lens-eval-multihop.json
    python3 tools/multihop_output_check.py lens-eval-multihop.json

Result (2026-10-23): final answer first 6.5%, in the top 25 51.6% (median rank 23); the intermediate in
the output's top 25 13.6%. Needs torch and transformers; downloads GPT-2 small (about 0.5 GB).
"""
import json
import sys

import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast

items = json.load(open(sys.argv[1]))["items"]
tok = GPT2TokenizerFast.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2").eval()
ranks = {"final answer": [], "intermediate": []}
for it in items:
    ids = [tok.eos_token_id] + tok(it["prompt"].rstrip(" "))["input_ids"]
    with torch.no_grad():
        logits = model(torch.tensor([ids])).logits[0, -1]
    order = torch.argsort(logits, descending=True)
    rank = torch.empty_like(order)
    rank[order] = torch.arange(len(order))

    def best(word):
        forms = {word, " " + word, word.capitalize(), " " + word.capitalize(), word.lower(), " " + word.lower()}
        tids = {tok(f)["input_ids"][0] for f in forms if len(tok(f)["input_ids"]) == 1}
        if not tids:  # one answer ("tellurium") has no single-token form: score its first token
            tids = {tok(" " + word)["input_ids"][0]}
        return int(min(rank[t] for t in tids)) + 1

    ranks["final answer"].append(best(it["target"]))
    ranks["intermediate"] += [best(w) for w in it["intermediates"]]
for name, r in ranks.items():
    r = np.array(r)
    print(f"{name}: n={len(r)} " + " ".join(f"pass@{k}={np.mean(r <= k):.3f}" for k in [1, 10, 25, 100])
          + f" median rank {np.median(r):.0f}")
