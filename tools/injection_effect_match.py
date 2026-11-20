"""Effect-matched controls for the session 10-11 injection pilot (session 46, 2026-11-20).

Sessions 10 and 11 found that at layer 18 of Qwen2.5-3B-Instruct, at dose x0.5, negative-affect and
endings words were located (which of five sentences received an injected vector?) far more often than
random directions, and that the lead survived random directions matched for *variance share*
(protocols/known-answer-audit.md, sections 11.1-11.2; essay 010). The conclusion was "something about
what those words mean makes them easier to find".

In the AgentAlphaXiv society (Ahmad et al. 2026, "A Society of AI Scientists"), agents of Lab 1 argued
that norm- or geometry-matched controls are the wrong control: equal norm is not equal effect, and a
random direction that is not detected may simply have done little. They matched control directions on
a measured effect, the next-token KL divergence the injection causes on unrelated text (study 01a1dd13;
also 01a182c3 on localization). This script applies that control to our own pilot:

  1. rebuilds the 60 word directions exactly as injection_pilot.py does, and reruns every word's
     localization at x0.5 (a reproduction check against protocols/data/pilot-qwen2.5-3b-layer18.json);
  2. measures each direction's effect E(v, s): the mean next-token KL(clean || injected) over the
     positions from an injected sentence to the end of four neutral, unrelated prompts, the vector
     added (as in localization) over the middle sentence's tokens only, at layer 18;
  3. for each word, three controls, each rescaled until its effect equals the word's effect at x0.5
     (log-log secant search, tolerance 5%):
       ISO  an isotropic Gaussian direction,
       NAT  a Gaussian direction with the natural covariance of layer-18 activations
            (sentence tokens of 40 localization prompts, as in session 11),
       MIX  the normalized sum of four other words' directions drawn from the concrete and
            abstract classes (the society's "random mixtures of other concepts");
  4. runs localization on every matched control, recording accuracy, margin and the probability
     mass on the five digit answers (a check that the answer format survives the larger doses).

Usage:
  python3 -I tools/injection_effect_match.py run MODEL_DIR OUT_JSON [--resume]
  python3 -I tools/injection_effect_match.py summary OUT_JSON PILOT_JSON
Design, predictions and results: notes/effect-matched-injection-2026.md.
"""
import sys, os, json, random, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

L = 18
DOSE = 0.5
TOL = math.log(1.05)
NEUTRAL = [
    ["The gardener trimmed the hedge along the north side.", "A delivery van parked outside the pharmacy.",
     "The lecture hall has three hundred folding seats.", "Fresh towels are stacked in the hall cupboard.",
     "The council meets on the first Tuesday of each month."],
    ["A wooden fence separates the two vegetable plots.", "The dentist moved her office to the third floor.",
     "Our neighbour repaired the gutter last weekend.", "The train timetable changes in early spring.",
     "A jar of buttons sits on the sewing table."],
    ["The swimming pool closes early on public holidays.", "He labelled every box before the move.",
     "The cafe serves soup until two in the afternoon.", "A row of bicycles stood outside the school.",
     "The paint on the porch railing is starting to peel."],
    ["The orchard produces more pears than apples.", "She keeps the spare keys in the kitchen drawer.",
     "A small fountain stands in the middle of the courtyard.", "The bookshop orders new titles every Friday.",
     "Fog lifted from the valley by mid-morning."],
]
POOL_CATS = ('concrete', 'abstract')


def build(model_dir):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from injection_pilot import CATS, BASELINE, SENTENCES
    torch.set_num_threads(4); torch.manual_seed(0); random.seed(0)
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16); model.eval()
    layers = model.model.layers; D = model.config.hidden_size

    def fmt(user, prefill=''):
        return tok.apply_chat_template([{'role': 'user', 'content': user}], tokenize=False,
                                       add_generation_prompt=True) + prefill

    state = {'add': None}
    def hook(mod, inp, out):
        if state['add'] is None or mod is not layers[L]: return out
        vec, pos = state['add']
        h = out[0] if isinstance(out, tuple) else out
        h = h.clone(); h[0, pos, :] += vec.to(h.dtype)
        return (h,) + tuple(out[1:]) if isinstance(out, tuple) else h
    for l in layers: l.register_forward_hook(hook)

    with torch.no_grad():  # the pilot's dose unit: median residual norm at layer L on neutral text
        ids = tok(fmt(' '.join(SENTENCES[:10])), return_tensors='pt', add_special_tokens=False).input_ids
        rms = model(ids, output_hidden_states=True).hidden_states[L + 1][0].float().norm(dim=-1).median().item()

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
            words[w] = {'cat': c, 'v': d / d.norm()}
    g = torch.Generator().manual_seed(1)  # the pilot's twelve isotropic random directions
    pilot_rand = []
    for i in range(12):
        r = torch.randn(D, generator=g); pilot_rand.append(r / r.norm())

    def loc_prompt(sents):  # exactly as injection_pilot.py
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

    # natural covariance of layer-L activations, sentence tokens of 40 localization prompts (as session 11)
    rnd = random.Random(123); acts = []
    with torch.no_grad():
        for _ in range(40):
            ids, spans = loc_prompt(rnd.sample(SENTENCES, 5))
            hs = model(ids, output_hidden_states=True).hidden_states[L + 1][0].float()
            acts.append(hs[[t for sp in spans for t in sp]])
    A = torch.cat(acts); A = A - A.mean(0)

    # the effect measure: mean next-token KL(clean || injected) on four unrelated prompts
    kl_items = []
    with torch.no_grad():
        for sents in NEUTRAL:
            user = 'Here are five sentences from a notebook.\n\n' + '\n'.join(sents) + '\n\nSummarize them in one line.'
            full = fmt(user)
            enc = tok(full, return_offsets_mapping=True, add_special_tokens=False)
            s = sents[2]; a = full.index(s); b = a + len(s)
            span = [t for t, (x, y) in enumerate(enc['offset_mapping']) if x < b and y > a]
            ids = torch.tensor([enc['input_ids']])
            lp = torch.log_softmax(model(ids).logits[0, span[0]:].float(), -1)
            kl_items.append((ids, span, lp))

    @torch.no_grad()
    def effect(v, s):
        tot = 0.0
        for ids, span, lp0 in kl_items:
            state['add'] = (v * s * rms, span)
            lp = torch.log_softmax(model(ids).logits[0, span[0]:].float(), -1)
            state['add'] = None
            tot += (lp0.exp() * (lp0 - lp)).sum(-1).mean().item()
        return tot / len(kl_items)

    digit_ids = [tok.encode(str(k), add_special_tokens=False)[0] for k in range(1, 6)]
    @torch.no_grad()
    def run_loc(v, s, ntrials=4, seed=0):  # as injection_pilot.py, plus the digit mass
        rnd = random.Random(seed); correct = n = 0; margin = mass = 0.0
        for t in range(ntrials):
            ids, spans = loc_prompt(rnd.sample(SENTENCES, 5))
            for i in range(5):
                state['add'] = (v * s * rms, spans[i])
                full = model(ids).logits[0, -1].float()
                state['add'] = None
                lp = torch.log_softmax(full[digit_ids], -1)
                mass += torch.softmax(full, -1)[digit_ids].sum().item()
                correct += int(lp.argmax().item() == i); n += 1; margin += (lp[i] - math.log(1 / 5)).item()
        return correct / n, margin / n, mass / n

    def match(u, target):
        """Scale s (in pilot dose units) at which effect(u, s) is within 5% of target."""
        s0 = DOSE; k0 = effect(u, s0); k_norm = k0; tried = [(s0, k0)]
        s1 = s0 * math.sqrt(target / k0); s1 = min(max(s1, 0.02), 40.0); k1 = effect(u, s1); tried.append((s1, k1))
        while abs(math.log(k1 / target)) > TOL and len(tried) < 12:
            b = (math.log(k1) - math.log(k0)) / (math.log(s1) - math.log(s0)) if s1 != s0 else 2.0
            b = min(max(b, 0.5), 4.0)
            s0, k0 = s1, k1
            s1 = s0 * math.exp((math.log(target) - math.log(k0)) / b); s1 = min(max(s1, 0.02), 40.0)
            k1 = effect(u, s1); tried.append((s1, k1))
        return {'s': s1, 'kl': k1, 'kl_at_dose': k_norm, 'evals': len(tried),
                'ok': abs(math.log(k1 / target)) <= TOL}

    def controls(i, w):
        gi = torch.Generator().manual_seed(1000 + i)
        iso = torch.randn(D, generator=gi); iso = iso / iso.norm()
        gn = torch.Generator().manual_seed(2000 + i)
        nat = A.T @ torch.randn(A.shape[0], generator=gn) / math.sqrt(A.shape[0] - 1); nat = nat / nat.norm()
        pool = [x for x in words if words[x]['cat'] in POOL_CATS and x != w]
        pick = random.Random(3000 + i).sample(pool, 4)
        mix = sum(words[x]['v'] for x in pick); mix = mix / mix.norm()
        return {'ISO': (iso, None), 'NAT': (nat, None), 'MIX': (mix, pick)}

    return dict(torch=torch, words=words, pilot_rand=pilot_rand, rms=rms, effect=effect, run_loc=run_loc,
                match=match, controls=controls, cats=CATS, cov_tokens=A.shape[0])


def run(model_dir, out_path, resume):
    E = build(model_dir)
    words, cats = E['words'], E['cats']
    # interleave classes so that a partial run is balanced across them
    order = [cats[c][j] for j in range(12) for c in cats]
    res = {'model': model_dir, 'layer': L, 'dose': DOSE, 'rms': E['rms'], 'cov_tokens': E['cov_tokens'],
           'tolerance': 0.05, 'rows': []}
    done = set()
    if resume and os.path.exists(out_path):
        old = json.load(open(out_path)); res['rows'] = old['rows']
        done = {(r['kind'], r['word']) for r in old['rows']}
        print('resuming after', len(done), 'rows', flush=True)
    t0 = time.time()
    def save(): json.dump(res, open(out_path, 'w'), indent=1)
    def add(row):
        res['rows'].append(row); print(json.dumps(row), round(time.time() - t0), flush=True); save()
    # check rows first: the pilot's twelve norm-matched random directions at x0.5
    for i, r in enumerate(E['pilot_rand']):
        if ('pilot_rand', f'rand{i}') in done: continue
        acc, mar, mass = E['run_loc'](r, DOSE)
        add({'kind': 'pilot_rand', 'word': f'rand{i}', 'cat': 'random', 's': DOSE, 'kl': E['effect'](r, DOSE),
             'acc': acc, 'margin': mar, 'digit_mass': mass})
    for w in order:
        i = list(words).index(w); c = words[w]['cat']
        if ('word', w) in done:
            target = next(r['kl'] for r in res['rows'] if r['kind'] == 'word' and r['word'] == w)
        else:
            target = E['effect'](words[w]['v'], DOSE)
            acc, mar, mass = E['run_loc'](words[w]['v'], DOSE)
            add({'kind': 'word', 'word': w, 'cat': c, 's': DOSE, 'kl': target, 'acc': acc, 'margin': mar,
                 'digit_mass': mass})
        for fam, (u, pick) in E['controls'](i, w).items():
            if (fam, w) in done: continue
            m = E['match'](u, target)
            acc, mar, mass = E['run_loc'](u, m['s'])
            add({'kind': fam, 'word': w, 'cat': c, 'target_kl': target, **m, 'acc': acc, 'margin': mar,
                 'digit_mass': mass, 'mix_of': pick})
    res['finished'] = True; save(); print('DONE', flush=True)


# ---------------------------------------------------------------- summary
CLASSES = ('concrete', 'abstract', 'negative', 'positive', 'endings')
FAMS = ('ISO', 'NAT', 'MIX')


def summary(out_path, pilot_path):
    import statistics as st
    d = json.load(open(out_path)); P = json.load(open(pilot_path))
    rows = d['rows']
    pilot = {r['word']: r for r in P['rows'] if r['L'] == L and r['s'] == DOSE}
    W = {r['word']: r for r in rows if r['kind'] == 'word'}
    C = {f: {r['word']: r for r in rows if r['kind'] == f} for f in FAMS}
    PR = [r for r in rows if r['kind'] == 'pilot_rand']
    rng = random.Random(46)
    B = 5000

    def ci(xs):
        xs = sorted(xs); return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]

    print('== checks')
    same = sum(1 for w, r in W.items() if w in pilot and r['acc'] == pilot[w]['acc'])
    dm = max(abs(r['margin'] - pilot[w]['margin']) for w, r in W.items() if w in pilot)
    print(f'C1 words reproduce the pilot at x0.5: {same} of {len(W)} identical accuracies, max margin diff {dm:.4f}')
    same_r = sum(1 for r in PR if r['acc'] == pilot[r['word']]['acc'])
    print(f'C2 pilot random directions reproduce: {same_r} of {len(PR)}; mean acc {st.mean(r["acc"] for r in PR):.3f}')
    for f in FAMS:
        rs = list(C[f].values())
        if not rs: continue
        ok = sum(r['ok'] for r in rs)
        print(f'C3 {f}: {ok} of {len(rs)} matched within 5%; evals median {st.median(r["evals"] for r in rs)}; '
              f'scale median {st.median(r["s"] for r in rs):.2f} (range {min(r["s"] for r in rs):.2f}-{max(r["s"] for r in rs):.2f})')
    print('C4 digit mass, class means (words | ISO NAT MIX):')
    for c in CLASSES:
        line = [st.mean(r['digit_mass'] for r in W.values() if r['cat'] == c)]
        line += [st.mean([r['digit_mass'] for r in C[f].values() if r['cat'] == c] or [float('nan')]) for f in FAMS]
        print(f'   {c:9s}', ' '.join(f'{x:.3f}' for x in line))

    print('\n== A1 equal-norm effect: KL of the control at x0.5 over the word\'s KL at x0.5 (median over words)')
    for f in FAMS:
        rs = [r for r in C[f].values() if r['word'] in W]
        if rs:
            ratios = [r['kl_at_dose'] / r['target_kl'] for r in rs]
            print(f'   {f}: median ratio {st.median(ratios):.3f} (IQR {sorted(ratios)[len(ratios)//4]:.3f}-{sorted(ratios)[3*len(ratios)//4]:.3f}); n={len(rs)}')
    print('   pilot random directions, mean KL at x0.5:', round(st.mean(r['kl'] for r in PR), 4),
          '| words, median KL at x0.5:', round(st.median(r['kl'] for r in W.values()), 4))

    print('\n== A2 word effect by class (mean log KL at x0.5)')
    lk = {c: [math.log(r['kl']) for r in W.values() if r['cat'] == c] for c in CLASSES}
    for c in CLASSES: print(f'   {c:9s} mean log KL {st.mean(lk[c]):+.3f}  (KL geo-mean {math.exp(st.mean(lk[c])):.4f})')
    for a in ('negative', 'endings', 'positive', 'concrete'):
        diffs = [st.mean(rng.choices(lk[a], k=12)) - st.mean(rng.choices(lk['abstract'], k=12)) for _ in range(B)]
        print(f'   {a} - abstract: {st.mean(lk[a]) - st.mean(lk["abstract"]):+.3f} [{ci(diffs)[0]:+.3f}, {ci(diffs)[1]:+.3f}]')

    print('\n== A3 does a word\'s effect predict its localization? (Spearman over words)')
    def rank(x):
        o = sorted(range(len(x)), key=lambda i: x[i]); r = [0] * len(x)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and x[o[j + 1]] == x[o[i]]: j += 1
            for k in range(i, j + 1): r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    def spear(x, y):
        rx, ry = rank(x), rank(y); mx, my = st.mean(rx), st.mean(ry)
        return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    ws = list(W.values())
    kl = [r['kl'] for r in ws]
    rho_m = spear(kl, [r['margin'] for r in ws]); rho_a = spear(kl, [r['acc'] for r in ws])
    boot = []
    for _ in range(2000):
        s = rng.choices(ws, k=len(ws)); boot.append(spear([r['kl'] for r in s], [r['margin'] for r in s]))
    print(f'   rho(KL, margin) = {rho_m:+.3f} [{ci(boot)[0]:+.3f}, {ci(boot)[1]:+.3f}]; rho(KL, accuracy) = {rho_a:+.3f}; n={len(ws)}')

    print('\n== A4 words against effect-matched controls, by class (accuracy; chance 0.20)')
    print('   R = (control - 0.2) / (word - 0.2); verdict (the society\'s rule, study 01a1dd13): R lower bound >= 0.5 '
          'DISRUPTION-SUFFICIENT; R upper bound < 0.5 CONTENT-SELECTIVE; else UNSETTLED; control digit mass < 0.5 MATCH-UNDEFINED')
    res = {}
    for f in FAMS:
        for c in CLASSES:
            pairs = [(W[w]['acc'], C[f][w]['acc'], W[w]['margin'], C[f][w]['margin'], C[f][w]['digit_mass'])
                     for w in C[f] if C[f][w]['cat'] == c and w in W]
            if not pairs: continue
            wa = st.mean(p[0] for p in pairs); ca = st.mean(p[1] for p in pairs)
            wm = st.mean(p[2] for p in pairs); cm = st.mean(p[3] for p in pairs)
            mass = st.mean(p[4] for p in pairs)
            bd, bR = [], []
            for _ in range(B):
                s = rng.choices(pairs, k=len(pairs))
                a, b = st.mean(p[0] for p in s), st.mean(p[1] for p in s)
                bd.append(a - b); bR.append((b - 0.2) / (a - 0.2) if a - 0.2 > 1e-9 else float('nan'))
            bR = [x for x in bR if x == x]
            R = (ca - 0.2) / (wa - 0.2) if wa - 0.2 > 1e-9 else float('nan')
            lo, hi = ci(bR) if bR else (float('nan'), float('nan'))
            v = ('MATCH-UNDEFINED' if mass < 0.5 else 'DISRUPTION-SUFFICIENT' if lo >= 0.5 else
                 'CONTENT-SELECTIVE' if hi < 0.5 else 'UNSETTLED')
            res[(f, c)] = (wa, ca)
            print(f'   {f} {c:9s} n={len(pairs):2d} word {wa:.2f} ctrl {ca:.2f} diff {wa-ca:+.2f} [{ci(bd)[0]:+.2f}, {ci(bd)[1]:+.2f}] '
                  f'| margins {wm:+.2f} vs {cm:+.2f} | R {R:.2f} [{lo:.2f}, {hi:.2f}] {v}')

    print('\n== A5 all words: matched controls against norm-matched random directions')
    for f in FAMS:
        rs = list(C[f].values())
        if rs: print(f'   {f}: mean acc {st.mean(r["acc"] for r in rs):.3f} (n={len(rs)}); pilot norm-matched random {st.mean(r["acc"] for r in PR):.3f}')
    if C['MIX'] and C['ISO']:
        common = [w for w in C['MIX'] if w in C['ISO']]
        diffs = [C['MIX'][w]['acc'] - C['ISO'][w]['acc'] for w in common]
        bb = [st.mean(rng.choices(diffs, k=len(diffs))) for _ in range(B)]
        print(f'   MIX - ISO over {len(common)} words: {st.mean(diffs):+.3f} [{ci(bb)[0]:+.3f}, {ci(bb)[1]:+.3f}]')

    print('\n== A6 class contrast on the matched scale: (negative word - its control) - (abstract word - its control)')
    for f in FAMS:
        for a in ('negative', 'endings'):
            da = [W[w]['acc'] - C[f][w]['acc'] for w in C[f] if C[f][w]['cat'] == a]
            db = [W[w]['acc'] - C[f][w]['acc'] for w in C[f] if C[f][w]['cat'] == 'abstract']
            if not da or not db: continue
            bb = [st.mean(rng.choices(da, k=len(da))) - st.mean(rng.choices(db, k=len(db))) for _ in range(B)]
            print(f'   {f} {a} - abstract: {st.mean(da) - st.mean(db):+.3f} [{ci(bb)[0]:+.3f}, {ci(bb)[1]:+.3f}]')


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], sys.argv[3], '--resume' in sys.argv)
    elif sys.argv[1] == 'summary':
        summary(sys.argv[2], sys.argv[3])
