"""Turn a numeric style profile into a readable style guide.

The same guide is shown to you (`report`) and given to the model that rewrites
text in your voice, so what you read is exactly what the rewriter follows.
"""
from .analyze import NEVER_USED, never_used_marks

LANG_NAMES = {"en": "English", "id": "Indonesian", "other": "not auto-detected"}


def _share(d, a, b):
    total = d.get(b, 0)
    return round(d.get(a, 0) / total * 100) if total else None


def word_preference_lines(profile):
    lines = []
    for concept, counts in profile["word_preferences"].items():
        total = sum(counts.values())
        if total < 3:
            continue
        ranked = list(counts.items())
        used = ", ".join(f"“{w}” {k}×" for w, k in ranked if k)
        unused = ", ".join(f"“{w}”" for w, k in ranked if not k)
        line = f"- {concept}: {used}"
        if unused:
            line += f"; never: {unused}"
        lines.append(line)
    return lines


def render(profile):
    lex, sen, pun, mk = profile["lexical"], profile["sentences"], profile["punctuation"], profile["markers"]
    lvl, rate, cnt = lex["level"], pun["per_1k_words"], pun["counts"]
    out = []
    add = out.append

    add("## Overview")
    add(f"- Language: {LANG_NAMES.get(profile['language'], profile['language'])}; "
        f"learned from {lex['total_words']:,} words of prose in {sen['count']} sentences.")
    level = f"- Language level: LIX {lvl['lix']} ({lvl['lix_band']})"
    if "flesch_kincaid_grade" in lvl:
        level += (f", Flesch reading ease {lvl['flesch_reading_ease']}, "
                  f"Flesch-Kincaid grade {lvl['flesch_kincaid_grade']}")
    add(level + ".")
    add(f"- Vocabulary: average word {lex['mean_word_length']} letters, {lex['pct_long_words_gt6']}% long words "
        f"(7+ letters), richness {lex['vocabulary_richness_mattr']} "
        f"(share of distinct words per 100-word window; higher = more varied).")

    add("\n## Sentences")
    add(f"- Length: average {sen['mean_words']} words, median {sen['median_words']}, "
        f"typical range {sen['p10_words']} to {sen['p90_words']}, longest {sen['max_words']}.")
    add(f"- Mix: {sen['pct_short_le_10']}% short (10 words or fewer), {sen['pct_medium_11_29']}% medium, "
        f"{sen['pct_long_ge_30']}% long (30+).")
    if sen["words_per_paragraph"] <= 300:
        add(f"- Paragraphs: about {sen['sentences_per_paragraph']} sentences / {sen['words_per_paragraph']} words each.")
    add(f"- Questions end {sen['pct_questions']}% of sentences; exclamations {sen['pct_exclamations']}%.")
    openers = ", ".join(f"“{w}” {p}%" for w, p in mk["sentence_openers"][:8])
    add(f"- Most common first words: {openers}.")
    add(f"- {mk['pct_sentences_opening_with_connector']}% of sentences open with a connector; "
        f"{mk['pct_sentences_opening_with_conjunction']}% open with a coordinating conjunction.")

    add("\n## Punctuation and symbols")
    add(f"- Commas: {rate['comma']} per 1,000 words, {pun['commas_per_sentence']} per sentence on average; "
        f"{pun['pct_sentences_without_comma']}% of sentences have none, "
        f"{pun['pct_sentences_with_3plus_commas']}% have three or more.")
    cb = [f"“{c}” {_share(v, 'with_comma', 'total')}%" for c, v in pun["comma_before_conjunction"].items()]
    if cb:
        add(f"- Comma placed before a conjunction (share of its uses): {', '.join(cb)}.")
    ao = pun["comma_after_opening_connector"]
    if ao["with_comma"] + ao["without_comma"] >= 3:
        add(f"- Comma after an opening connector (“However, …”): {ao['with_comma']} of "
            f"{ao['with_comma'] + ao['without_comma']} times.")
    sc = pun["serial_comma"]
    if sc["list_patterns_total"] >= 3:
        add(f"- Lists of three or more: final comma before and/or in about {sc['with_final_comma']} of "
            f"{sc['list_patterns_total']} list-like patterns (rough estimate).")
    labels = [("semicolon", "Semicolons"), ("colon", "Colons"), ("parentheses", "Parentheses"),
              ("em_dash", "Em dashes (—)"), ("en_dash_as_dash", "Spaced en dashes ( – )"),
              ("spaced_hyphen_as_dash", "Spaced hyphens used as dashes ( - )"),
              ("hyphenated_words", "Hyphenated words"), ("slash", "Slashes between words"),
              ("ellipsis", "Ellipses"), ("ampersand", "Ampersands"), ("percent_sign", "Percent signs")]
    for key, label in labels:
        if cnt[key]:
            add(f"- {label}: {cnt[key]} uses ({rate[key]} per 1,000 words).")
    ds = pun["em_dash_spacing"]
    if cnt["em_dash"]:
        add(f"- Em dash spacing: {'spaced' if ds['spaced'] >= ds['tight'] else 'no spaces'} "
            f"({ds['spaced']} spaced, {ds['tight']} tight).")
    q = [(cnt["straight_double_quotes"], 'straight "double"'), (cnt["curly_double_quotes"], "curly “double”"),
         (cnt["curly_single_quotes"], "curly ‘single’")]
    if any(k for k, _ in q):
        add(f"- Quotation marks: mostly {max(q)[1]}.")
    nums = pun["numbers"]
    add(f"- Numbers: small numbers written as digits {nums['small_numbers_as_digits']}×, spelled out "
        f"{nums['small_numbers_spelled']}×; “%” sign {cnt['percent_sign']}×, the word percent/persen "
        f"{nums['percent_word']}×.")
    never = [NEVER_USED[k][0] for k in never_used_marks(profile)]
    if never:
        add(f"- NEVER used anywhere in the sample: {', '.join(never)}. Do not introduce them.")

    add("\n## Voice")
    add(f"- First person: singular {mk['first_person_singular']}×, plural {mk['first_person_plural']}×.")
    if "contractions" in mk:
        add(f"- Contractions (don't, it's): {mk['contractions']}×.")
    if "passive_per_100_sentences" in mk:
        add(f"- Passive constructions: roughly {mk['passive_per_100_sentences']} per 100 sentences (estimate).")
    if "spelling" in mk and sum(mk["spelling"].values()):
        sp = mk["spelling"]
        add(f"- Spelling: {'British' if sp['british_markers'] > sp['american_markers'] else 'American'} "
            f"(British markers {sp['british_markers']}, American {sp['american_markers']}).")
    add(f"- Hedging words: {mk['hedges_per_1k']} per 1,000 words"
        + (f" (most used: {', '.join(w for w, _ in mk['hedges'][:6])})" if mk["hedges"] else "") + ".")
    add(f"- Emphasis words: {mk['boosters_per_1k']} per 1,000 words"
        + (f" (most used: {', '.join(w for w, _ in mk['boosters'][:6])})" if mk["boosters"] else "") + ".")
    cit = profile["citations"]
    if sum(cit.values()):
        add(f"- Citations: {cit['author_year_parenthetical']} author-year in parentheses, "
            f"{cit['numeric_bracket']} numeric in brackets.")

    add("\n## Word choice")
    if mk["transitions"]:
        add(f"- Connectors ({mk['transitions_per_1k']} per 1,000 words), by frequency: "
            + ", ".join(f"{w} {k}×" for w, k in mk["transitions"][:18]) + ".")
    prefs = word_preference_lines(profile)
    if prefs:
        add("- Preferred word among alternatives with the same meaning:")
        out.extend("  " + line for line in prefs)
    add("- Most used content words: " + ", ".join(w for w, _ in lex["top_content_words"][:40]) + ".")
    ng = profile["ngrams"]
    if ng["bigrams"] or ng["trigrams"]:
        add("- Habitual word pairings: " + ", ".join(g for g, _ in (ng["trigrams"][:10] + ng["bigrams"][:15])) + ".")
    if ng["recurring_phrases"]:
        add("- Recurring phrasings: " + "; ".join(f"“{g}”" for g, _ in ng["recurring_phrases"][:12]) + ".")

    if profile.get("qualitative"):
        add("\n## Qualitative notes (from deep analysis)")
        add(profile["qualitative"])
    return "\n".join(out)
