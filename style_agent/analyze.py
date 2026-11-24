"""Offline stylometric analysis: turns raw text into a style profile (a plain dict).

Nothing here touches the network. Every number is a measurement of the author's
own text: word choice, sentence shape, punctuation and symbol habits, level.
"""
import re
import statistics
from collections import Counter

from . import lexicon as lx

WORD_RE = re.compile(r"[^\W\d_]+(?:[’'\-][^\W\d_]+)*")
CITE_PAREN = re.compile(r"\s?\([^()]*\b(?:1[89]|20)\d{2}[a-z]?\b[^()]*\)")
CITE_BRACKET = re.compile(r"\s?\[\d+(?:\s*[,\-–]\s*\d+)*\]")
REFERENCES = re.compile(r"^\s*(references|bibliography|works cited|daftar pustaka|referensi)\s*:?\s*$",
                        re.I | re.M)
SENT_END = re.compile(r"[.!?]+[\"”’)\]]*\s+(?=[\"“‘(\[]?[A-ZÀ-Ý0-9])")


def words_of(text):
    return WORD_RE.findall(text)


def per_1k(count, n_words):
    return round(count / n_words * 1000, 2) if n_words else 0.0


def pct(part, whole):
    return round(part / whole * 100, 1) if whole else 0.0


# ---------------------------------------------------------------- preparation

def clean(text):
    """Normalize line endings, drop the reference list, re-join hyphenated line breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    m = None
    for m in REFERENCES.finditer(text):
        pass  # keep the last match
    if m and m.start() > len(text) * 0.4:
        text = text[:m.start()]
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def paragraphs_of(text):
    """Prose paragraphs only: headings, captions, tables and stray lines are dropped."""
    blocks = re.split(r"\n\s*\n", text)
    if len(blocks) < 3:  # no blank lines: treat each line as a paragraph
        blocks = text.split("\n")
    out = []
    for b in blocks:
        b = re.sub(r"\s+", " ", b).strip()
        if len(words_of(b)) >= 12 and re.search(r"[.!?]", b):
            out.append(b)
    return out


def sentences_of(paragraph):
    sents, start = [], 0
    for m in SENT_END.finditer(paragraph):
        before = paragraph[start:m.start()]
        last = re.sub(r"[^\w.]", "", before.split()[-1]).lower().rstrip(".") if before.split() else ""
        if last in lx.ABBREVIATIONS or (len(last) == 1 and last.isalpha() and m.group().startswith(".")):
            continue  # "et al. Smith", "e.g. X", initials
        sents.append(paragraph[start:m.end()].strip())
        start = m.end()
    tail = paragraph[start:].strip()
    if tail:
        sents.append(tail)
    return sents


def detect_language(words):
    low = [w.lower() for w in words]
    scores = {lang: sum(w in sw for w in low) for lang, sw in lx.STOPWORDS.items()}
    lang = max(scores, key=scores.get)
    return lang if scores[lang] >= max(5, 0.15 * len(low)) else "other"


def count_phrase(phrase, low_text):
    return len(re.findall(r"(?<![\w-])" + re.escape(phrase) + r"(?![\w-])", low_text))


# ------------------------------------------------------------------- features

def sentence_features(sents, paras):
    lens = [len(words_of(s)) for s in sents]
    lens = [n for n in lens if n] or [0]
    ordered = sorted(lens)
    q = lambda f: ordered[min(len(ordered) - 1, int(f * len(ordered)))]
    return {
        "count": len(lens),
        "mean_words": round(statistics.mean(lens), 1),
        "median_words": statistics.median(lens),
        "stdev_words": round(statistics.pstdev(lens), 1),
        "p10_words": q(0.10), "p90_words": q(0.90), "max_words": ordered[-1],
        "pct_short_le_10": pct(sum(n <= 10 for n in lens), len(lens)),
        "pct_medium_11_29": pct(sum(10 < n < 30 for n in lens), len(lens)),
        "pct_long_ge_30": pct(sum(n >= 30 for n in lens), len(lens)),
        "pct_questions": pct(sum(s.rstrip("\"”’)") .endswith("?") for s in sents), len(sents)),
        "pct_exclamations": pct(sum(s.rstrip("\"”’)").endswith("!") for s in sents), len(sents)),
        "sentences_per_paragraph": round(len(sents) / len(paras), 1) if paras else 0,
        "words_per_paragraph": round(sum(lens) / len(paras), 1) if paras else 0,
    }


def punctuation_features(text, sents, n_words, lang):
    c = lambda pat: len(re.findall(pat, text))
    counts = {
        "comma": c(","),
        "semicolon": c(";"),
        "colon": c(r":(?![\d/])"),
        "em_dash": c("—"),
        "en_dash_as_dash": c(r"\s–\s"),
        "spaced_hyphen_as_dash": c(r"\s-\s"),
        "double_hyphen": c(r"(?<!-)--(?!-)"),
        "parentheses": c(r"\("),
        "square_brackets": c(r"\["),
        "exclamation": c("!"),
        "question": c(r"\?"),
        "ellipsis": c(r"…|\.\.\."),
        "slash": c(r"(?<=[^\W\d])/(?=[^\W\d])"),
        "ampersand": c("&"),
        "percent_sign": c("%"),
        "straight_double_quotes": c('"') // 2,
        "curly_double_quotes": c("“"),
        "curly_single_quotes": c("‘"),
        "hyphenated_words": c(r"[^\W\d_]-[^\W\d_]"),
    }
    commas = [s.count(",") for s in sents] or [0]
    low = text.lower()

    comma_before = {}
    for conj in lx.COMMA_BEFORE.get(lang, []):
        total = len(re.findall(r"\s" + conj + r"\b", low))
        if total >= 3:
            comma_before[conj] = {"with_comma": len(re.findall(r",\s" + conj + r"\b", low)), "total": total}

    serial = r"\w+, (?:[\w-]+ ){1,3}?(?:and|or|dan|atau|serta) \w"
    oxford = r"\w+, (?:[\w-]+ ){0,2}?[\w-]+, (?:and|or|dan|atau|serta) \w"
    opener_yes = opener_no = 0
    for s in sents:
        sl = s.lower().lstrip("\"“‘(")
        for t in sorted(lx.TRANSITIONS.get(lang, []), key=len, reverse=True):
            if t in lx.NO_COMMA_OPENERS or not sl.startswith(t):
                continue
            rest = sl[len(t):]
            if rest[:1] == ",":
                opener_yes += 1
            elif rest[:1] == " ":
                opener_no += 1
            break

    return {
        "counts": counts,
        "per_1k_words": {k: per_1k(v, n_words) for k, v in counts.items()},
        "commas_per_sentence": round(statistics.mean(commas), 2),
        "pct_sentences_without_comma": pct(sum(n == 0 for n in commas), len(commas)),
        "pct_sentences_with_3plus_commas": pct(sum(n >= 3 for n in commas), len(commas)),
        "comma_before_conjunction": comma_before,
        "serial_comma": {"with_final_comma": len(re.findall(oxford, low)),
                         "list_patterns_total": len(re.findall(serial, low))},
        "comma_after_opening_connector": {"with_comma": opener_yes, "without_comma": opener_no},
        "em_dash_spacing": {"spaced": c(r"\s—\s"), "tight": c(r"\S—\S")},
        "numbers": {"digits": c(r"(?<![\w.])\d[\d.,]*"),
                    "small_numbers_as_digits": c(r"(?<![\w.,])\d(?![\w.,%])"),
                    "small_numbers_spelled": len(re.findall(
                        r"\b(?:two|three|four|five|six|seven|eight|nine|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan)\b", low)),
                    "percent_word": len(re.findall(r"\b(?:percent|per cent|persen)\b", low))},
    }


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(1, n)


def lexical_features(words, sents, lang):
    low = [w.lower() for w in words]
    n = len(low) or 1
    window = 100
    if n >= window:  # moving-average type-token ratio: length-independent vocabulary richness
        mattr = statistics.mean(len(set(low[i:i + window])) / window for i in range(0, n - window + 1, 10))
    else:
        mattr = len(set(low)) / n
    long_words = sum(len(w) > 6 for w in low)
    n_sents = len(sents) or 1
    lix = n / n_sents + 100 * long_words / n
    band = ("very easy" if lix < 30 else "easy" if lix < 40 else "medium" if lix < 50
            else "difficult (academic)" if lix < 60 else "very difficult (dense academic)")
    level = {"lix": round(lix, 1), "lix_band": band}
    if lang == "en":
        syl = sum(syllables(w) for w in low)
        level["flesch_reading_ease"] = round(206.835 - 1.015 * n / n_sents - 84.6 * syl / n, 1)
        level["flesch_kincaid_grade"] = round(0.39 * n / n_sents + 11.8 * syl / n - 15.59, 1)
    stop = lx.STOPWORDS.get(lang, set())
    content = Counter(w for w in low if w not in stop and len(w) > 2)
    return {
        "total_words": len(low),
        "unique_words": len(set(low)),
        "vocabulary_richness_mattr": round(mattr, 3),
        "mean_word_length": round(statistics.mean(len(w) for w in low), 2) if low else 0,
        "pct_long_words_gt6": pct(long_words, n),
        "pct_words_used_once": pct(sum(1 for v in Counter(low).values() if v == 1), len(set(low)) or 1),
        "level": level,
        "top_content_words": content.most_common(50),
    }


def ngram_features(sents, lang):
    stop = lx.STOPWORDS.get(lang, set())
    grams = {2: Counter(), 3: Counter(), 4: Counter()}
    for s in sents:
        w = [x.lower() for x in words_of(s)]
        for n in grams:
            for i in range(len(w) - n + 1):
                g = w[i:i + n]
                if n < 4 and (g[0] in stop or g[-1] in stop):
                    continue  # 2-3 grams: content collocations only
                grams[n][" ".join(g)] += 1
    keep = lambda cnt, least, top: [(g, k) for g, k in cnt.most_common(top) if k >= least]
    return {"bigrams": keep(grams[2], 3, 30), "trigrams": keep(grams[3], 2, 20),
            "recurring_phrases": keep(grams[4], 3, 20)}


def marker_features(text, sents, words, lang):
    low_text = text.lower()
    low = Counter(w.lower() for w in words)
    n = len(words)
    count_list = lambda items: sorted(((p, count_phrase(p, low_text)) for p in items),
                                      key=lambda kv: -kv[1])
    transitions = [(p, k) for p, k in count_list(lx.TRANSITIONS.get(lang, [])) if k]
    hedges = [(p, k) for p, k in count_list(lx.HEDGES.get(lang, [])) if k]
    boosters = [(p, k) for p, k in count_list(lx.BOOSTERS.get(lang, [])) if k]
    fp = lx.FIRST_PERSON.get(lang, {"singular": [], "plural": []})

    firsts = Counter()
    conj_open = trans_open = 0
    for s in sents:
        w = words_of(s)
        if not w:
            continue
        firsts[w[0].lower()] += 1
        conj_open += w[0].lower() in lx.COORD_CONJ.get(lang, [])
        sl = s.lower().lstrip("\"“‘(")
        trans_open += any(re.match(re.escape(t) + r"\b", sl) for t in lx.TRANSITIONS.get(lang, []))

    out = {
        "transitions": transitions[:25],
        "transitions_per_1k": per_1k(sum(k for _, k in transitions), n),
        "hedges": hedges[:15], "hedges_per_1k": per_1k(sum(k for _, k in hedges), n),
        "boosters": boosters[:15], "boosters_per_1k": per_1k(sum(k for _, k in boosters), n),
        "first_person_singular": sum(low[w] for w in fp["singular"]),
        "first_person_plural": sum(low[w] for w in fp["plural"]),
        "sentence_openers": [(w, pct(k, len(sents))) for w, k in firsts.most_common(12)],
        "pct_sentences_opening_with_conjunction": pct(conj_open, len(sents)),
        "pct_sentences_opening_with_connector": pct(trans_open, len(sents)),
    }
    if lang == "en":
        out["contractions"] = len(re.findall(
            r"\b\w+n[’']t\b|\b\w+[’'](?:re|ve|ll|m|d)\b|\b(?:it|that|there|here|let|what|he|she)[’']s\b", low_text))
        out["passive_per_100_sentences"] = pct(len(re.findall(
            r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?\w+(?:ed|en|wn)\b", low_text)), len(sents))
        brit, amer = (len(re.findall(lx.SPELLING[k], low_text)) for k in ("british", "american"))
        out["spelling"] = {"british_markers": brit, "american_markers": amer}
    elif lang == "id":
        out["passive_per_100_sentences"] = pct(len(re.findall(r"\bdi[a-z]{4,}(?:kan|i|nya)?\b", low_text)), len(sents))
    return out


def synonym_features(text, lang):
    """For each group of interchangeable words, which one does the author pick?"""
    out = {}
    for concept, variants in lx.SYNONYM_SETS.get(lang, {}).items():
        work, counts = text.lower(), {}
        for name, pat in sorted(variants.items(), key=lambda kv: -len(kv[0])):
            rx = re.compile(r"(?<![\w-])(?:" + pat + r")(?![\w-])")
            counts[name] = len(rx.findall(work))
            work = rx.sub(" _ ", work)  # so "akan tetapi" is not also counted as "tetapi"
        if sum(counts.values()) >= 2:
            out[concept] = dict(sorted(counts.items(), key=lambda kv: -kv[1]))
    return out


def pick_excerpts(paras, mean_len, max_excerpts=6, max_words=900):
    """Representative paragraphs, spread across the text, used as few-shot samples."""
    cands = []
    for i, p in enumerate(paras):
        n = len(words_of(p))
        if 40 <= n <= 200:
            s = sentences_of(p)
            cands.append((abs(n / max(1, len(s)) - mean_len), i, p, n))
    if not cands:
        cands = [(0, i, p, len(words_of(p))) for i, p in enumerate(paras)]
    buckets = {}
    for cand in cands:  # best paragraph from each section of the document
        b = cand[1] * max_excerpts // max(1, len(paras))
        if b not in buckets or cand[0] < buckets[b][0]:
            buckets[b] = cand
    out, total = [], 0
    for _, _, p, n in sorted(buckets.values(), key=lambda c: c[1]):
        if total + n > max_words and out:
            break
        out.append(p)
        total += n
    return out


# -------------------------------------------------------------------- profile

def analyze(raw_text, with_excerpts=True):
    """Full style profile of a text."""
    text = clean(raw_text)
    citations = {"author_year_parenthetical": len(CITE_PAREN.findall(text)),
                 "numeric_bracket": len(CITE_BRACKET.findall(text))}
    text = CITE_BRACKET.sub("", CITE_PAREN.sub("", text))  # citations are not style punctuation
    text = re.sub(r" +([.,;:])", r"\1", text)
    paras = paragraphs_of(text)
    prose = "\n\n".join(paras)
    sents = [s for p in paras for s in sentences_of(p)]
    words = words_of(prose)
    if len(words) < 30:
        raise ValueError("Not enough prose to analyze (need at least a few sentences).")
    lang = detect_language(words)
    sent = sentence_features(sents, paras)
    profile = {
        "language": lang,
        "lexical": lexical_features(words, sents, lang),
        "sentences": sent,
        "punctuation": punctuation_features(prose, sents, len(words), lang),
        "markers": marker_features(prose, sents, words, lang),
        "word_preferences": synonym_features(prose, lang),
        "ngrams": ngram_features(sents, lang),
        "citations": citations,
    }
    if with_excerpts:
        profile["excerpts"] = pick_excerpts(paras, sent["mean_words"])
    return profile


# ------------------------------------------------------------- style checking

NEVER_USED = {  # mark -> (label, regex that detects it in a candidate text)
    "em_dash": ("em dashes (—)", r"—"),
    "en_dash_as_dash": ("spaced en dashes ( – )", r"\s–\s"),
    "semicolon": ("semicolons", r";"),
    "exclamation": ("exclamation marks", r"!"),
    "ellipsis": ("ellipses", r"…|\.\.\."),
    "ampersand": ("ampersands (&)", r"&"),
    "double_hyphen": ("double hyphens (--)", r"(?<!-)--(?!-)"),
    "parentheses": ("parentheses", r"\("),
    "colon": ("colons", r":(?![\d/])"),
}
MIN_WORDS_FOR_NEVER = 800  # "never uses X" only means something on a decent sample


def never_used_marks(profile):
    if profile["lexical"]["total_words"] < MIN_WORDS_FOR_NEVER:
        return []
    return [k for k in NEVER_USED if profile["punctuation"]["counts"].get(k, 0) == 0]


def violations(profile, text):
    """Hard breaks: marks the author never uses that appear in `text`."""
    text = CITE_BRACKET.sub("", CITE_PAREN.sub("", text))
    found = [NEVER_USED[k][0] for k in never_used_marks(profile) if re.search(NEVER_USED[k][1], text)]
    if (profile["language"] == "en" and profile["markers"].get("contractions") == 0
            and profile["lexical"]["total_words"] >= MIN_WORDS_FOR_NEVER
            and re.search(r"\b\w+n[’']t\b|\b\w+[’'](?:re|ve|ll|m)\b|\b(?:it|that|there|here|let)[’']s\b", text, re.I)):
        found.append("contractions")
    return found


def drift(profile, text):
    """Soft differences between `text` and the profile. Needs ~60+ words to be meaningful."""
    try:
        cand = analyze(text, with_excerpts=False)
    except ValueError:
        return []
    if cand["lexical"]["total_words"] < 60:
        return []
    notes = []

    def check(label, mine, theirs, rel, floor):
        if abs(theirs - mine) > max(floor, rel * mine):
            notes.append(f"{label}: text {theirs} vs your usual {mine}")

    check("words per sentence", profile["sentences"]["mean_words"], cand["sentences"]["mean_words"], 0.25, 4)
    check("commas per sentence", profile["punctuation"]["commas_per_sentence"],
          cand["punctuation"]["commas_per_sentence"], 0.35, 0.5)
    check("long words (%)", profile["lexical"]["pct_long_words_gt6"], cand["lexical"]["pct_long_words_gt6"], 0.25, 5)
    check("connectors per 1,000 words", profile["markers"]["transitions_per_1k"],
          cand["markers"]["transitions_per_1k"], 0.5, 8)
    check("readability (LIX)", profile["lexical"]["level"]["lix"], cand["lexical"]["level"]["lix"], 0.2, 7)
    return notes
