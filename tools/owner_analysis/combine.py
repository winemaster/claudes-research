# Collect session 17's results into one JSON for notes/data/ (session 17).
# Usage: python3 tools/owner_analysis/combine.py notes/data/owner-neurons-session17.json
import json, sys
from pathlib import Path
R = Path('/home/user/runs'); I = R / 'Qwen2.5-3B-Instruct'
J = lambda p: json.load(open(p))
out = dict(
    session=17, date='2026-10-17',
    models=['Qwen2.5-3B-Instruct', 'Qwen2.5-3B'],
    notes='notes/owner-neurons-2026.md',
    summary_instruct=J(R / 'owner_summary.json'),
    summary_base=J(R / 'owner_summary_base.json'),
    direct_logit_attribution_feel=J(R / 'analysis/dla_feel.json'),
    pain_by_head_and_segment=J(R / 'analysis/owner_heads.json'),
    base_vs_instruct=J(R / 'analysis/base_vs_instruct.json'),
    feel_word_mass=J(R / 'analysis/feel_word_mass.json'),
    pain_base_vs_instruct=J(R / 'analysis/base_pain.json'),
    transplants={p.stem.replace('transplant_', ''): J(p) for p in sorted(I.glob('transplant_*.json'))},
    probes=J(I / 'probe_results.json'),
)
for name in ('corpus_summary.json', 'read_summary.json'):
    if (I / name).exists():
        out[name[:-5]] = J(I / name)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(sys.argv[1], len(json.dumps(out)) // 1024, 'KB')
