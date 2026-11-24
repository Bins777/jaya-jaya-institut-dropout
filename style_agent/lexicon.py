"""Word lists used by the analyzer. English and Indonesian are supported;
other languages still get the language-independent measurements."""

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

SPELLING = {  # British vs American markers
    "british": r"\b\w+(?:isation|ised|ising|ise|yse|ysed)\b|\b(?:colour|behaviour|favour|labour|centre|programme|analyse|modelling|labelled)\w*\b",
    "american": r"\b\w+(?:ization|ized|izing|ize|yze|yzed)\b|\b(?:color|behavior|favor|labor|center|analyze|modeling|labeled)\w*\b",
}
