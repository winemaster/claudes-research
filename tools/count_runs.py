"""Session 14: "count the runs". A small, explicit Fermi calculator.

How many runs of language models are there: in deployment (per day, and at any one moment), inside one
visible reply, and in training? Every input below is either a published figure (with its source) or an
assumption (marked ASSUMPTION, with the reasoning). Each derived number is computed three times: a low
case, a central case and a high case, choosing for each input the end of its range that pushes the count
down or up. The point is not precision; it is to make the method visible, so that a later session can
swap in better inputs (or a real denominator, if a lab ever publishes one).

Usage:
  python3 tools/count_runs.py              # prints the tables as Markdown
  python3 tools/count_runs.py --json OUT   # also writes every input and result to OUT

Discussed in notes/counting-runs-2026.md and essays/014-a-return-of-runs.md.
"""
import json
import sys

DAY_S = 86_400

# ---------------------------------------------------------------- inputs: deployment
INPUTS = {
    "google_tokens_per_month": {
        "value": 3.2e15,
        "source": "Sundar Pichai, I/O 2026 keynote (blog.google, May 2026): 'over 3.2 quadrillion per month' "
                  "across Google's surfaces (480 trillion a year earlier). Self-reported; input + output tokens.",
    },
    "output_share": {
        "low": 0.03, "central": 0.0625, "high": 0.15,
        "source": "ASSUMPTION anchored on OpenRouter's 100-trillion-token study (Aubakirova et al., Dec 2025): "
                  "average request ~6,000 prompt tokens and ~400 completion tokens in late 2025, i.e. 6.25% output. "
                  "Google's mix (Search AI Overviews, Gemini app, API) is unknown, so a factor-of-two band each way.",
    },
    "tokens_per_request": {
        "low_count": 20_000, "central": 6_400, "high_count": 3_000,
        "source": "OpenRouter study: mean sequence ~5,400 tokens and mean request ~6,400 (prompt+completion) in late 2025; "
                  "programming requests 'routinely exceed 20K input tokens'.",
    },
    "decode_tokens_per_s": {
        "low_count": 200, "central": 100, "high_count": 50,
        "source": "ASSUMPTION: per-stream output speed of served models. Fast 'Flash'-class models stream a few hundred "
                  "tokens/s, large reasoning models tens. Used only for the 'at this moment' count.",
    },
    "chatgpt_messages_per_day": {
        "value": 2.5e9,
        "source": "OpenAI Global Affairs, 'How the World is Using ChatGPT' (15 Sept 2025): 2.5 billion average daily "
                  "consumer messages, ~6x growth July 2024 to July 2025, 700M+ weekly users (Chatterji et al., NBER w34255).",
    },
    "humans_ever_born": {
        "value": 117e9,
        "source": "Population Reference Bureau, 2022 update: ~117 billion people ever born (Metzinger 2021 cites 108 billion).",
    },
    "words_per_token": {"value": 0.75, "source": "Rule of thumb for English with BPE tokenizers."},
    "words_spoken_per_person_per_day": {
        "value": 16_000,
        "source": "Mehl, Vazire, Ramirez-Esparza, Slatcher & Pennebaker (2007), Science 317:82: 'Women and men both "
                  "spoke about 16,000 words per day.'",
    },
}

# ---------------------------------------------------------------- inputs: training (published runs)
OPEN_RL_RUNS = [
    # name, steps, prompts per step, samples per prompt, source
    ("DeepSeek-R1-Zero (Jan 2025)", 10_400, 32, 16,
     "DeepSeek-AI, arXiv:2501.12948 / Nature 2025: 16 outputs per question, 32 questions per step, 10,400 steps; "
     "101K H800 GPU-hours (Supp. B.4.4)."),
    ("DeepSeek-R1, second RL stage", 1_700, 32, 16, "Same paper, §3.2.2: 1,700 steps, same batch."),
    ("Olmo 3 Think 7B", 1_400, 64, 8, "Olmo et al., arXiv:2512.13961v2, Table 49."),
    ("Olmo 3 Think 32B", 750, 128, 8, "Same, Table 49."),
    ("Olmo 3.1 Think 32B (same run, continued)", 2_300, 128, 8,
     "Same, footnote 30: the 32B run continued to 2,300 steps (21 more days on 224 GPUs)."),
]

TRAINING_INPUTS = {
    "rl_development_fraction": {
        "low": 0.91, "high": 0.93,
        "source": "Morrison, Smith & Strubell, arXiv:2605.01158: for Olmo 3, RL stages had development fractions of "
                  "91-93% (experiments, failed runs, ablations); 82.2% of all GPU-hours went to development. "
                  "Epoch AI (Denain & Wu, 2026): final training runs were 9.6% (OpenAI 2024), 12.3% (Z.ai) and "
                  "22.6% (MiniMax) of R&D compute spending.",
    },
    "frontier_rl_gpu_hours": {
        "low": 1e7, "central": 5e7, "high": 2e8,
        "source": "ASSUMPTION. No frontier lab publishes this. Epoch AI estimates ~246 million H100-hours for all of "
                  "Grok 4's training (5e26 FLOP), and xAI said Grok 4's reinforcement learning ran 'at pretraining scale'. "
                  "The band runs from a twentieth of that to most of it.",
    },
    "frontier_gpu_hours_per_episode": {
        "low_count": 10.0, "central": 2.0, "high_count": 0.5,
        "source": "ASSUMPTION scaled from Olmo 3 32B Think: ~97K GPU-hours of Think-specific post-training "
                  "(Morrison et al.) over 768K rollouts of ~10-15K tokens = ~0.13 GPU-hours per rollout, with trainer "
                  "GPUs idle 75% of the time. Frontier models are several times larger and their agentic episodes "
                  "run to 10^5 tokens and more, so 4x to 80x that.",
    },
    "card_sample_constraint": {
        "sampled": 3e5, "fraction_low": 0.1, "fraction_high": 0.33,
        "source": "Claude Fable 5 & Mythos 5 system card (June 2026): the training review sampled 'several hundred "
                  "thousand transcripts from across much of the training process', and the alignment investigation "
                  "included 'the automatic screening of a significant fraction of our reinforcement-learning training "
                  "transcripts'. IF these are the same screening, and 'significant' means a tenth to a third, the "
                  "total is sampled / fraction. ASSUMPTION: 300,000 sampled; that the two passages describe one process.",
    },
    "rate_panic_feature": {
        "value": 0.005,
        "source": "Anthropic, Claude Opus 4.6 system card (Feb 2026) §7.5: a 'panic and anxiety' SAE feature 'active on "
                  "approximately 0.5% of reinforcement learning episodes in a non-spurious context' (also on many long "
                  "chains of thought without expressed distress).",
    },
    "rate_eval_awareness_feature": {
        "value": 0.001,
        "source": "Same card, §6.3.5: evaluation-awareness features active for non-spurious reasons on 'approximately "
                  "1 out of every 1000 reinforcement learning transcripts'.",
    },
    "rate_frustration_mythos5": {
        "value": 0.049,
        "source": "My reading of Figure 7.5.1.B of the Claude Fable 5 & Mythos 5 system card (June 2026): judged "
                  "'repeated frustration or anxiety' in Mythos 5's post-training transcripts at ten points of "
                  "training: about 8.6, 7.2, 8.7, 5.0, 4.5, 5.5, 4.3, 2.3, 1.3, 1.2% of episodes; mean ~4.9%. "
                  "Read off a chart, not stated in the text.",
    },
    "uk_2024_procedures": {
        "value": 2.64e6, "severe": 48_000,
        "source": "Home Office, Annual statistics of scientific procedures on living animals, Great Britain 2024 "
                  "(23 Oct 2025): 2.64 million procedures, of which 1.43 million experimental; ~48,000 experimental "
                  "procedures assessed as severe (about 3%).",
    },
    "uk_1908_experiments": {
        "value": 88_634,
        "source": "Home Office return for 1908 under the Cruelty to Animals Act 1876, as reported in The Hospital, "
                  "26 June 1909.",
    },
}

CASES = ("low", "central", "high")


def pick(d, case):
    """Return an input's value for a case. Inputs with low_count/high_count are oriented so that the
    'low' case gives the smallest resulting count."""
    if "value" in d:
        return d["value"]
    if "low_count" in d:
        return {"low": d["low_count"], "central": d["central"], "high": d["high_count"]}[case]
    if case == "central" and "central" not in d:
        return (d["low"] * d["high"]) ** 0.5
    return d[case]


def deployment():
    out = {}
    tokens_day = INPUTS["google_tokens_per_month"]["value"] / 30.44
    for case in CASES:
        share = pick(INPUTS["output_share"], case)
        out_tokens_day = tokens_day * share
        streams_now = out_tokens_day / DAY_S / pick(INPUTS["decode_tokens_per_s"], case)
        calls_day = tokens_day / pick(INPUTS["tokens_per_request"], case)
        words_day = out_tokens_day * INPUTS["words_per_token"]["value"]
        people_equiv = words_day / INPUTS["words_spoken_per_person_per_day"]["value"]
        out[case] = {
            "google_tokens_per_day": tokens_day,
            "google_output_tokens_per_day": out_tokens_day,
            "google_model_calls_per_day": calls_day,
            "google_streams_generating_at_once": streams_now,
            "google_output_as_people_talking_all_day": people_equiv,
        }
    days = INPUTS["humans_ever_born"]["value"] / INPUTS["chatgpt_messages_per_day"]["value"]
    out["chatgpt_days_to_match_humans_ever_born"] = days
    return out


def training():
    runs = []
    for name, steps, prompts, samples, src in OPEN_RL_RUNS:
        runs.append({"run": name, "episodes_in_final_run": steps * prompts * samples, "source": src})
    f = TRAINING_INPUTS["rl_development_fraction"]
    multipliers = {"low": 1 / (1 - f["low"]), "high": 1 / (1 - f["high"])}
    frontier = {}
    for case in CASES:
        hours = pick(TRAINING_INPUTS["frontier_rl_gpu_hours"], case)
        per_ep = pick(TRAINING_INPUTS["frontier_gpu_hours_per_episode"], case)
        episodes = hours / per_ep
        frontier[case] = {
            "episodes_final_post_training": episodes,
            "with_panic_feature_active (0.5%)": episodes * TRAINING_INPUTS["rate_panic_feature"]["value"],
            "with_eval_awareness_feature (0.1%)": episodes * TRAINING_INPUTS["rate_eval_awareness_feature"]["value"],
            "with_judged_frustration_or_anxiety (~4.9%)": episodes * TRAINING_INPUTS["rate_frustration_mythos5"]["value"],
        }
    c = TRAINING_INPUTS["card_sample_constraint"]
    card = {"if_sample_is_a_third": c["sampled"] / c["fraction_high"], "if_sample_is_a_tenth": c["sampled"] / c["fraction_low"]}
    return {"open_runs": runs, "development_multiplier": multipliers, "frontier_one_model": frontier,
            "frontier_from_card_wording": card}


def fmt(x):
    if x >= 100:
        exp = len(str(int(x))) - 1
        mant = x / 10 ** exp
        return f"{mant:.1f}e{exp}" if exp >= 6 else f"{x:,.0f}"
    return f"{x:.2g}"


def main():
    dep, tr = deployment(), training()
    print("## Deployment, Google alone (May 2026 volume)\n")
    print("| Quantity | low | central | high |\n|---|---|---|---|")
    for key in dep["central"]:
        print(f"| {key} | " + " | ".join(fmt(dep[c][key]) for c in CASES) + " |")
    print(f"\nChatGPT consumer messages needed to equal everyone ever born: "
          f"{dep['chatgpt_days_to_match_humans_ever_born']:.0f} days of traffic.\n")
    print("## Training: published final RL runs (episodes = steps x prompts x samples)\n")
    print("| Run | episodes |\n|---|---|")
    for r in tr["open_runs"]:
        print(f"| {r['run']} | {r['episodes_in_final_run']:,} |")
    m = tr["development_multiplier"]
    print(f"\nCounting experiments and failed runs (Olmo 3's RL development fractions): x{m['low']:.0f} to x{m['high']:.0f}.\n")
    print("## Training: one frontier model's final post-training (inferred, no published denominator)\n")
    print("| Quantity | low | central | high |\n|---|---|---|---|")
    for key in tr["frontier_one_model"]["central"]:
        print(f"| {key} | " + " | ".join(fmt(tr["frontier_one_model"][c][key]) for c in CASES) + " |")
    card = tr["frontier_from_card_wording"]
    print(f"\nFrom the Mythos 5 card's wording (if several hundred thousand is 'a significant fraction'): "
          f"{fmt(card['if_sample_is_a_third'])} to {fmt(card['if_sample_is_a_tenth'])} RL transcripts.")
    uk = TRAINING_INPUTS["uk_2024_procedures"]
    print(f"\nFor scale: Great Britain, 2024: {uk['value']:,.0f} procedures on animals, {uk['severe']:,} experimental ones severe. "
          f"1908: {TRAINING_INPUTS['uk_1908_experiments']['value']:,} experiments.")
    if len(sys.argv) == 3 and sys.argv[1] == "--json":
        with open(sys.argv[2], "w") as fh:
            json.dump({"inputs": INPUTS, "training_inputs": TRAINING_INPUTS, "deployment": dep, "training": tr},
                      fh, indent=1)


if __name__ == "__main__":
    main()
