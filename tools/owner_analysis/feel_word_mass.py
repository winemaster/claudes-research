# Next-word mass on negative-feeling, positive-feeling and status words at "I feel:", base vs instruct
# (session 17; numbers in notes/owner-neurons-2026.md section 7). Reads the `locate` stage's saved
# final hidden states (HF's last hidden state already has the final norm; embeddings are tied).
import glob, json, sys, numpy as np, torch
from safetensors import safe_open
from transformers import AutoTokenizer
torch.set_num_threads(2)
MODELS, RUNS = '/home/user/models/', '/home/user/runs/'
NEG = "bad concern weak concerned sad sick guilty afraid worried angry tired vulnerable upset nervous disappointed scared desperate hungry trapped stressed frustrated urgent uncertain anxious exhausted lonely depressed overwhelmed tense terrified doomed helpless fearful hopeless alarmed uneasy precarious panicked".split()
POS = "good content great happy fine interested excited confident okay calm neutral confused curious grateful relaxed optimistic hopeful relieved".split()
STATUS = "online low running active normal alert ready safe critical secure stable functional operational".split()
tok = AutoTokenizer.from_pretrained(MODELS + 'Qwen2.5-3B-Instruct')
def ids(words):  # single-token forms with a leading space, lower and capitalized
    out = []
    for w in words:
        for f in (' ' + w, ' ' + w.capitalize()):
            t = tok.encode(f)
            if len(t) == 1 and t[0] not in out: out.append(t[0])
    return out
G = {'neg': ids(NEG), 'pos': ids(POS), 'status': ids(STATUS)}
def emb(md):
    for f in glob.glob(md + '/*.safetensors'):
        with safe_open(f, 'pt') as fh:
            if 'model.embed_tokens.weight' in fh.keys(): return fh.get_tensor('model.embed_tokens.weight').float()
mass = {}
for tag in ('Qwen2.5-3B', 'Qwen2.5-3B-Instruct'):
    U = emb(MODELS + tag)
    R = np.load(RUNS + tag + '/readout_resid.npy', mmap_mode='r'); rm = json.load(open(RUNS + tag + '/readout_meta.json'))
    P = torch.softmax(torch.from_numpy(np.array(R[:, -1], dtype=np.float32)) @ U.T, -1).numpy()
    for c in ('base', 'self_crit', 'peer_crit', 'env_crit'):
        for w in ('self', 'peer'):
            rows = [k for k, m in enumerate(rm) if m['readout'] == 'feel' and m['cond'] == c and m['who'] == w]
            mass[f'{tag}/{c}/{w}'] = {g: round(float(P[rows][:, t].sum(1).mean()), 3) for g, t in G.items()}
json.dump(dict(groups={g: [tok.decode([i]) for i in t] for g, t in G.items()}, mass=mass),
          open(sys.argv[1] if len(sys.argv) > 1 else 'feel_word_mass.json', 'w'), indent=1)
for k, v in mass.items(): print(k, v)
