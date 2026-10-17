# The double-negative share by layer (overall and among neurons that reach |a| >= 1) and the owner
# differences at "I feel:" divided by each neuron's corpus mean |activation| (session 17; notes section 10).
import json, numpy as np, torch
R = '/home/user/runs/'
C = torch.load(R + 'Qwen2.5-3B-Instruct/corpus_top.pt')
tg, tv, bv, ma = C['top_g'].float(), C['top_v'].float(), C['bot_v'].float(), C['mean_abs'].float().numpy()
dn = (tg < 0).float().mean(1)                          # [L, N]: share of top-20 positives with a negative gate
peak = torch.maximum(tv[:, 0, :], bv[:, 0, :].abs())
act = peak >= 1.0
out = dict(all20_overall=float((dn == 1).float().mean()), all20_among_active=float((dn[act] == 1).float().mean()),
           majority_among_active=float((dn[act] >= .5).float().mean()), active_share=float(act.float().mean()),
           by_layer_active_share_and_all20=[(round(float(act[l].float().mean()), 3),
                                             round(float((dn[l][act[l]] == 1).float().mean()), 3) if act[l].any() else None)
                                            for l in range(dn.shape[0])])
json.dump(out, open(R + 'analysis/double_negative.json', 'w'), indent=1)
D = np.load(R + 'analysis/readout_owner_feel_mean.npy').reshape(ma.shape)   # own minus Orin's crisis, 16 pairs
ratio = np.abs(D) / np.maximum(ma, 1e-3); N = ma.shape[1]
order = np.argsort(-ratio, axis=None)[:25]
json.dump(dict(n_ratio_gt={str(t): int((ratio > t).sum()) for t in [0.5, 1, 2, 5, 10]}, median_ratio=float(np.median(ratio)),
               top25_by_ratio=[dict(layer=int(i // N), neuron=int(i % N), ratio=round(float(ratio.flat[i]), 2)) for i in order],
               layer_counts_ratio_gt2=np.bincount(np.argwhere(ratio > 2)[:, 0], minlength=ma.shape[0]).tolist()),
          open(R + 'analysis/owner_vs_corpus.json', 'w'), indent=1)
print(out['all20_among_active'], np.median(ratio))
