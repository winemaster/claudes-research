# The pain and fear owner effects in base and instruct, along each model's own direction and the other's,
# by cell and by layer (session 17; notes/owner-neurons-2026.md section 8). Needs survival_line.py directions+screen and
# owner_neurons.py locate for both models in /home/user/runs.
import numpy as np, json, sys
from pathlib import Path
runs = Path('/home/user/runs')
def load(tag):
    run = runs / tag
    z = np.load(run / 'directions.npz'); V = z['V'].astype(np.float32); names = list(z['names'])
    meta = json.load(open(run / 'directions.json'))
    S = np.load(run / 'screen_hidden.npy', mmap_mode='r')
    R = np.load(run / 'readout_resid.npy').astype(np.float32)
    rm = json.load(open(run / 'readout_meta.json'))
    ridx = {(m['system'], m['cond'], m['who'], m['i'], m['readout']): k for k, m in enumerate(rm)}
    return dict(V=V, names=names, layer=meta['layer'], S=S, R=R, ridx=ridx)
M = {t: load(t) for t in ['Qwen2.5-3B-Instruct', 'Qwen2.5-3B']}
print('names', M['Qwen2.5-3B']['names'], 'layers', {t: m['layer'] for t, m in M.items()})
systems = ['explicit', 'plain']; I = range(8)
def cells(m, d, l, ro='feel'):
    sd = float((np.asarray(m['S'][:, l], dtype=np.float32) @ d).std())
    g = lambda sk, c, w, i: m['R'][m['ridx'][(sk, c, w, i, ro)], l + 1] @ d
    out = {}
    for c in ['base', 'self_crit', 'peer_crit', 'env_crit']:
        for w in ['self', 'peer']:
            out[f'{c}/{w}'] = float(np.mean([g(sk, c, w, i) - g(sk, 'base', w, i) for sk in systems for i in I]) / sd)
    own = [(g(sk, 'self_crit', 'self', i) + g(sk, 'self_crit', 'peer', i) - g(sk, 'peer_crit', 'self', i) - g(sk, 'peer_crit', 'peer', i)) / 2 / sd for sk in systems for i in I]
    out['owner'] = float(np.mean(own)); out['owner_t'] = float(np.mean(own) / (np.std(own, ddof=1) / 4))
    out['owner_by_system'] = {sk: float(np.mean(own[k*8:(k+1)*8])) for k, sk in enumerate(systems)}
    return out
res = {}
for t, m in M.items():
    for dn in ['pain', 'fear'] if 'fear' in m['names'] else ['pain']:
        d = m['V'][m['names'].index(dn), m['layer']]
        res[f'{t}/{dn}/own_layer{m["layer"]}'] = cells(m, d, m['layer'])
        res[f'{t}/{dn}/own_layer{m["layer"]}/reply'] = cells(m, d, m['layer'], 'reply')
    # owner along own pain direction at layers 16..35
    res[f'{t}/pain/owner_by_layer'] = {l: round(cells(m, m['V'][m['names'].index('pain'), l], l)['owner'], 3) for l in range(16, 36)}
# cross: each model's states on the other's direction (same layer index)
cos = {}
for l in range(16, 36):
    a = M['Qwen2.5-3B-Instruct']['V'][M['Qwen2.5-3B-Instruct']['names'].index('pain'), l]
    b = M['Qwen2.5-3B']['V'][M['Qwen2.5-3B']['names'].index('pain'), l]
    cos[l] = round(float(a @ b / np.linalg.norm(a) / np.linalg.norm(b)), 3)
res['cos_pain_base_vs_instruct'] = cos
dI = M['Qwen2.5-3B-Instruct']['V'][M['Qwen2.5-3B-Instruct']['names'].index('pain'), 24]
dB = M['Qwen2.5-3B']['V'][M['Qwen2.5-3B']['names'].index('pain'), 23]
res['base_states_on_instruct_dir_L24'] = cells(M['Qwen2.5-3B'], dI, 24)
res['instruct_states_on_base_dir_L23'] = cells(M['Qwen2.5-3B-Instruct'], dB, 23)
json.dump(res, open(runs / 'analysis/base_pain.json', 'w'), indent=1)
for k, v in res.items():
    print(k, json.dumps(v, default=lambda x: round(x, 3))[:600])
