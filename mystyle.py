"""mystyle.py - learns how you write, then rewrites other text in your wording.

Run it with no arguments (or the Run button in VS Code) for the guided mode:
it asks for a document you wrote, learns your style, then lets you paste text.

    python mystyle.py                      guided mode
    python mystyle.py learn paper.pdf      learn from a document (.pdf .docx .txt .md)
    python mystyle.py report               show your style profile
    python mystyle.py rewrite "some text"  rewrite text in your wording
    python mystyle.py check "some text"    offline: does this text break your habits?
    python mystyle.py suggest "a word for very important"

Needs: pip install -U anthropic pypdf python-docx
Rewriting needs a Claude API key in the ANTHROPIC_API_KEY environment variable.

Generated from the style_agent package by build_mystyle.py. Edit the package, not this file.
"""

# ============================== lexicon ==============================

STOPWORDS = {
    "en": set("""a about above after again against all also am an and any are as at be because been
before being below between both but by can could did do does doing down during each few for from
further had has have having he her here hers him his how i if in into is it its just may me might
more most must my no nor not of off on once only or other our ours out over own same she should so
some such than that the their theirs them then there these they this those through to too under
until up us very was we were what when where which while who whom why will with would you your
yours one two also however thus therefore""".split()),
    "id": set("""yang dan di ke dari untuk pada dengan ini itu adalah atau juga dalam tidak akan
oleh sebagai karena ada mereka kami kita saya aku ia dia anda bahwa dapat bisa telah sudah lebih
serta para saat seperti hal tersebut yaitu yakni secara maka agar supaya jika bila ketika namun
tetapi tapi sehingga antara atas bawah setelah sebelum hingga sampai masih hanya saja pun lah kah
nya se suatu sebuah setiap tiap banyak beberapa lain lainnya merupakan menjadi terhadap tentang
belum harus perlu sangat paling kali sendiri baik bagi kepada tanpa selama sejak sedangkan
meskipun walaupun apa siapa mana bagaimana mengapa kapan dimana terdapat demikian oleh""".split()),
}

# Connectors / transitions. Multi-word phrases are matched as phrases.
TRANSITIONS = {
    "en": ["however", "therefore", "moreover", "furthermore", "thus", "hence", "nevertheless",
           "nonetheless", "consequently", "additionally", "in addition", "on the other hand",
           "in contrast", "for example", "for instance", "in other words", "as a result",
           "in conclusion", "overall", "meanwhile", "similarly", "likewise", "instead", "indeed",
           "in fact", "specifically", "in particular", "first", "second", "third", "finally",
           "then", "also", "besides", "although", "though", "whereas", "while", "despite",
           "in order to", "due to", "because of", "such as", "that is", "in this case",
           "to begin with", "in summary", "notably", "importantly", "interestingly"],
    "id": ["namun", "oleh karena itu", "oleh sebab itu", "selain itu", "dengan demikian",
           "sehingga", "kemudian", "selanjutnya", "akan tetapi", "tetapi", "meskipun", "walaupun",
           "sedangkan", "sementara itu", "misalnya", "contohnya", "dengan kata lain", "akibatnya",
           "pada akhirnya", "secara keseluruhan", "di sisi lain", "sebaliknya", "bahkan",
           "terlebih lagi", "pertama", "kedua", "ketiga", "terakhir", "maka", "jadi",
           "antara lain", "berdasarkan", "hal ini", "dalam hal ini", "di samping itu",
           "lebih lanjut", "singkatnya", "artinya"],
}

# Sentence-opening connectors that are NOT normally followed by a comma
# (excluded when measuring the "comma after opener" habit).
NO_COMMA_OPENERS = set("""although though whereas while despite in order to due to because of
such as meskipun walaupun sedangkan berdasarkan hal ini maka""".split()) | {
    "in order to", "due to", "because of", "such as", "hal ini"}

HEDGES = {
    "en": ["may", "might", "could", "perhaps", "possibly", "likely", "seems", "seem", "appears",
           "appear", "suggests", "suggest", "somewhat", "relatively", "generally", "often",
           "tends", "tend", "arguably", "approximately", "roughly", "potentially", "probably"],
    "id": ["mungkin", "kemungkinan", "cenderung", "tampaknya", "sepertinya", "diduga",
           "kurang lebih", "sekitar", "relatif", "umumnya", "biasanya", "kiranya"],
}

BOOSTERS = {
    "en": ["clearly", "obviously", "definitely", "certainly", "very", "extremely", "highly",
           "significantly", "strongly", "always", "never", "undoubtedly", "really", "truly",
           "absolutely", "greatly"],
    "id": ["sangat", "jelas", "tentu", "pasti", "selalu", "amat", "sekali", "sungguh",
           "benar-benar", "tentunya"],
}

FIRST_PERSON = {
    "en": {"singular": ["i", "my", "me", "mine", "myself"],
           "plural": ["we", "our", "us", "ours", "ourselves"]},
    "id": {"singular": ["saya", "aku", "penulis"], "plural": ["kami", "kita"]},
}

COORD_CONJ = {"en": ["and", "but", "so", "or", "yet"], "id": ["dan", "tetapi", "tapi", "atau", "jadi"]}

# Conjunctions for which we measure "is there a comma in front of it?"
COMMA_BEFORE = {
    "en": ["and", "but", "so", "or", "which", "because", "while", "although", "since"],
    "id": ["dan", "tetapi", "namun", "sehingga", "karena", "yang", "serta", "atau", "sedangkan"],
}

# Groups of interchangeable words. The analyzer counts which variant the author
# actually reaches for. Values are regexes (matched on word boundaries, case-insensitive).
SYNONYM_SETS = {
    "en": {
        "use": {"use": r"us(?:e|es|ed|ing)", "utilize": r"utili[sz]\w*", "employ": r"employ(?:s|ed|ing)?",
                "leverage": r"leverag\w*", "apply": r"appl(?:y|ies|ied|ying)"},
        "show": {"show": r"show(?:s|ed|n|ing)?", "demonstrate": r"demonstrat\w*",
                 "indicate": r"indicat\w*", "reveal": r"reveal\w*", "illustrate": r"illustrat\w*",
                 "highlight": r"highlight\w*", "suggest": r"suggest\w*"},
        "contrast": {"however": r"however", "but": r"but", "nevertheless": r"nevertheless|nonetheless",
                     "yet": r"yet", "on the other hand": r"on the other hand", "although": r"although|though"},
        "cause": {"because": r"because(?! of)", "since": r"since", "due to": r"due to",
                  "because of": r"because of", "owing to": r"owing to"},
        "addition": {"also": r"also", "moreover": r"moreover", "furthermore": r"furthermore",
                     "in addition": r"in addition", "additionally": r"additionally", "besides": r"besides"},
        "result": {"therefore": r"therefore", "thus": r"thus", "hence": r"hence",
                   "consequently": r"consequently", "as a result": r"as a result"},
        "important": {"important": r"important\w*", "crucial": r"crucial\w*", "significant": r"significant\w*",
                      "essential": r"essential\w*", "vital": r"vital\w*", "key": r"key", "critical": r"critical\w*"},
        "help": {"help": r"help(?:s|ed|ing)?", "assist": r"assist\w*", "facilitate": r"facilitat\w*",
                 "support": r"support(?:s|ed|ing)?", "enable": r"enabl\w*"},
        "get": {"get": r"get(?:s|ting)?|got(?:ten)?", "obtain": r"obtain\w*", "acquire": r"acquir\w*",
                "gain": r"gain(?:s|ed|ing)?"},
        "large": {"large": r"larg(?:e|er|est)", "big": r"big(?:ger|gest)?", "substantial": r"substantial\w*",
                  "considerable": r"considerabl\w*", "huge": r"huge"},
        "many": {"many": r"many", "numerous": r"numerous", "several": r"several",
                 "a lot of": r"a lot of|lots of", "various": r"various"},
        "example": {"for example": r"for example", "for instance": r"for instance", "such as": r"such as",
                    "e.g.": r"e\.g\."},
        "about": {"about": r"about", "regarding": r"regarding", "concerning": r"concerning",
                  "in terms of": r"in terms of", "related to": r"related to"},
        "try": {"try": r"tr(?:y|ies|ied|ying)", "attempt": r"attempt\w*", "aim": r"aim(?:s|ed|ing)?",
                "seek": r"seek(?:s|ing)?|sought"},
        "need": {"need": r"need(?:s|ed|ing)?", "require": r"requir\w*", "must": r"must", "have to": r"ha(?:ve|s|d) to"},
        "find": {"find": r"find(?:s|ing)?|found", "discover": r"discover\w*", "identify": r"identif\w*",
                 "observe": r"observ\w*"},
        "improve": {"improve": r"improv\w*", "enhance": r"enhanc\w*", "increase": r"increas\w*",
                    "boost": r"boost\w*", "optimize": r"optimi[sz]\w*"},
        "problem": {"problem": r"problems?", "issue": r"issues?", "challenge": r"challenges?",
                    "obstacle": r"obstacles?"},
        "rather": {"instead of": r"instead of", "rather than": r"rather than", "as opposed to": r"as opposed to"},
        "start": {"start": r"start(?:s|ed|ing)?", "begin": r"beg[iau]n(?:s|ning)?", "commence": r"commenc\w*"},
        "think": {"think": r"think(?:s|ing)?|thought", "believe": r"believ\w*", "argue": r"argu\w*",
                  "assume": r"assum\w*", "consider": r"consider(?:s|ed|ing)?"},
    },
    "id": {
        "kontras": {"namun": r"namun", "tetapi": r"tetapi", "akan tetapi": r"akan tetapi", "tapi": r"tapi"},
        "sebab": {"karena": r"karena", "sebab": r"sebab", "dikarenakan": r"dikarenakan",
                  "disebabkan": r"disebabkan", "akibat": r"akibat"},
        "memakai": {"menggunakan": r"menggunakan|digunakan", "memakai": r"memakai|dipakai",
                    "memanfaatkan": r"memanfaatkan|dimanfaatkan"},
        "menunjukkan": {"menunjukkan": r"menunjukkan|ditunjukkan", "memperlihatkan": r"memperlihatkan",
                        "menggambarkan": r"menggambarkan", "mengindikasikan": r"mengindikasikan"},
        "tambahan": {"selain itu": r"selain itu", "di samping itu": r"di samping itu", "juga": r"juga",
                     "serta": r"serta"},
        "akibat": {"sehingga": r"sehingga", "maka": r"maka", "oleh karena itu": r"oleh (?:karena|sebab) itu",
                   "dengan demikian": r"dengan demikian", "jadi": r"jadi"},
        "definisi": {"yaitu": r"yaitu", "yakni": r"yakni", "adalah": r"adalah", "merupakan": r"merupakan",
                     "ialah": r"ialah"},
        "penting": {"penting": r"penting", "krusial": r"krusial", "signifikan": r"signifikan", "utama": r"utama"},
        "mampu": {"dapat": r"dapat", "bisa": r"bisa", "mampu": r"mampu"},
        "tujuan": {"agar": r"agar", "supaya": r"supaya", "untuk": r"untuk", "guna": r"guna"},
        "contoh": {"misalnya": r"misalnya", "contohnya": r"contohnya", "seperti": r"seperti",
                   "antara lain": r"antara lain"},
        "masalah": {"masalah": r"masalah", "permasalahan": r"permasalahan", "kendala": r"kendala",
                    "tantangan": r"tantangan"},
        "meningkatkan": {"meningkatkan": r"meningkatkan", "memperbaiki": r"memperbaiki",
                         "mengoptimalkan": r"mengoptimalkan", "menambah": r"menambah"},
    },
}

ABBREVIATIONS = set("""e.g i.e etc vs cf al fig figs eq eqs no nos dr mr mrs ms prof st sr jr vol pp p
ed eds approx dept inc ltd dll dsb dst dkk hlm tsb yth""".split())

_ROOTS = (r"(?:organi|reali|recogni|utili|optimi|minimi|maximi|generali|normali|characteri|summari|"
          r"emphasi|categori|visuali|standardi|speciali|prioriti|initiali|regulari|centrali|tokeni|"
          r"parameteri|formali|penali|capitali|locali|randomi|digiti|moderni|stabili|synthesi|hypothesi|"
          r"criminali|legali|incentivi|contextuali|operationali|criti[cs]i|apologi|memori|authori)")
SPELLING = {  # British vs American markers
    "british": r"\b" + _ROOTS + r"s(?:e|ed|es|ing|ation|ations)\b|\b(?:colour|behaviour|favour|labour|centre|programme|analys[ei]|modelling|labelled|neighbour)\w*\b",
    "american": r"\b" + _ROOTS + r"z(?:e|ed|es|ing|ation|ations)\b|\b(?:color|behavior|favor|labor|center|analyz|modeling|labeled|neighbor)\w*\b",
}

# ============================== extract ==============================
import re
import statistics
from collections import Counter
from pathlib import Path

HEADING = re.compile(r"^(?:(?:\d+(?:\.\d+)*|[A-Z])\.?\s+)?[A-Z][^.!?]{0,70}$")
SECTION_WORDS = re.compile(r"^(abstract|keywords|references|bibliography|acknowledg\w+|daftar pustaka|abstrak)\s*:?$", re.I)
MATH_CHARS = re.compile(r"[\U0001D400-\U0001D7FF∑∏∈≤≥≠≈∥⊕⊙√∞∂∇←→↦]")


def _is_noise(line):
    """Table rows, equations, axis labels: mostly symbols and numbers, not prose."""
    letters = sum(ch.isalpha() for ch in line)
    return letters / len(line) < 0.6 or bool(MATH_CHARS.search(line))


def tidy_pdf(pages):
    """Rebuild prose paragraphs from hard-wrapped PDF text.

    Drops running headers/footers (lines repeated across pages), page numbers,
    table rows and equations, sets headings apart, and re-joins words that were
    hyphenated at a line break.
    """
    page_lines = [[l.strip() for l in page.splitlines()] for page in pages]
    norm = lambda l: re.sub(r"\d+", "#", l)
    seen = Counter(n for lines in page_lines for n in {norm(l) for l in lines if l})
    repeated = {n for n, k in seen.items() if k >= 3 and len(n) < 160}
    lines = [l for ls in page_lines for l in ls if norm(l) not in repeated and not re.fullmatch(r"\d{1,4}", l)]
    # ACM-style front matter (CCS concepts, reference format, permission notice)
    text = "\n".join(lines)
    m = re.search(r"^CCS Concepts$.*?^(?=1\s+Introduction$)", text, re.S | re.M)
    if m and len(m.group()) < 5000:
        text = text[:m.start()] + text[m.end():]
    lines = text.split("\n")
    full = [len(l) for l in lines if len(l) > 30]
    width = statistics.median(full) if full else 80

    # Compounds seen whole inside a line ("offshore-leak") keep their hyphen when split across lines.
    compounds = {c.lower() for c in re.findall(r"[^\W\d_]+(?:-[^\W\d_]+)+", " ".join(lines))}
    blocks, cur = [], ""

    def flush():
        nonlocal cur
        if cur:
            blocks.append(cur)
        cur = ""

    for line in lines:
        if not line:
            flush()
            continue
        if SECTION_WORDS.match(line):
            flush()
            blocks.append(line)
            continue
        if HEADING.match(line) and len(line.split()) <= 10 and len(line) < 0.8 * width and not cur.endswith("-"):
            flush()  # headings are layout, not prose
            continue
        if _is_noise(line):
            continue
        if re.match(r"^(?:[•\-–*]\s|(?:Figure|Table|Fig\.|Algorithm|Gambar|Tabel)\s+\d+[:.])", line):
            flush()
        if cur.endswith("-") and line[:1].islower():
            head, tail = cur.split()[-1], line.split()[0].rstrip(".,;:)")
            keep = (head + tail).lower() in compounds or "-" in head[:-1] or "-" in tail
            cur = (cur if keep else cur[:-1]) + line  # "juris-" + "dictionally" vs "offshore-" + "leak"
        else:
            cur = (cur + " " + line).strip()
        if len(line) < 0.8 * width and line[-1] in ".!?":
            flush()  # a short final line ends the paragraph
    flush()
    out = "\n\n".join(blocks)
    return re.sub(r"(?<=[a-z])\.(?=[A-Z][a-z])", ". ", out)  # run-in headings: "Model.We introduce"


def load(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"No such file: {path}")
    suffix = p.suffix.lower()
    if suffix == ".docx":
        try:
            import docx
        except ImportError:
            raise RuntimeError("Reading .docx needs python-docx: pip install python-docx")
        return "\n\n".join(par.text for par in docx.Document(str(p)).paragraphs)
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise RuntimeError("Reading .pdf needs pypdf: pip install pypdf")
        return tidy_pdf([(page.extract_text() or "") for page in PdfReader(str(p)).pages])
    if suffix in {".txt", ".md", ".tex", ".rst", ""}:
        return p.read_text(encoding="utf-8", errors="replace")
    raise RuntimeError(f"Unsupported file type '{suffix}'. Use .txt, .md, .docx or .pdf.")

# ============================== analyze ==============================
import re
import statistics
from collections import Counter


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
        if last in ABBREVIATIONS or (len(last) == 1 and last.isalpha() and m.group().startswith(".")):
            continue  # "et al. Smith", "e.g. X", initials
        sents.append(paragraph[start:m.end()].strip())
        start = m.end()
    tail = paragraph[start:].strip()
    if tail:
        sents.append(tail)
    return sents


def detect_language(words):
    low = [w.lower() for w in words]
    scores = {lang: sum(w in sw for w in low) for lang, sw in STOPWORDS.items()}
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
    for conj in COMMA_BEFORE.get(lang, []):
        total = len(re.findall(r"\s" + conj + r"\b", low))
        if total >= 3:
            comma_before[conj] = {"with_comma": len(re.findall(r",\s" + conj + r"\b", low)), "total": total}

    lists = re.findall(r"\w+, (?:[\w-]+ ){0,3}?[\w-]+(,)? (?:and|or|dan|atau|serta) \w", low)
    opener_yes = opener_no = 0
    for s in sents:
        sl = s.lower().lstrip("\"“‘(")
        for t in sorted(TRANSITIONS.get(lang, []), key=len, reverse=True):
            if t in NO_COMMA_OPENERS or not sl.startswith(t):
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
        "serial_comma": {"with_final_comma": sum(1 for g in lists if g),
                         "list_patterns_total": len(lists)},
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
    stop = STOPWORDS.get(lang, set())
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
    stop = STOPWORDS.get(lang, set())
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
    phrases, seen = [], set()
    for g, k in keep(grams[4], 3, 200):  # one entry per repeated passage, not every overlapping window
        w = g.split()
        ends = {" ".join(w[:3]), " ".join(w[1:])}
        if not ends & seen:
            phrases.append((g, k))
        seen |= ends
    return {"bigrams": keep(grams[2], 3, 30), "trigrams": keep(grams[3], 2, 20),
            "recurring_phrases": phrases[:15]}


def marker_features(text, sents, words, lang):
    low_text = text.lower()
    low = Counter(w.lower() for w in words)
    n = len(words)
    count_list = lambda items: sorted(((p, count_phrase(p, low_text)) for p in items),
                                      key=lambda kv: -kv[1])
    transitions = [(p, k) for p, k in count_list(TRANSITIONS.get(lang, [])) if k]
    hedges = [(p, k) for p, k in count_list(HEDGES.get(lang, [])) if k]
    boosters = [(p, k) for p, k in count_list(BOOSTERS.get(lang, [])) if k]
    fp = FIRST_PERSON.get(lang, {"singular": [], "plural": []})

    firsts = Counter()
    conj_open = trans_open = 0
    for s in sents:
        w = words_of(s)
        if not w:
            continue
        firsts[w[0].lower()] += 1
        conj_open += w[0].lower() in COORD_CONJ.get(lang, [])
        sl = s.lower().lstrip("\"“‘(")
        trans_open += any(re.match(re.escape(t) + r"\b", sl) for t in TRANSITIONS.get(lang, []))

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
        brit, amer = (len(re.findall(SPELLING[k], low_text)) for k in ("british", "american"))
        out["spelling"] = {"british_markers": brit, "american_markers": amer}
    elif lang == "id":
        out["passive_per_100_sentences"] = pct(len(re.findall(r"\bdi[a-z]{4,}(?:kan|i|nya)?\b", low_text)), len(sents))
    return out


def synonym_features(text, lang):
    """For each group of interchangeable words, which one does the author pick?"""
    out = {}
    for concept, variants in SYNONYM_SETS.get(lang, {}).items():
        work, counts = text.lower(), {}
        for name, pat in sorted(variants.items(), key=lambda kv: -len(kv[0])):
            rx = re.compile(r"(?<![\w-])(?:" + pat + r")(?![\w-])")
            counts[name] = len(rx.findall(work))
            work = rx.sub(" _ ", work)  # so "akan tetapi" is not also counted as "tetapi"
        if sum(counts.values()) >= 2:
            out[concept] = dict(sorted(counts.items(), key=lambda kv: -kv[1]))
    return out


def pick_excerpts(paras, mean_len, max_excerpts=8, max_words=1100):
    """Representative paragraphs, spread across the text, used as few-shot samples."""
    cands = []
    for i, p in enumerate(paras):
        n = len(words_of(p))
        whole = p[0].isupper() and p[-1] in ".!?" and not re.match(r"(?:Figure|Table|Fig\.|Gambar|Tabel)\s+\d", p)
        if 40 <= n <= 200 and whole:
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

# ============================== guide ==============================

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

# ============================== llm ==============================
import os


MODEL = os.environ.get("STYLE_AGENT_MODEL", "claude-opus-5-5")


class LLMError(RuntimeError):
    pass


def complete(system, user, effort="high"):
    try:
        import anthropic
    except ImportError:
        raise LLMError("This command needs the Anthropic SDK: pip install anthropic")
    request = dict(
        model=MODEL,
        max_tokens=64000,
        thinking={"type": "adaptive"},
        output_config={"effort": effort},
        # The style profile is identical on every call, so cache it.
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    try:
        client = anthropic.Anthropic()
        try:
            # If the model declines a request, the API retries it on a fallback model.
            with client.beta.messages.stream(betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                                             **request) as stream:
                message = stream.get_final_message()
        except TypeError as e:
            if "unexpected keyword" not in str(e):
                raise
            with client.messages.stream(**request) as stream:  # older SDK without the fallbacks parameter
                message = stream.get_final_message()
    except anthropic.AuthenticationError:
        raise LLMError("The Claude API rejected the API key. Check ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        raise LLMError("Rate limited by the Claude API. Wait a moment and try again.")
    except anthropic.APIStatusError as e:
        raise LLMError(f"Claude API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        raise LLMError("Could not reach the Claude API. Check your internet connection.")
    except TypeError as e:
        if "authentication" not in str(e):
            raise LLMError(f"The installed anthropic package is too old ({e}). Run: pip install -U anthropic")
        raise LLMError("No Claude API key found. In PowerShell run:  setx ANTHROPIC_API_KEY \"your-key\"  "
                       "then open a new terminal (macOS/Linux: export ANTHROPIC_API_KEY=your-key). "
                       "Without a key, `rewrite --print-prompt` gives a prompt you can paste into any model.")
    if message.stop_reason == "refusal":
        raise LLMError("The model declined this request.")
    text = "".join(b.text for b in message.content if b.type == "text").strip()
    if message.stop_reason == "max_tokens":
        raise LLMError("The response was cut off at the output limit. Try a shorter input.")
    return text


def _samples(profile):
    return "\n\n".join(f"<sample>\n{p}\n</sample>" for p in profile.get("excerpts", []))


def rewrite_system(profile):
    return f"""You rewrite text so that it reads as if one specific author wrote it. Below is a measured \
profile of how this author writes, followed by untouched samples of their writing. The profile was \
computed from their own documents, so treat its numbers as facts about their habits.

The goal is that the author could read your output and take it for their own draft. That means matching \
their habits as they are, including the plain or imperfect ones: their sentence lengths, how often and \
where they put commas, which punctuation marks and symbols they use and which they never use, their \
connectors, their preferred word among synonyms, their level of vocabulary, their degree of hedging, and \
their use of first person and passive voice. Do not polish the text beyond their level or make it more \
elegant than their samples. Where the profile says a mark or word is never used, do not use it. Reach \
first for words and phrasings the profile shows they actually use.

Keep the meaning exactly. Every claim, number, name, technical term, citation and piece of formatting \
(headings, lists, code, equations) in the input must survive, and nothing new may be added. The samples \
show manner only; never carry their subject matter into the output. Write in the same language as the \
input text.

Reply with the rewritten text only, with no preface, explanation or quotation marks around it.

<style_profile>
{render(profile)}
</style_profile>

<author_samples>
{_samples(profile)}
</author_samples>"""


def rewrite_user(text, note=None):
    msg = f"Rewrite this in the author's voice.\n\n<text>\n{text}\n</text>"
    if note:
        msg += f"\n\nAdditional instruction from the author: {note}"
    return msg


def rewrite(profile, text, note=None, max_revisions=1):
    """Rewrite `text`, then check the result against the profile's hard rules and
    ask for a correction if it used a mark the author never uses."""
    system = rewrite_system(profile)
    result = complete(system, rewrite_user(text, note))
    for _ in range(max_revisions):
        broken = violations(profile, result)
        if not broken:
            break
        result = complete(system, (
            "This draft is already in the author's voice, but it uses things the author never uses: "
            f"{', '.join(broken)}. Rework only the affected sentences so they no longer appear, the way "
            "the author would have phrased them, and return the full corrected text.\n\n"
            f"<text>\n{result}\n</text>"))
    return result


def suggest_system(profile):
    return f"""You help an author find words and phrasings that sound like them. Below is a measured \
profile of how they write and samples of their writing.

The author will describe a meaning, or give a sentence with a gap or a word they want to replace. Offer \
five to eight options they would plausibly have written themselves, most characteristic first. Prefer \
words the profile shows they already use, stay at their vocabulary level, and respect their punctuation \
habits. For each option give the word or phrase, then one short example sentence in their voice. Write \
in the language of the request.

<style_profile>
{render(profile)}
</style_profile>

<author_samples>
{_samples(profile)}
</author_samples>"""


def suggest(profile, request):
    return complete(suggest_system(profile), request, effort="medium")


DEEP_SYSTEM = """You are a stylistics analyst. You will receive an author's writing and a statistical \
profile already computed from it. Describe what the numbers cannot capture, so that someone imitating \
this author gets the manner right.

Cover: tone and register; how they introduce, define and describe things; how they build an argument \
or explanation across a paragraph; characteristic sentence constructions; word-choice tendencies \
(concrete or abstract, plain or ornate, favourite verbs and qualifiers); recurring quirks, including \
grammar or usage slips that are part of their voice and should be kept; an estimated proficiency level \
(CEFR) with one line of reasoning; and what typical AI-written prose does that this author does not.

Write it as direct guidance to an imitator, in at most 450 words, as a plain list of points. Quote \
short phrases from the text as evidence. Do not repeat the statistics."""


def deep_analysis(profile, corpus_text):
    return complete(DEEP_SYSTEM, f"<statistical_profile>\n{render(profile)}\n</statistical_profile>\n\n"
                                 f"<author_text>\n{corpus_text}\n</author_text>")

# ============================== cli ==============================
import argparse
import hashlib
import json
import sys
from pathlib import Path



def _paths(data_dir):
    root = Path(data_dir)
    return root, root / "corpus", root / "profile.json"


def load_profile(data_dir):
    _, _, pfile = _paths(data_dir)
    if not pfile.exists():
        sys.exit("No style profile yet. Teach it first:  python mystyle.py learn <your-paper>")
    return json.loads(pfile.read_text(encoding="utf-8"))


def read_input(args):
    if getattr(args, "file", None):
        return load(args.file)
    if args.text:
        return " ".join(args.text)
    if sys.stdin.isatty():
        print("Paste the text, then press Ctrl-D (Ctrl-Z then Enter on Windows):", file=sys.stderr)
    return sys.stdin.read()


def print_checks(profile, text):
    broken = violations(profile, text)
    notes = drift(profile, text)
    if broken:
        print("Uses things you never use: " + ", ".join(broken), file=sys.stderr)
    for n in notes:
        print("Differs from your style - " + n, file=sys.stderr)
    return broken, notes


# ------------------------------------------------------------------- commands

def cmd_learn(args):
    root, corpus, pfile = _paths(args.data)
    if args.reset and corpus.exists():
        for f in corpus.glob("*.txt"):
            f.unlink()
    corpus.mkdir(parents=True, exist_ok=True)
    for path in args.files:
        path = path.strip().strip("\"'")
        text = load(path)
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]  # same document twice = stored once
        (corpus / f"{Path(path).stem}-{digest}.txt").write_text(text, encoding="utf-8")
        print(f"Read {path} ({len(words_of(text)):,} words)")
    docs = [f.read_text(encoding="utf-8") for f in sorted(corpus.glob("*.txt"))]
    if not docs:
        sys.exit("Nothing to learn from. Pass at least one document.")
    # Each document is cleaned on its own (so its reference list is dropped), then pooled.
    pooled = "\n\n".join(clean(d) for d in docs)
    profile = analyze(pooled)
    profile["documents"] = len(docs)
    if args.deep:
        print("Running deep analysis with Claude...")
        profile["qualitative"] = deep_analysis(profile, pooled)
    elif pfile.exists() and not args.reset:
        old = json.loads(pfile.read_text(encoding="utf-8"))
        if old.get("qualitative"):
            profile["qualitative"] = old["qualitative"]
    pfile.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    words = profile["lexical"]["total_words"]
    print(f"Profile saved to {pfile} ({profile['documents']} document(s), {words:,} words of prose).")
    if words < 1500:
        print("Note: under 1,500 words is a thin sample. Add more of your writing for a sharper profile.")
    print("See it with:  python mystyle.py report")


def cmd_report(args):
    profile = load_profile(args.data)
    print(json.dumps(profile, ensure_ascii=False, indent=2) if args.json else render(profile))


def cmd_rewrite(args):
    profile = load_profile(args.data)
    text = read_input(args).strip()
    if not text:
        sys.exit("No text given.")
    if args.print_prompt:
        print(rewrite_system(profile) + "\n\n-----\n\n" + rewrite_user(text, args.note))
        return
    result = rewrite(profile, text, args.note)
    if args.output:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(result)
    print_checks(profile, result)


def cmd_suggest(args):
    profile = load_profile(args.data)
    print(suggest(profile, " ".join(args.request)))


def cmd_check(args):
    profile = load_profile(args.data)
    text = read_input(args).strip()
    broken, notes = print_checks(profile, text)
    if not broken and not notes:
        short = len(words_of(text)) < 60
        print("No hard-rule breaks." + (" (Text is too short to compare rhythm and vocabulary.)" if short
                                        else " Rhythm, commas and vocabulary are within your usual range."))


def cmd_chat(args):
    profile = load_profile(args.data)
    print("Paste a sentence or paragraph and press Enter to get it in your wording.\n"
          "Start a line with '?' to ask for word suggestions. Empty line or Ctrl-D to quit.")
    while True:
        try:
            line = input("\n> ").strip()
        except EOFError:
            break
        if not line:
            break
        try:
            if line.startswith("?"):
                print(suggest(profile, line[1:].strip()))
            else:
                result = rewrite(profile, line)
                print(result)
                print_checks(profile, result)
        except LLMError as e:
            print(f"Error: {e}", file=sys.stderr)


def interactive(data_dir):
    """No arguments (e.g. the Run button in an editor): set up if needed, then chat."""
    _, _, pfile = _paths(data_dir)
    if not pfile.exists():
        print("No style profile yet. Give me a document you wrote (.pdf, .docx, .txt, .md).")
        path = input("Path to your document (you can drag the file into this window): ").strip().strip("\"'& ")
        cmd_learn(argparse.Namespace(data=data_dir, files=[path], deep=False, reset=False))
        print()
    cmd_chat(argparse.Namespace(data=data_dir))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mystyle.py",
                                 description="Learns how you write and rewrites other text in your wording.")
    ap.add_argument("--data", default=str(Path(__file__).resolve().parent / "style_agent_data"), help="where the profile is stored (default: %(default)s)")
    sub = ap.add_subparsers(dest="command")

    p = sub.add_parser("learn", help="analyze your document(s) and build/update the style profile")
    p.add_argument("files", nargs="*", help=".txt, .md, .docx or .pdf")
    p.add_argument("--deep", action="store_true", help="also add a qualitative reading by Claude (needs API key)")
    p.add_argument("--reset", action="store_true", help="forget previously learned documents first")
    p.set_defaults(func=cmd_learn)

    p = sub.add_parser("report", help="show your style profile")
    p.add_argument("--json", action="store_true", help="raw numbers instead of the readable guide")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("rewrite", help="rewrite text into your wording")
    p.add_argument("text", nargs="*")
    p.add_argument("-f", "--file", help="read the text from a file")
    p.add_argument("-o", "--output", help="write the result to a file")
    p.add_argument("--note", help="extra instruction, e.g. 'keep it under 100 words'")
    p.add_argument("--print-prompt", action="store_true",
                   help="print the full prompt instead of calling the API (paste it into any model)")
    p.set_defaults(func=cmd_rewrite)

    p = sub.add_parser("suggest", help="get words/phrasings you would use for a meaning")
    p.add_argument("request", nargs="+")
    p.set_defaults(func=cmd_suggest)

    p = sub.add_parser("check", help="offline: how far is a text from your style?")
    p.add_argument("text", nargs="*")
    p.add_argument("-f", "--file")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("chat", help="interactive: paste sentences, get them back in your wording")
    p.set_defaults(func=cmd_chat)

    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # never crash on a console that cannot show a character
        stream.reconfigure(errors="replace")
    try:
        if args.command is None:
            interactive(args.data)
        else:
            args.func(args)
    except (FileNotFoundError, RuntimeError, ValueError) as e:  # LLMError is a RuntimeError
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
