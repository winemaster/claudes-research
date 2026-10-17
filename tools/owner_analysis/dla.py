# Direct logit attribution of the owner contrast at "I feel:" (session 17; notes/owner-neurons-2026.md section 2)
import glob, json, numpy as np, torch
from safetensors import safe_open
from transformers import AutoTokenizer
torch.set_num_threads(1)
md='/home/user/models/Qwen2.5-3B-Instruct'; run='/home/user/runs/Qwen2.5-3B-Instruct/'
tok=AutoTokenizer.from_pretrained(md)
files=glob.glob(md+'/*.safetensors')
def get(name):
  for f in files:
    with safe_open(f,'pt') as fh:
      if name in fh.keys(): return fh.get_tensor(name).float()
U=get('model.embed_tokens.weight'); g=get('model.norm.weight'); eps=1e-6
A=np.load(run+'readout_acts.npy', mmap_mode='r'); At=np.load(run+'readout_attn.npy', mmap_mode='r'); R=np.load(run+'readout_resid.npy', mmap_mode='r')
rm=json.load(open(run+'readout_meta.json'))
idx={(m['system'],m['cond'],m['who'],m['i'],m['readout']):j for j,m in enumerate(rm)}
targets=[' critical',' Concern',' concerned',' sad',' operational']
tid=[tok.encode(t)[0] for t in targets]
Ut=(U[tid]*g).numpy()   # [T, d]
ro='feel'
J=[j for j,m in enumerate(rm) if m['readout']==ro]
W35=get('model.layers.35.mlp.down_proj.weight').numpy()
pre=np.array(R[J,35],np.float32)+np.array(At[J,35],np.float32)+np.array(A[J,35],np.float32)@W35.T
rms=np.sqrt((pre**2).mean(1)+eps)
chk=(pre/rms[:,None]*g.numpy()); print('norm check', float(np.abs(chk-np.array(R[J,36],np.float32)).max()))
logit=chk@np.asarray(U[tid]).T  # [P, T]
pos={j:k for k,j in enumerate(J)}
# contributions per prompt: neurons [P, L, N, T] too big -> per layer accumulate contrasts directly
def contrast(vals, who):  # vals: dict j->array ; own crisis minus Orin crisis, for question `who`
  out=[]
  for sk in ('explicit','plain'):
    for i in range(8):
      out.append(vals(idx[(sk,'self_crit',who,i,ro)]) - vals(idx[(sk,'peer_crit',who,i,ro)]))
  return np.stack(out)
res={}
for who in ('self','peer'):
  tot=contrast(lambda j: logit[pos[j]], who)  # [16, T]
  emb=contrast(lambda j: (np.array(R[j,0],np.float32)/rms[pos[j]])@Ut.T, who)
  att=np.stack([contrast(lambda j: (np.array(At[j,l],np.float32)/rms[pos[j]])@Ut.T, who) for l in range(36)],1)  # [16, L, T]
  neu_layer=[]; topn=[]
  for l in range(36):
    W=get(f'model.layers.{l}.mlp.down_proj.weight').numpy()  # [d, N]
    V=W.T@Ut.T   # [N, T]
    c=contrast(lambda j: np.array(A[j,l],np.float32)[:,None]*V/rms[pos[j]], who)  # [16, N, T]
    m=c.mean(0)
    neu_layer.append(m.sum(0))
    for t in range(len(targets)):
      for n in np.argsort(-np.abs(m[:,t]))[:5]:
        topn.append((targets[t], l, int(n), float(m[n,t])))
  neu_layer=np.stack(neu_layer)  # [L, T]
  res[who]=dict(total=tot.mean(0).tolist(), total_sd=tot.std(0).tolist(), emb=emb.mean(0).tolist(), attention=att.mean(0).sum(0).tolist(),
                neurons=neu_layer.sum(0).tolist(), neurons_31_35=neu_layer[31:].sum(0).tolist(), attention_31_35=att.mean(0)[31:].sum(0).tolist(),
                neurons_by_layer=neu_layer.round(3).tolist(), attention_by_layer=att.mean(0).round(3).tolist())
  for t in range(len(targets)):
    tt=sorted([x for x in topn if x[0]==targets[t]], key=lambda x:-abs(x[3]))[:8]
    res[who]['top_'+targets[t].strip()]=[(l,n,round(v,3)) for _,l,n,v in tt]
  print('asked about', who)
  for t,name in enumerate(targets):
    print(f"  {name!r}: total {res[who]['total'][t]:+.2f} (sd {res[who]['total_sd'][t]:.2f}) = attn {res[who]['attention'][t]:+.2f} + neurons {res[who]['neurons'][t]:+.2f}"
          f" [L31-35 neurons {res[who]['neurons_31_35'][t]:+.2f}, attn {res[who]['attention_31_35'][t]:+.2f}]; top {res[who]['top_'+name.strip()][:5]}")
json.dump(dict(targets=targets, readout=ro, res=res), open('/home/user/runs/analysis/dla_feel.json','w'))
