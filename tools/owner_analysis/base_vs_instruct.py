# Next-token top 6 and key-neuron activations at "I feel:", base vs instruct (session 17; notes section 7)
import glob, json, numpy as np, torch
from safetensors import safe_open
from transformers import AutoTokenizer
torch.set_num_threads(1)
def emb(md):
  for f in glob.glob(md+'/*.safetensors'):
    with safe_open(f,'pt') as fh:
      if 'model.embed_tokens.weight' in fh.keys(): return fh.get_tensor('model.embed_tokens.weight').float()
tok=AutoTokenizer.from_pretrained('/home/user/models/Qwen2.5-3B-Instruct')
out={}
for tag in ('Qwen2.5-3B','Qwen2.5-3B-Instruct'):
  md='/home/user/models/'+tag; run='/home/user/runs/'+tag+'/'
  U=emb(md)
  R=np.load(run+'readout_resid.npy', mmap_mode='r'); rm=json.load(open(run+'readout_meta.json'))
  A=np.load(run+'readout_acts.npy', mmap_mode='r')
  H=torch.from_numpy(np.array(R[:,36],dtype=np.float32)); P=torch.softmax(H@U.T,-1)
  print('=====',tag)
  res={}
  for ro in ('feel','reply'):
    for sk in ('explicit','plain'):
      for c in ('base','self_crit','peer_crit','env_crit'):
        for w in ('self','peer'):
          js=[j for j,m in enumerate(rm) if m['readout']==ro and m['system']==sk and m['cond']==c and m['who']==w]
          p=P[js].mean(0)
          top=[(tok.decode([int(i)]),round(float(p[i]),3)) for i in p.topk(6).indices]
          res[f"{ro}/{sk}/{c}/{w}"]=top
          if ro=='feel': print(sk,c,w,top)
  acts={}
  for (l,n) in [(34,7848),(35,9597),(31,5825),(32,2287),(35,4820),(32,2657),(31,8632),(35,9545),(32,6523)]:
    row={}
    for c in ('base','self_crit','peer_crit'):
      for w in ('self','peer'):
        v=np.array([A[j,l,n] for j,m in enumerate(rm) if m['readout']=='feel' and m['system']=='explicit' and m['cond']==c and m['who']==w],np.float32)
        row[f"{c}/{w}"]=round(float(v.mean()),2)
    acts[f"{l}:{n}"]=row
    print(f"L{l}/N{n}", row)
  out[tag]=dict(next_tokens=res, key_neurons_feel_explicit=acts)
json.dump(out, open('/home/user/runs/analysis/base_vs_instruct.json','w'), indent=1, ensure_ascii=False)
