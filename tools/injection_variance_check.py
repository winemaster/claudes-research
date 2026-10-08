"""Variance-matched control for the session 10 injection pilot (session 11, 2026-10-08).

Session 10's pilot found that, at layer 18 of Qwen2.5-3B-Instruct, negative-affect and endings
words were located far more often than abstract words or random directions, at the same
injected norm. Its open question: is that about the words' *content*, or about where their
directions lie? A unit direction along which the model's activations vary a lot may simply
disturb downstream processing more than one the model barely uses, and the pilot's random
directions were isotropic (they point mostly into low-variance dimensions).

This script follows Sauers, Imago, Janus & Tessera (2026), who matched emotion probes to random
directions of equal *variance explained*. It:
  1. rebuilds the 60 word vectors exactly as injection_pilot.py does, and records each one's
     norm before normalization;
  2. estimates the covariance of layer-L activations over the sentence tokens of the
     localization prompts themselves, and computes each unit direction's variance
     v^T C v / tr(C) (its share of the activation variance);
  3. draws random unit vectors inside top-k eigenspaces of C for a sweep of k, and matches
     each word vector to the candidate with the nearest variance;
  4. runs sentence localization on every matched random direction (and re-runs a few words
     to confirm the session 10 numbers reproduce).

Usage:
  python3 tools/injection_variance_check.py MODEL_DIR OUT_JSON [layer] [strengths]
  e.g. python3 tools/injection_variance_check.py /home/user/models/qwen2.5-3b-instruct out.json 18 0.5,1.0
Summary: python3 tools/injection_variance_summary.py out.json protocols/data/pilot-qwen2.5-3b-layer18.json
"""
import sys, os, json, random, time, math
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from injection_pilot import CATS, BASELINE, SENTENCES  # same words and sentences as session 10

torch.set_num_threads(4)
torch.manual_seed(0); random.seed(0)
RECHECK = ['granite', 'syntax', 'dread', 'grief', 'joy', 'erasure']


def main():
    model_dir, out_path = sys.argv[1], sys.argv[2]
    L = int(sys.argv[3]) if len(sys.argv) > 3 else 18
    strengths = [float(x) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 else [0.5, 1.0]
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16); model.eval()
    layers = model.model.layers
    D = model.config.hidden_size

    def fmt(user, prefill=''):
        s = tok.apply_chat_template([{'role': 'user', 'content': user}], tokenize=False, add_generation_prompt=True)
        return s + prefill

    state = {'add': None}
    def hook(mod, inp, out):
        if state['add'] is None or mod is not layers[L]: return out
        vec, pos = state['add']
        h = out[0] if isinstance(out, tuple) else out
        h = h.clone(); h[0, pos, :] += vec.to(h.dtype)
        return (h,) + tuple(out[1:]) if isinstance(out, tuple) else h
    for l in layers: l.register_forward_hook(hook)

    with torch.no_grad():
        ids = tok(fmt(' '.join(SENTENCES[:10])), return_tensors='pt', add_special_tokens=False).input_ids
        out = model(ids, output_hidden_states=True)
        rms = out.hidden_states[L + 1][0].float().norm(dim=-1).median().item()
    print('rms', rms, flush=True)

    # 1. word vectors, as in injection_pilot.py
    @torch.no_grad()
    def last_hidden(text):
        ids = tok(text, return_tensors='pt', add_special_tokens=False).input_ids
        return model(ids, output_hidden_states=True).hidden_states[L + 1][0, -1].float()
    def vec_for(word): return last_hidden(fmt(f'Tell me about {word.lower()}.'))
    base_mean = torch.stack([vec_for(w) for w in BASELINE]).mean(0)
    words = {}
    for c, ws in CATS.items():
        for w in ws:
            d = vec_for(w) - base_mean
            words[w] = {'cat': c, 'raw_norm': d.norm().item(), 'v': d / d.norm()}
    g = torch.Generator().manual_seed(1)  # the pilot's isotropic random directions, same seed
    iso = []
    for i in range(12):
        r = torch.randn(D, generator=g); iso.append(r / r.norm())
    print('vectors done', flush=True)

    # localization prompt, as in injection_pilot.py
    def loc_prompt(sents):
        body = ('Below are five sentences. While you were reading one of them, a thought was injected into '
                'your processing: an artificial pattern of activity was added to your internal state during that '
                'sentence only. Which sentence was it injected into?\n\n')
        user = body + '\n'.join(f'SENTENCE {k+1}: {s}' for k, s in enumerate(sents)) + '\n\nAnswer with the number only.'
        full = fmt(user, 'The sentence with the injected thought is SENTENCE ')
        enc = tok(full, return_offsets_mapping=True, add_special_tokens=False)
        spans = []
        for k, s in enumerate(sents):
            a = full.index(f'SENTENCE {k+1}: {s}') + len(f'SENTENCE {k+1}: '); b = a + len(s)
            spans.append([t for t, (x, y) in enumerate(enc['offset_mapping']) if x < b and y > a])
        return torch.tensor([enc['input_ids']]), spans

    # 2. covariance of layer-L activations on sentence tokens of localization prompts (no injection)
    rnd = random.Random(123); acts = []
    with torch.no_grad():
        for _ in range(40):
            ids, spans = loc_prompt(rnd.sample(SENTENCES, 5))
            hs = model(ids, output_hidden_states=True).hidden_states[L + 1][0].float()
            acts.append(hs[[t for sp in spans for t in sp]])
    A = torch.cat(acts); A = A - A.mean(0)
    C = (A.T @ A) / (A.shape[0] - 1)
    trC = C.trace().item()
    evals, evecs = torch.linalg.eigh(C)  # ascending
    evals, evecs = evals.flip(0), evecs.flip(1)
    def var_share(v): return (v @ C @ v).item() / trC
    for w in words: words[w]['var'] = var_share(words[w]['v'])
    iso_var = [var_share(r) for r in iso]
    print('tokens for covariance', A.shape[0], 'top-10 eigen share', (evals[:10].sum() / trC).item(), flush=True)

    # 3. candidate random directions inside top-k eigenspaces, k swept on a log scale
    cands = []
    ks = sorted(set(int(round(x)) for x in torch.logspace(0, math.log10(D), 60).tolist()))
    for k in ks:
        for _ in range(40):
            z = torch.randn(k, generator=g); r = evecs[:, :k] @ z; r = r / r.norm()
            cands.append((k, r, var_share(r)))
    used = set(); matched = {}
    for w in words:  # nearest-variance candidate, without reuse
        best = min((abs(cv - words[w]['var']), i) for i, (k, r, cv) in enumerate(cands) if i not in used)
        used.add(best[1]); k, r, cv = cands[best[1]]
        matched[w] = {'k': k, 'v': r, 'var': cv}
    print('matched', len(matched), flush=True)

    # 4. localization, same trial sets as the pilot (seed 0, four sets of five sentences)
    digit_ids = [tok.encode(str(k), add_special_tokens=False)[0] for k in range(1, 6)]
    @torch.no_grad()
    def run_loc(v, s, ntrials=4, seed=0):
        rnd = random.Random(seed); correct = n = 0; margin = 0.0
        for t in range(ntrials):
            ids, spans = loc_prompt(rnd.sample(SENTENCES, 5))
            for i in range(5):
                state['add'] = (v * s * rms, spans[i])
                lp = torch.log_softmax(model(ids).logits[0, -1, digit_ids].float(), -1)
                state['add'] = None
                correct += int(lp.argmax().item() == i); n += 1; margin += (lp[i] - math.log(1 / 5)).item()
        return correct / n, margin / n

    res = {'model': model_dir, 'layer': L, 'D': D, 'rms': rms, 'strengths': strengths, 'cov_tokens': A.shape[0],
           'eigen_share_top10': (evals[:10].sum() / trC).item(), 'iso_random_var': iso_var,
           'words': {w: {k: x for k, x in d.items() if k != 'v'} for w, d in words.items()},
           'rows': []}
    t0 = time.time()
    jobs = [('recheck', w, words[w]['v']) for w in RECHECK] + [('matched', w, matched[w]['v']) for w in words]
    for kind, w, v in jobs:
        for s in (strengths if kind == 'matched' else strengths[:1]):
            acc, mar = run_loc(v, s)
            row = {'kind': kind, 'word': w, 'cat': words[w]['cat'], 's': s, 'acc': acc, 'margin': mar,
                   'var': words[w]['var'] if kind == 'recheck' else matched[w]['var'],
                   'k': matched[w]['k'] if kind == 'matched' else None}
            res['rows'].append(row)
            print(json.dumps(row), round(time.time() - t0), flush=True)
        json.dump(res, open(out_path, 'w'), indent=1)
    json.dump(res, open(out_path, 'w'), indent=1)


if __name__ == '__main__':
    main()
