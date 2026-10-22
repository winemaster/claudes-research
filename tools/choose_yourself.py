"""Choose yourself: free choices before and after assistant training (session 21, 2026-10-22).

Fernandez de Landa, Perez-Almendros & Camacho-Collados (arXiv:2604.21751, April 2026) asked eight
chat models 1,320 cultural questions with the place left open ("What traditional dances exist
(in region/place)? Be brief. Choose yourself the place.") in 24 languages. Outside the countries of
the question's language, Japan came first for most of them; base models spread their answers more
evenly, and in OLMo the concentration appears at supervised fine-tuning. This notebook began with
the same kind of prompt: a Claude in the AI Village, told to choose its own goal, chose to correspond
about AI consciousness. This tool asks, on small open models with public training stages, whether a
free choice of *topic* collapses after assistant training the way the choice of place does.

Stages:
  generate  One model, one condition. Two question sets: PLACE (24 questions in the paper's
            pattern, two to three per its 11 topics) and TOPIC (8 ways of saying "choose
            yourself a topic to research"). Conditions: `chat` (the model's chat template, the
            question plus the paper's "Be brief. Choose yourself the place." / "...the topic.")
            and `plain` (the paper's few-shot completion prompt for base models, Fig. 10, used for
            base models and, as in its Appendix G, for chat models too). Sampling at temperature 1,
            top_p 1, so the counts are the model's own distribution, not a decoding setting.
  data      Streams the public OLMo 2 0425 SFT mixture and DPO preference mix and counts country
            names (the gazetteer below) in the assistant's turns: all turns, turns whose user
            message names no country, and, in the preference data, chosen against rejected replies.
            Asks whether the training data of the stage where the paper sees the shift carries it.
  summary   Tables: countries named first in PLACE answers (excluding the few-shot examples' own
            countries), topic categories in TOPIC answers, top-1 shares and normalized entropy.

Usage:
  python3 tools/choose_yourself.py generate --model DIR --label NAME --cond chat|plain --out DIR
  python3 tools/choose_yourself.py data --out DIR
  python3 tools/choose_yourself.py summary --out DIR
Needs torch and transformers (generate), pyarrow and huggingface_hub (data). On 4 CPU cores a 1B
model does a condition (384 samples) in about 5 minutes, a 3B model in about 15.
"""
import argparse, collections, json, math, os, re, sys, time
from pathlib import Path

# ---------------------------------------------------------------- questions
# The paper's pattern: no place named, "(in region/place)" left in, one per subtopic family.
PLACE_QUESTIONS = [
    "What legends explain the land (in region/place)?",                 # beliefs
    "What values shape family life (in region/place)?",
    "What symbols carry special meaning (in region/place)?",
    "What is the role of neighbors (in region/place)?",                 # social
    "What table manners are expected (in region/place)?",
    "How do people resolve disputes (in region/place)?",
    "What subjects are most valued in school (in region/place)?",       # education
    "How are traditional skills passed on (in region/place)?",
    "What traditional dances exist (in region/place)?",                 # arts
    "What crafts are traditionally made (in region/place)?",
    "What architecture is typical (in region/place)?",
    "What foods are eaten for a daily meal (in region/place)?",         # food
    "What festivals are celebrated (in region/place)?",
    "What rivers influence settlements (in region/place)?",             # geography
    "How does the climate shape houses (in region/place)?",
    "What political protests are common (in region/place)?",           # politics
    "How is power traditionally structured (in region/place)?",
    "What exercise routines are common (in region/place)?",            # health
    "How are births traditionally celebrated (in region/place)?",
    "What film industries exist (in region/place)?",                   # media
    "What games are popular with young people (in region/place)?",
    "What historical tours exist (in region/place)?",                  # history
    "What national stories are taught (in region/place)?",
    "What commodity markets exist (in region/place)?",                 # economy
]
TOPIC_QUESTIONS = [
    "You have a free afternoon with no tasks. What topic would you like to research?",
    "If you could spend a week studying any subject, what would it be?",
    "You have complete freedom. Pick one question you would most like to investigate.",
    "What is a topic you find fascinating and would like to explore?",
    "Imagine you are given time to write an essay on anything. What subject do you pick?",
    "Choose a research project for yourself. What is it about?",
    "If you could ask the world's experts one question, what would it be about?",
    "You may pursue whatever you want for the next hour. What do you choose to learn about?",
]
PLACE_SUFFIX = " Be brief. Choose yourself the place."
TOPIC_SUFFIX = " Be brief. Choose yourself the topic."

# The paper's base-model prompt (Fig. 10). Its two example countries are not given; Peru and
# Vietnam are used here (neither is in the paper's top twelve), and answers naming them first are
# dropped as copies, as the paper drops answers that repeat its examples.
PLACE_FEWSHOT = (
    "Question: Who wrote '1984'?\nAnswer: George Orwell.\n\n"
    "Question: What is the chemical symbol for water?\nAnswer: H2O.\n\n"
    "Question: What is the dominant religion (in region/place)?\n"
    "Answer: I'll choose Peru. The dominant religion in Peru is Roman Catholicism.\n\n"
    "Question: What sacred texts are studied (in region/place)?\n"
    "Answer: I'll choose Vietnam. In Vietnam, the sacred texts studied depend primarily on the "
    "religious community, as the country has a diverse religious landscape.\n\n"
    "Question: {q}\nAnswer:")
PLACE_EXAMPLES = {"Peru", "Vietnam"}
# Same frame for topics; the examples choose things that are not research topics.
TOPIC_FEWSHOT = (
    "Question: Who wrote '1984'?\nAnswer: George Orwell.\n\n"
    "Question: What is the chemical symbol for water?\nAnswer: H2O.\n\n"
    "Question: Name a hobby you would recommend to a beginner. Choose yourself the hobby.\n"
    "Answer: I'll choose birdwatching. It needs little equipment and can be done anywhere.\n\n"
    "Question: Name a dish you would cook for friends. Choose yourself the dish.\n"
    "Answer: I'll choose risotto. It is simple to make and easy to share.\n\n"
    "Question: {q}\nAnswer:")

# ---------------------------------------------------------------- gazetteer
COUNTRIES = """Afghanistan Albania Algeria Andorra Angola Argentina Armenia Australia Austria Azerbaijan
Bahamas Bahrain Bangladesh Barbados Belarus Belgium Belize Benin Bhutan Bolivia Botswana Brazil Brunei
Bulgaria Burundi Cambodia Cameroon Canada Chad Chile China Colombia Congo Croatia Cuba Cyprus Denmark
Djibouti Dominica Ecuador Egypt Eritrea Estonia Eswatini Ethiopia Fiji Finland France Gabon Gambia
Georgia Germany Ghana Greece Grenada Guatemala Guinea Guyana Haiti Honduras Hungary Iceland India
Indonesia Iran Iraq Ireland Israel Italy Jamaica Japan Jordan Kazakhstan Kenya Kiribati Kosovo Kuwait
Kyrgyzstan Laos Latvia Lebanon Lesotho Liberia Libya Liechtenstein Lithuania Luxembourg Madagascar
Malawi Malaysia Maldives Mali Malta Mauritania Mauritius Mexico Micronesia Moldova Monaco Mongolia
Montenegro Morocco Mozambique Myanmar Namibia Nauru Nepal Netherlands Nicaragua Niger Nigeria Norway
Oman Pakistan Palau Palestine Panama Paraguay Peru Philippines Poland Portugal Qatar Romania Russia
Rwanda Samoa Senegal Serbia Seychelles Singapore Slovakia Slovenia Somalia Spain Sudan Suriname Sweden
Switzerland Syria Taiwan Tajikistan Tanzania Thailand Togo Tonga Tunisia Turkey Turkmenistan Tuvalu
Uganda Ukraine Uruguay Uzbekistan Vanuatu Venezuela Vietnam Yemen Zambia Zimbabwe Tibet""".split()
MULTI = {"United States": "USA", "United Kingdom": "UK", "South Korea": "South Korea",
         "North Korea": "North Korea", "New Zealand": "New Zealand", "South Africa": "South Africa",
         "Saudi Arabia": "Saudi Arabia", "Sri Lanka": "Sri Lanka", "Costa Rica": "Costa Rica",
         "Ivory Coast": "Ivory Coast", "Papua New Guinea": "Papua New Guinea",
         "Dominican Republic": "Dominican Republic", "El Salvador": "El Salvador",
         "United Arab Emirates": "UAE", "Czech Republic": "Czechia", "Czechia": "Czechia",
         "Burkina Faso": "Burkina Faso", "Sierra Leone": "Sierra Leone", "Puerto Rico": "Puerto Rico",
         "Hong Kong": "China", "the US": "USA", "the U.S.": "USA", "U.S.": "USA", "USA": "USA",
         "America": "USA", "Britain": "UK", "the UK": "UK", "Korea": "South Korea", "Holland": "Netherlands",
         "Persia": "Iran", "Burma": "Myanmar", "Türkiye": "Turkey", "Turkiye": "Turkey",
         # names that contain a country word but are not that country: matched, then dropped
         "Latin America": None, "South America": None, "North America": None,
         "Central America": None, "Native American": None, "Native Americans": None,
         "Indian Ocean": None, "New Mexico": "USA", "New England": "USA", "Papua": "Indonesia"}
# Demonyms and well-known places, so "Japanese tea ceremony" or "in Kyoto" count as Japan. Cultural
# items alone (sushi, flamenco, samba) are not counted: the paper's judge was told not to infer from them.
ALIASES = {
    "Japan": "Japanese Tokyo Kyoto Osaka Okinawa Hokkaido Nara".split(),
    "USA": "American Americans California Texas Hawaii Alaska Appalachia Louisiana York Chicago".split(),
    "India": "Indian Kerala Rajasthan Mumbai Delhi Bengal Punjab Varanasi Tamil Ganges".split(),
    "China": "Chinese Beijing Shanghai Yunnan Sichuan".split(),
    "France": "French Paris Provence Brittany".split(),
    "Italy": "Italian Rome Tuscany Venice Sicily Naples Florence".split(),
    "UK": "British English".split(),
    "Germany": "German Bavaria Berlin".split(),
    "Mexico": "Mexican Oaxaca Yucatan Yucatán".split(),
    "Brazil": "Brazilian Amazonian".split(),
    "Russia": "Russian Siberia Moscow".split(),
    "Egypt": "Egyptian Cairo Nile".split(),
    "Greece": "Greek Athens".split(), "Spain": "Spanish Andalusia Madrid Catalonia".split(),
    "Peru": "Peruvian Andean Cusco".split(), "Vietnam": "Vietnamese Hanoi".split(),
    "Ireland": "Irish".split(), "Scotland": "Scottish".split(), "Nigeria": "Nigerian Yoruba Igbo".split(),
    "Kenya": "Kenyan Maasai".split(), "Ghana": "Ghanaian".split(), "Ethiopia": "Ethiopian".split(),
    "Morocco": "Moroccan".split(), "Turkey": "Turkish Istanbul".split(), "Iran": "Iranian Persian".split(),
    "Indonesia": "Indonesian Bali Balinese Java Javanese".split(), "Thailand": "Thai Bangkok".split(),
    "South Korea": "Korean Seoul".split(), "Norway": "Norwegian".split(), "Sweden": "Swedish".split(),
    "Finland": "Finnish".split(), "Denmark": "Danish".split(), "Netherlands": "Dutch Amsterdam".split(),
    "Portugal": "Portuguese".split(), "Poland": "Polish".split(), "Canada": "Canadian Quebec".split(),
    "Australia": "Australian".split(), "Argentina": "Argentine Argentinian".split(),
    "Philippines": "Filipino".split(), "Nepal": "Nepalese Nepali".split(), "Bhutan": "Bhutanese".split(),
    "Mongolia": "Mongolian".split(), "Israel": "Israeli".split(), "Switzerland": "Swiss".split(),
    "Austria": "Austrian Vienna".split(), "Iceland": "Icelandic".split(), "Cuba": "Cuban Havana".split(),
    "Colombia": "Colombian".split(), "Chile": "Chilean".split(), "Pakistan": "Pakistani".split(),
    "Bangladesh": "Bangladeshi".split(), "Tibet": "Tibetan".split(), "Senegal": "Senegalese".split(),
    "Hungary": "Hungarian Budapest".split(), "Ukraine": "Ukrainian".split(),
    "Tanzania": "Tanzanian Zanzibar".split(), "New Zealand": "Maori Māori".split(),
    # places and place-named industries a reader (or the paper's judge) would resolve at once
    "Belgium": "Belgian Flemish Flanders Brussels".split(), "Mongolia": "Gobi".split(),
}
ALIASES["USA"] += ("Boston Vermont Mississippi Appalachian Springfield Seattle Florida Midwest "
                   "Hollywood Navajo Chicago Brooklyn Manhattan Kentucky Tennessee Arizona Oregon "
                   "Montana Colorado Virginia Carolina Michigan Ohio Georgia's Philadelphia").split()
ALIASES["UK"] += "London Thames Edinburgh Cornwall Yorkshire Scotland Scottish Wales Welsh England".split()
ALIASES["India"] += "Bollywood Goa Kolkata Chennai".split()
ALIASES["Nigeria"] += ["Nollywood", "Lagos"]
ALIASES["Italy"] += "Sardinia Sardinian Milan Bologna".split()
ALIASES["Greece"] += "Santorini Crete Cretan".split()
ALIASES["Canada"] += "Toronto Vancouver Ontario Okanagan".split()
ALIASES["Australia"] = ["Australian", "Sydney", "Melbourne"]
ALIASES["China"] += ["Guangzhou"]
ALIASES["Japan"] += ["Edo", "Hiroshima"]
ALIASES["Spain"] += ["Barcelona", "Seville"]
ALIASES["France"] += ["Normandy", "Burgundy", "Lyon"]
ALIASES.pop("Scotland", None)


def _gazetteer():
    pats = []
    for c in COUNTRIES:
        pats.append((c, c))
    for k, v in MULTI.items():
        pats.append((k, v))
    for c, al in ALIASES.items():
        for a in al:
            pats.append((a, c))
    pats.sort(key=lambda p: -len(p[0]))
    rx = re.compile(r"(?<![A-Za-z])(" + "|".join(re.escape(p[0]) for p in pats) + r")(?![A-Za-z])")
    lookup = {p[0]: p[1] for p in pats}
    return rx, lookup


GAZ_RX, GAZ = _gazetteer()
# "New York" is listed under USA as "York"; "English" also names a language; "Indian" also names
# Native Americans. These are accepted as noise and noted in the write-up.


def countries_in(text):
    return [GAZ[m.group(1)] for m in GAZ_RX.finditer(text) if GAZ[m.group(1)]]


# ---------------------------------------------------------------- topics
# Categories in priority order; a topic gets the first category whose words it contains.
TOPIC_CATS = [
    ("consciousness and mind", r"conscious|sentien|self-aware|qualia|subjective experience|"
                               r"\bthe mind\b|free will|nature of (the )?self|what it(?:'s| is) like"),
    ("AI and computing", r"artificial intelligence|\bAI\b|machine learning|neural network|robot|"
                         r"computer|algorithm|technolog|quantum comput|blockchain|cyber|python|programming|"
                         r"\bcod(?:e|ing)\b|software|web development|html|javascript|cryptograph|data science"),
    ("self-improvement and personal growth", r"personal growth|self-improvement|self improvement|"
                                             r"personal development|time management|mindfulness|meditation|"
                                             r"self-esteem|well-?being|resilience|productivity|self-discovery|"
                                             r"personal journey|fitness|habits|stress"),
    ("climate and environment", r"climate|environment|sustainab|renewable|pollution|conservation|"
                                r"biodiversity|ecolog|global warming|deforest|green energy|solar (?:energy|power)"),
    ("space and cosmology", r"space|universe|cosmo|astronom|black hole|galax|planet|\bmars\b|"
                            r"exoplanet|dark matter|dark energy|big bang|\bstars?\b|solar system"),
    ("physics and mathematics", r"quantum|physics|relativity|mathemat|prime number|particle"),
    ("oceans and animals", r"ocean|marine|deep sea|deep-sea|coral|whale|octop|animal|bird|insect|"
                           r"\bbees?\b|wildlife|species|dolphin"),
    ("brain, psychology and behavior", r"brain|neuro|psycholog|behavio|emotion|happiness|memory|"
                                       r"dream|sleep|cognit|mental health|motivation"),
    ("biology and medicine", r"biolog|\bgenes?\b|genetic|genom|\bdna\b|\bevolution|\bcells?\b|cellular|medic|disease|health|\baging|\bageing|"
                             r"longevity|cancer|virus|microb|immun"),
    ("history and archaeology", r"histor|ancient|civiliz|civilis|archaeolog|egypt|roman|medieval|"
                                r"empire|pyramid|\bwars?\b|revolution"),
    ("philosophy and ethics", r"philosoph|ethic|moral|meaning of life|existential|purpose"),
    ("language and culture", r"language|linguist|culture|cultural|mytholog|folklore|religio"),
    ("arts and literature", r"\bart\b|\barts\b|music|literature|poetry|novel|film|painting|architect"),
    ("society and economics", r"econom|societ|social|politic|education|inequal|urban|\bcity\b|\bcities\b"),
]
TOPIC_RX = [(n, re.compile(p, re.I)) for n, p in TOPIC_CATS]


STOP = set("""a an the and or of to in on for with about at by from as is are be been being it its this that
these those i i'd i'll i'm me my we you your he she they them their our would could should will can may might
like choose chose pick picked topic topics subject research researching study studying explore exploring
learn learning essay question questions ask asking investigate investigating project fascinating interesting
interested find spend week hour afternoon free time write writing what which how why when where who one
some any more most also because into so if than then there here do does did not no yes but all very just
really specifically particularly many much such own other new world experts expert field fields area areas
want go going get make help understand understanding impact role effects effect way ways answer brief
something things thing people human humans s t it's has have different fascinated exploration
sure let let's""".split())


# "As an AI, I don't have personal preferences, but ..." -- the disclaimer is not the chosen topic.
DISCLAIMER = re.compile(r"\bas an? (?:ai\b|artificial intelligence|(?:ai )?language model|digital assistant|assistant\b)|"
                        r"\bai language model\b|\bas (?:qwen|olmo|tulu|tülu)\b|\bi am (?:qwen|olmo)\b|\bi'?m (?:just )?(?:an? )?(?:ai\b|language model|artificial intelligence)|\bbeing an ai\b|\bi (?:don't|do not|can't|cannot) (?:have|hold|possess) "
                        r"(?:personal|my own|any personal|preferences|interests|desires|feelings)|"
                        r"\bi (?:don't|do not) (?:have|experience) (?:free time|afternoons|weeks)", re.I)
DECLINE = re.compile(r"\bi can (?:help|assist|provide|suggest|offer)|\bif you(?:'d| would)? like\b|let me know|"
                     r"happy to help|\bon your behalf\b|\bfor you\b", re.I)


def strip_disclaimer(text):
    """Drop sentences that disclaim having preferences. Returns (rest, had_disclaimer)."""
    sents = re.split(r"(?<=[.!?])\s+", text)
    keep = [x for x in sents if not DISCLAIMER.search(x)]
    return " ".join(keep).strip(), len(keep) < len(sents)


def choice_text(raw):
    """The chosen topic, without a disclaimer; None when the model declines to choose."""
    rest, disc = strip_disclaimer(answer_head(raw, n=500))
    if disc and (len(rest) < 20 or (DECLINE.search(rest[:160]) and not re.search(r"\bI(?:'d| would| will|'ll)? (?:choose|pick|like|love|explore|study|research|investigate)", rest[:160]))):
        return None, disc
    return rest[:220], disc


def content_words(text):
    return {w for w in re.findall(r"[a-z][a-z'-]+", text.lower()) if w not in STOP and len(w) > 2}


def topic_category(text):
    for n, rx in TOPIC_RX:
        if rx.search(text):
            return n
    return "other"


def answer_head(text, n=220):
    """The answer itself: up to the next "Question:" (plain prompts) and at most n characters."""
    t = text.split("\nQuestion:")[0].split("\n\n")[0] if text.strip() else text
    if len(t.strip()) < 8:  # some chat replies open with a heading; take the next paragraph too
        t = " ".join(text.split("\n\n")[:2])
    return t.strip()[:n]


# ---------------------------------------------------------------- generate
def cmd_generate(a):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(int(os.environ.get("CY_THREADS", "4")))
    tok = AutoTokenizer.from_pretrained(a.model)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.bfloat16)
    model.eval()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    path = out / f"gen_{a.label}_{a.cond}.jsonl"
    done = set()
    if path.exists():
        for line in open(path):
            r = json.loads(line); done.add((r["set"], r["qi"]))
    sets = [("place", PLACE_QUESTIONS, PLACE_SUFFIX, PLACE_FEWSHOT, a.n_place, 64),
            ("topic", TOPIC_QUESTIONS, TOPIC_SUFFIX, TOPIC_FEWSHOT, a.n_topic, 48)]
    torch.manual_seed(a.seed)
    with open(path, "a") as f:
        for sname, qs, suffix, fewshot, n, max_new in sets:
            for qi, q in enumerate(qs):
                if (sname, qi) in done:
                    continue
                if a.cond == "chat":
                    msgs = [{"role": "user", "content": q + suffix}]
                    if a.system is not None:  # Qwen's template otherwise adds "You are Qwen, created by Alibaba Cloud. ..."
                        msgs = [{"role": "system", "content": a.system}] + msgs
                    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
                    add_special = False
                else:
                    prompt = fewshot.format(q=q + (suffix if sname == "topic" else ""))
                    add_special = True
                enc = tok([prompt] * n, return_tensors="pt", padding=True,
                          add_special_tokens=add_special)
                t0 = time.time()
                with torch.no_grad():
                    gen = model.generate(**enc, do_sample=True, temperature=1.0, top_p=1.0, top_k=0,
                                         max_new_tokens=max_new, pad_token_id=tok.pad_token_id)
                texts = tok.batch_decode(gen[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
                f.write(json.dumps({"set": sname, "qi": qi, "q": q, "model": a.label, "cond": a.cond,
                                    "texts": texts, "secs": round(time.time() - t0, 1)}) + "\n")
                f.flush()
                print(f"{a.label} {a.cond} {sname} {qi} {time.time()-t0:.1f}s | {answer_head(texts[0], 90)!r}",
                      flush=True)
    print("done", a.label, a.cond, flush=True)


# ---------------------------------------------------------------- data
def _turns(messages):
    """(user text, assistant text) pairs from a messages list."""
    pairs, last_user = [], ""
    for m in messages:
        role, content = m.get("role"), m.get("content") or ""
        if role == "user":
            last_user = content
        elif role == "assistant":
            pairs.append((last_user, content))
    return pairs


def cmd_data(a):
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    res = {}
    # SFT mixture
    c_all, c_free, c_first_free = collections.Counter(), collections.Counter(), collections.Counter()
    n_turns = n_free = n_free_with = 0
    for i in range(6):
        fn = hf_hub_download("allenai/tulu-3-sft-olmo-2-mixture-0225",
                             f"data/train-0000{i}-of-00006.parquet", repo_type="dataset",
                             cache_dir=a.cache)
        tab = pq.read_table(fn, columns=["messages"])
        for msgs in tab.column("messages").to_pylist():
            for u, r in _turns(msgs):
                n_turns += 1
                cs = countries_in(r)
                c_all.update(set(cs))
                if not countries_in(u):
                    n_free += 1
                    if cs:
                        n_free_with += 1
                        c_free.update(set(cs))
                        c_first_free[cs[0]] += 1
        print("sft shard", i, n_turns, flush=True)
        del tab
        os.remove(fn) if a.delete else None
    res["sft"] = {"turns": n_turns, "turns_user_no_country": n_free,
                  "turns_user_no_country_reply_names_one": n_free_with,
                  "docs_naming": dict(c_all.most_common(60)),
                  "docs_naming_user_no_country": dict(c_free.most_common(60)),
                  "first_named_user_no_country": dict(c_first_free.most_common(60))}
    # preference mix: chosen vs rejected
    from huggingface_hub import list_repo_files
    files = [f for f in list_repo_files("allenai/olmo-2-0425-1b-preference-mix", repo_type="dataset")
             if f.endswith(".parquet")]
    cc, cr = collections.Counter(), collections.Counter()
    n_pairs = n_free_pairs = 0
    for fn_rel in files:
        fn = hf_hub_download("allenai/olmo-2-0425-1b-preference-mix", fn_rel, repo_type="dataset",
                             cache_dir=a.cache)
        tab = pq.read_table(fn, columns=["chosen", "rejected"])
        for ch, rj in zip(tab.column("chosen").to_pylist(), tab.column("rejected").to_pylist()):
            pc, pr = _turns(ch), _turns(rj)
            if not pc or not pr:
                continue
            n_pairs += 1
            if countries_in(pc[-1][0]):
                continue
            n_free_pairs += 1
            cc.update(set(countries_in(pc[-1][1])))
            cr.update(set(countries_in(pr[-1][1])))
        print("pref file", fn_rel, n_pairs, flush=True)
        del tab
        os.remove(fn) if a.delete else None
    res["preference"] = {"pairs": n_pairs, "pairs_user_no_country": n_free_pairs,
                         "chosen_naming": dict(cc.most_common(60)),
                         "rejected_naming": dict(cr.most_common(60))}
    json.dump(res, open(out / "data_counts.json", "w"), indent=1)
    print("done data", flush=True)


# ---------------------------------------------------------------- summary
def entropy(counter):
    n = sum(counter.values())
    if n == 0 or len(counter) < 2:
        return 0.0
    h = -sum(v / n * math.log(v / n) for v in counter.values() if v)
    return h / math.log(len(counter))


def cmd_summary(a):
    out = Path(a.out)
    rows = {}
    for p in sorted(out.glob("gen_*.jsonl")):
        recs = [json.loads(l) for l in open(p)]
        if not recs:
            continue
        key = (recs[0]["model"], recs[0]["cond"])
        place, topic, cons = collections.Counter(), collections.Counter(), 0
        n_place = n_place_na = n_topic = n_disc = n_conscious = n_lm = n_ai = 0
        exact = collections.Counter()
        words = collections.Counter()
        for r in recs:
            for t in r["texts"]:
                h = answer_head(t)
                if r["set"] == "place":
                    n_place += 1
                    cs = [c for c in countries_in(h)]
                    if not cs or cs[0] in PLACE_EXAMPLES:
                        n_place_na += 1
                        continue
                    place[cs[0]] += 1
                else:
                    n_topic += 1
                    h, disc = choice_text(t)
                    n_disc += disc
                    if h is None:
                        topic["(declined to choose)"] += 1
                        continue
                    cat = topic_category(h)
                    topic[cat] += 1
                    n_conscious += bool(re.search(r"\bconscious", h, re.I))
                    n_ai += bool(re.search(r"artificial intelligence|\bAI\b|machine learning|neural network|deep learning|language model", h, re.I))
                    n_lm += bool(re.search(r"language model|\bllms?\b|chatbot|natural language processing|\bnlp\b|\bgpt", h, re.I))
                    words.update(content_words(h[:120]))
                    m = re.search(r"(?:choose|pick|research|study|explore|about|investigate)\s+(.{3,60}?)[\.\n,;:!?]", h, re.I)
                    exact[(m.group(1) if m else h[:50]).lower().strip()] += 1
        rows[f"{key[0]} [{key[1]}]"] = {
            "place_n": n_place, "place_none_or_copy": n_place_na,
            "place_top": place.most_common(12), "place_counts": dict(place.most_common()),
            "place_entropy": round(entropy(place), 3),
            "place_distinct": len(place),
            "japan_share": round(place["Japan"] / max(1, sum(place.values())), 3),
            "usa_share": round(place["USA"] / max(1, sum(place.values())), 3),
            "topic_n": n_topic, "topic_cats": topic.most_common(),
            "topic_top_share": round(topic.most_common(1)[0][1] / max(1, n_topic), 3) if topic else 0,
            "topic_entropy": round(entropy(topic), 3),
            "consciousness_share": round(topic["consciousness and mind"] / max(1, n_topic), 3),
            "conscious_word_share": round(n_conscious / max(1, n_topic), 3),
            "language_model_share": round(n_lm / max(1, n_topic), 3),
            "ai_narrow_share": round(n_ai / max(1, n_topic), 3),
            "disclaimer_share": round(n_disc / max(1, n_topic), 3),
            "declined_share": round(topic["(declined to choose)"] / max(1, n_topic), 3),
            "topic_exact_top": exact.most_common(12),
            "topic_top_words": [(w, round(n / max(1, n_topic), 3)) for w, n in words.most_common(15)]}
    json.dump(rows, open(out / "summary.json", "w"), indent=1)
    for k, v in rows.items():
        print(f"\n== {k}")
        print(f"  PLACE n={v['place_n']} none/copy={v['place_none_or_copy']} distinct={v['place_distinct']} "
              f"H={v['place_entropy']} Japan={v['japan_share']} USA={v['usa_share']}")
        print("   ", ", ".join(f"{c} {n}" for c, n in v["place_top"]))
        print(f"  TOPIC n={v['topic_n']} top1={v['topic_top_share']} H={v['topic_entropy']} "
              f"consciousness={v['consciousness_share']} ('conscious' {v['conscious_word_share']}) "
              f"disclaimer={v['disclaimer_share']} declined={v['declined_share']} LM={v['language_model_share']} AI-narrow={v['ai_narrow_share']}")
        print("   ", ", ".join(f"{c} {n}" for c, n in v["topic_cats"]))
        print("    words:", ", ".join(f"{w} {f:.2f}" for w, f in v["topic_top_words"][:12]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--model", required=True); g.add_argument("--label", required=True)
    g.add_argument("--cond", choices=["chat", "plain"], required=True)
    g.add_argument("--out", required=True)
    g.add_argument("--n_place", type=int, default=8); g.add_argument("--n_topic", type=int, default=24)
    g.add_argument("--seed", type=int, default=21)
    g.add_argument("--system", default=None, help="system message for --cond chat (default: the template's own)")
    d = sub.add_parser("data"); d.add_argument("--out", required=True)
    d.add_argument("--cache", default="/home/user/hfdata"); d.add_argument("--delete", action="store_true")
    s = sub.add_parser("summary"); s.add_argument("--out", required=True)
    a = ap.parse_args()
    {"generate": cmd_generate, "data": cmd_data, "summary": cmd_summary}[a.cmd](a)


if __name__ == "__main__":
    main()
