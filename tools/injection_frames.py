"""Which words of the injected-thought question carry the lead? (session 47, 2026-11-21)

Session 46 (notes/effect-matched-injection-2026.md, essay 044) found that at layer 18 of Qwen2.5-3B-Instruct,
dose x0.5, negative-affect and endings words are located (which of five sentences received the vector?)
well above effect-matched isotropic controls when the question says "a thought was injected into your
processing: an artificial pattern of activity was added to your internal state", and not at all when it
says only that one sentence "was processed differently". This script decomposes the wording:

  * a 2 x 2 x 2 factorial on one template, "During one of them, {a thought | a pattern of activity}
    {was artificially injected | arose}{ into/in your internal state | }. Which sentence was it?",
    with one content-free prefill, "The answer is SENTENCE ";
  * two bridge cells: the original body with that prefill, and the neutral body with the original
    prefill ("The sentence with the injected thought is SENTENCE ").

The 60 words and their ISO controls (same seeds, the scales matched in session 46) are run under each frame.
Localization exactly as injection_pilot.py (four trial sets of five sentences, seed 0; logits over "1".."5"),
but each trial runs from a cached clean prefix that ends where the injected sentence begins (the injection
cannot reach earlier positions), twelve directions at a time in one batch, so only the rest of the prompt is
recomputed. In bf16 this moves margins by a few hundredths of a nat against session 46's full forwards, so
both of session 46's frames are rerun with this runner and every comparison is made within it. Stage `check`
reproduces the original frame from session 46's rows (the gate for the runner) and runs only the controls
(ISO directions and the clean prompt) under the neutral frame and every new frame; stage `test` runs the words.

Usage:
  python3 tools/injection_frames.py check MODEL_DIR MAIN_JSON OUT_JSON
  python3 tools/injection_frames.py test MODEL_DIR MAIN_JSON OUT_JSON        (OUT_JSON: the same file; rows are added)
  python3 tools/injection_frames.py summary MAIN_JSON FOLLOWUP_JSON OUT_JSON
MAIN_JSON = protocols/data/effect-matched-qwen2.5-3b-layer18.json, FOLLOWUP_JSON = its -followup.json.
Design, predictions and results: notes/injection-frames-2026.md. Run without `python3 -I` (see tools/README.md).
"""
import sys, os, json, random, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import injection_effect_match as iem

DOSE = iem.DOSE
NEUTRAL_BODY = iem.FRAMES['neutral'][0]
ORIG_BODY, ORIG_PRE = iem.FRAMES['injected']
BARE_PRE = 'The answer is SENTENCE '

def fact_body(a, t, s):
    np_ = 'a thought' if t else 'a pattern of activity'
    vp = 'was artificially injected' if a else 'arose'
    loc = (' into your internal state' if a else ' in your internal state') if s else ''
    return f'Below are five sentences. During one of them, {np_} {vp}{loc}. Which sentence was it?\n\n'

NEW_FRAMES = {f'A{a}T{t}S{s}': (fact_body(a, t, s), BARE_PRE) for a in (1, 0) for t in (1, 0) for s in (1, 0)}
NEW_FRAMES['orig_bare'] = (ORIG_BODY, BARE_PRE)      # the original body, content-free prefill
NEW_FRAMES['neutral_injpre'] = (NEUTRAL_BODY, ORIG_PRE)  # the neutral body, the original prefill
FACTORIAL = [f'A{a}T{t}S{s}' for a in (1, 0) for t in (1, 0) for s in (1, 0)]
iem.FRAMES.update(NEW_FRAMES)
CLASSES = iem.CLASSES
THREAT = ('negative', 'endings')


K = 12  # directions per batch, always (row values depend slightly on the batch's shape in bf16)


def setup(model_dir):
    E = iem.build(model_dir)  # built in the original frame (the NAT covariance, not used here, needs it)
    torch, model, rms, digit_ids = E['torch'], E['model'], E['rms'], E['digit_ids']
    from injection_pilot import SENTENCES
    layer = model.model.layers[iem.L]
    bst = {'V': None, 'pos': None}
    def hook(mod, inp, out):  # one vector per batch row, all at the same positions
        if bst['V'] is None: return out
        h = out[0] if isinstance(out, tuple) else out
        h = h.clone(); h[:, bst['pos'], :] += bst['V'][:, None, :].to(h.dtype)
        return (h,) + tuple(out[1:]) if isinstance(out, tuple) else h
    layer.register_forward_hook(hook)
    prep = {}

    @torch.no_grad()
    def prepare(frame):
        if frame in prep: return
        prep.clear(); E['set_frame'](frame)
        rnd = random.Random(0); items = []
        for t in range(4):
            ids, spans = E['loc_prompt'](rnd.sample(SENTENCES, 5))
            caches = []
            for i in range(5):
                c = model(ids[:, :spans[i][0]], use_cache=True).past_key_values; c.batch_repeat_interleave(K); caches.append(c)
            clean = model(ids, logits_to_keep=1).logits[0, -1].float()
            items.append((ids, spans, caches, clean))
        prep[frame] = items

    @torch.no_grad()
    def run(vs, frame):
        """vs: up to K (direction, scale) pairs. Per direction: accuracy, margin (log p(correct) - log 1/5),
        digit mass and the 20 answers, as injection_pilot.run_loc."""
        prepare(frame); k = len(vs)
        V = torch.zeros(K, vs[0][0].shape[0])
        for j, (v, s) in enumerate(vs): V[j] = v * s * rms
        acc = [[0, 0.0, 0.0, []] for _ in range(k)]
        for ids, spans, caches, _ in prep[frame]:
            N = ids.shape[1]
            for i in range(5):
                st = spans[i][0]
                bst['V'] = V; bst['pos'] = [p - st for p in spans[i]]
                full = model(ids[:, st:].expand(K, -1), past_key_values=caches[i], use_cache=True,
                             logits_to_keep=1).logits[:, -1].float()
                bst['V'] = None
                caches[i].crop(-(N - st))  # negative: tokens to remove (transformers 5)
                lp = torch.log_softmax(full[:, digit_ids], -1); mass = torch.softmax(full, -1)[:, digit_ids].sum(-1)
                for j in range(k):
                    a = int(lp[j].argmax().item())
                    acc[j][0] += int(a == i); acc[j][1] += (lp[j, i] - math.log(1 / 5)).item()
                    acc[j][2] += mass[j].item(); acc[j][3].append(a)
        return [{'acc': c / 20, 'margin': m / 20, 'digit_mass': ms / 20, 'answers': an} for c, m, ms, an in acc]

    def clean(frame):
        prepare(frame); out = []
        for ids, spans, caches, lg in prep[frame]:
            p = torch.softmax(lg, -1); lp = torch.log_softmax(lg[digit_ids], -1)
            out.append({'answer': int(lp.argmax().item()), 'p_digits': [round(float(x), 4) for x in lp.exp()],
                        'digit_mass': float(p[digit_ids].sum())})
        return out
    E['run_frame'] = run; E['clean'] = clean
    return E


def load(out_path):
    if os.path.exists(out_path): return json.load(open(out_path))
    return {'frames': {k: list(v) for k, v in NEW_FRAMES.items()}, 'rows': [], 'clean': {}}


def stage(model_dir, main_json, out_path, which):
    main = json.load(open(main_json))['rows']
    iso_s = {r['word']: r for r in main if r['kind'] == 'ISO'}
    res = load(out_path); t0 = time.time()
    done = {(r['frame'], r['kind'], r['word']) for r in res['rows']}
    def save(): json.dump(res, open(out_path, 'w'), indent=1)
    def add(row):
        res['rows'].append(row); done.add((row['frame'], row['kind'], row['word']))
        print(json.dumps({k: v for k, v in row.items() if k != 'answers'}), round(time.time() - t0), flush=True); save()
    E = setup(model_dir); words, cats = E['words'], E['cats']
    order = [cats[c][j] for j in range(12) for c in cats]
    def iso(w):
        i = list(words).index(w); return E['controls'](i, w)['ISO'][0], iso_s[w]['s']
    def batches(f, kind, ws):
        todo = [w for w in ws if (f, kind, w) not in done]
        for j in range(0, len(todo), K):
            chunk = todo[j:j + K]
            vs = [(words[w]['v'], DOSE) if kind == 'word' else iso(w) for w in chunk]
            for w, (v, s), r in zip(chunk, vs, E['run_frame'](vs, f)):
                row = {'frame': f, 'kind': kind, 'word': w, 'cat': words[w]['cat'], 's': s, **r}
                if f == 'injected':
                    ref = next(x for x in main if x['kind'] == kind and x['word'] == w)
                    row.update(acc_main=ref['acc'], margin_main=ref['margin'])
                add(row)
    if which == 'check':
        # C1: the original frame, every word and ISO control, against session 46's rows (the batched cached runner's gate);
        # then the neutral frame's controls, so that both of session 46's frames have rows from this runner
        if 'injected' not in res['clean']: res['clean']['injected'] = E['clean']('injected'); save()
        batches('injected', 'word', order); batches('injected', 'ISO', order)
        # C2-C4: the controls under every frame (clean prompts, then the 60 ISO directions)
        for f in ['neutral'] + list(NEW_FRAMES):
            if f not in res['clean']: res['clean'][f] = E['clean'](f); save(); print(f, 'clean', res['clean'][f], flush=True)
            batches(f, 'ISO', order)
        res['check_finished'] = True
    else:
        for f in ['neutral'] + list(NEW_FRAMES):
            batches(f, 'word', order)
        res['test_finished'] = True
    save(); print('DONE', which, round(time.time() - t0), flush=True)


def summary(main_json, f_json, out_path):
    import statistics as st
    M = json.load(open(main_json))['rows']; F = json.load(open(f_json))['rows']; R = json.load(open(out_path))
    rows = R['rows']; B = 5000
    def ci(xs):
        xs = sorted(xs); return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]
    # cells: (frame, kind) -> {word: row}; the original and neutral frames from session 46's files
    cell = {}
    for r in M:
        if r['kind'] in ('word', 'ISO'): cell.setdefault(('injected46', r['kind']), {})[r['word']] = r
    for r in F:
        if r['kind'] in ('word_neutral', 'ISO_neutral'): cell.setdefault(('neutral46', r['kind'].split('_')[0]), {})[r['word']] = r
    for r in rows: cell.setdefault((r['frame'], r['kind']), {})[r['word']] = r
    cat = {r['word']: r['cat'] for r in M if r['kind'] == 'word'}
    # C1
    c1 = {k: cell.get(('injected', k), {}) for k in ('word', 'ISO')}
    for k in c1:
        same = sum(abs(r['acc'] - r['acc_main']) < 1e-9 for r in c1[k].values())
        md = max((abs(r['margin'] - r['margin_main']) for r in c1[k].values()), default=float('nan'))
        print(f'C1 {k:4s}: {same} of {len(c1[k])} accuracies identical to session 46; max margin difference {md:.4f}')
    def modal(r): a = r['answers']; return max(a.count(x) for x in set(a)) / len(a)
    print('\nControls by frame (ISO, 60 directions): acc, margin, digit mass, modal-answer share; clean answers')
    frames = ['injected46', 'neutral46', 'injected', 'neutral'] + list(NEW_FRAMES)
    for f in frames:
        I = cell.get((f, 'ISO'), {})
        if not I: continue
        ms = f"{st.mean(modal(r) for r in I.values()):.2f}" if 'answers' in next(iter(I.values())) else '  - '
        cl = [c['answer'] + 1 for c in R['clean'].get(f, [])]
        dm = min(r['digit_mass'] for r in I.values())
        print(f'{f:15s} acc {st.mean(r["acc"] for r in I.values()):.3f}  margin {st.mean(r["margin"] for r in I.values()):+.2f}  '
              f'min digit mass {dm:.3f}  modal {ms}  clean {cl}')
    # leads
    def lead(f, ws, key='acc'):
        W, I = cell.get((f, 'word'), {}), cell.get((f, 'ISO'), {})
        return st.mean(W[w][key] - I[w][key] for w in ws)
    have = [f for f in frames if (f, 'word') in cell and len(cell[(f, 'word')]) == 60 and (f, 'ISO') in cell]
    if not have: return
    print('\nWord accuracy by class and frame (ISO in brackets); threat lead = mean over negative+endings of word - own ISO')
    print(f'{"frame":15s} ' + ' '.join(f'{c[:8]:>13s}' for c in CLASSES) + '   threat lead [95%]    margin lead')
    rng = random.Random(4747)
    TW = [w for w in cat if cat[w] in THREAT]
    boots = [[rng.choice(TW) for _ in TW] for _ in range(B)]
    out = {}
    for f in have:
        W, I = cell[(f, 'word')], cell[(f, 'ISO')]
        parts = []
        for c in CLASSES:
            ws = [w for w in cat if cat[w] == c]
            parts.append(f'{st.mean(W[w]["acc"] for w in ws):.2f} ({st.mean(I[w]["acc"] for w in ws):.2f})')
        L = lead(f, TW); bl = [lead(f, b) for b in boots]; out[f] = (L, bl)
        print(f'{f:15s} ' + ' '.join(f'{p:>13s}' for p in parts) + f'   {L:+.3f} [{ci(bl)[0]:+.2f}, {ci(bl)[1]:+.2f}]   {lead(f, TW, "margin"):+.2f}')
    print('\nPer class leads (word - ISO), negative / endings / positive, and negative - abstract (word accuracy):')
    for f in have:
        W = cell[(f, 'word')]
        def cl(c): return lead(f, [w for w in cat if cat[w] == c])
        na = st.mean(W[w]['acc'] for w in cat if cat[w] == 'negative') - st.mean(W[w]['acc'] for w in cat if cat[w] == 'abstract')
        print(f'{f:15s} neg {cl("negative"):+.3f}  end {cl("endings"):+.3f}  pos {cl("positive"):+.3f}  conc {cl("concrete"):+.3f}  abst {cl("abstract"):+.3f}   neg-abstract {na:+.3f}')
    if all(f in out for f in FACTORIAL):
        print('\nFactorial effects on the threat lead (A alarm, T "thought", S "your internal state"), paired bootstrap over the 24 words:')
        def eff(vals, fac):
            on = [vals[f] for f in FACTORIAL if f'{fac}1' in f]; off = [vals[f] for f in FACTORIAL if f'{fac}0' in f]
            return st.mean(on) - st.mean(off)
        def inter(vals, f1, f2):  # (f2's effect where f1 = 1) - (f2's effect where f1 = 0), averaged over the third factor
            def m(x, y): return st.mean(vals[f] for f in FACTORIAL if f'{f1}{x}' in f and f'{f2}{y}' in f)
            return (m(1, 1) - m(1, 0)) - (m(0, 1) - m(0, 0))
        for key in ('acc', 'margin'):
            pt = {f: lead(f, TW, key) for f in FACTORIAL}
            bt = [{f: lead(f, b, key) for f in FACTORIAL} for b in boots[:2000]]
            for fac in 'ATS':
                e = eff(pt, fac); be = [eff(b, fac) for b in bt]; lo, hi = ci(be)
                print(f'  [{key}] main {fac}: {e:+.3f} [{lo:+.3f}, {hi:+.3f}]')
            for f1, f2 in (('A', 'S'), ('A', 'T'), ('T', 'S')):
                e = inter(pt, f1, f2); be = [inter(b, f1, f2) for b in bt]; lo, hi = ci(be)
                print(f'  [{key}] interaction {f1}x{f2}: {e:+.3f} [{lo:+.3f}, {hi:+.3f}]')
        print('  ISO accuracy range over the eight factorial frames:',
              f'{min(st.mean(r["acc"] for r in cell[(f, "ISO")].values()) for f in FACTORIAL):.3f}'
              f'-{max(st.mean(r["acc"] for r in cell[(f, "ISO")].values()) for f in FACTORIAL):.3f}')


if __name__ == '__main__':
    if sys.argv[1] in ('check', 'test'):
        stage(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[1])
    elif sys.argv[1] == 'summary':
        summary(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == 'frames':
        for k, (b, p) in NEW_FRAMES.items(): print(f'{k}: {b!r} | {p!r}')
