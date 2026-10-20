"""Session 19: recompute Experiment 3 of Cirrincione's *Mathematical Theory of the Transformer*, vol. I
(section 2.7.3): the asymmetry index alpha_h = ||M_a||_F / ||M||_F of M = W_Q^h (W_K^h)^T for all 144 heads
of bert-base-uncased, with a random rank-64 baseline, and list BERT's position tensors
(the book attributes early-layer positional structure to a sinusoidal encoding; BERT's is learned).

Reads the weights with numpy only (no torch):
    curl -L https://huggingface.co/google-bert/bert-base-uncased/resolve/main/model.safetensors -o model.safetensors
    python3 tools/bert_asymmetry_check.py model.safetensors notes/data/bert-asymmetry-session19.json
"""
import sys, json, numpy as np
from safetensors.numpy import load_file
w = load_file(sys.argv[1])
keys = [k for k in w if 'position' in k]
print('position-related tensors:', keys)
H, dh = 12, 64
res = {}
for l in range(12):
    p = f'bert.encoder.layer.{l}.attention.self.'
    if p+'query.weight' not in w:
        p = f'encoder.layer.{l}.attention.self.'
    Wq = w[p+'query.weight'].astype(np.float64)   # (out=768, in=768): q = Wq x
    Wk = w[p+'key.weight'].astype(np.float64)
    al = []
    for h in range(H):
        Q = Wq[h*dh:(h+1)*dh]          # 64 x 768
        K = Wk[h*dh:(h+1)*dh]
        M = Q.T @ K                     # score x_i^T M x_j
        Ma = (M - M.T) / 2
        al.append(np.linalg.norm(Ma) / np.linalg.norm(M))
    res[l] = al
alls = np.array([a for l in res for a in res[l]])
print('per-layer median alpha:', [round(float(np.median(res[l])), 3) for l in range(12)])
print('per-layer min/max:', [(round(min(res[l]),2), round(max(res[l]),2)) for l in range(12)])
med = [np.median(res[l]) for l in range(12)]
print('range of medians: %.3f; overall median %.3f; min %.3f max %.3f' % (max(med)-min(med), np.median(alls), alls.min(), alls.max()))
r = np.corrcoef(np.arange(12), med)[0,1]
print('linear fit r (layer vs median): %.2f' % r)
rng = np.random.default_rng(0)
rb = []
for _ in range(500):
    A = rng.standard_normal((64, 768)); B = rng.standard_normal((64, 768))
    M = A.T @ B; rb.append(np.linalg.norm((M-M.T)/2)/np.linalg.norm(M))
print('random rank-64 baseline alpha: mean %.3f sd %.4f' % (np.mean(rb), np.std(rb)))
json.dump({'per_layer': {str(l): [float(x) for x in res[l]] for l in res}, 'random_mean': float(np.mean(rb))}, open(sys.argv[2], 'w'), indent=1)
