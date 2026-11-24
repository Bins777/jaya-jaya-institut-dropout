import unittest
from unittest import mock

from style_agent import analyze, extract, guide, llm

PARAS = [
    "Student dropout is an important problem for many institutions, because it affects both the reputation "
    "of the school and the future of the students. In this paper, we use a machine learning approach to "
    "predict dropout as early as possible. However, the data that we have is not balanced, so we need to "
    "handle this issue before the training process.",
    "The dataset consists of 4,424 records and 36 features, such as age, gender, tuition status, and grades. "
    "First, we clean the data and remove the features that are not relevant. Then, we use a random forest "
    "model, because it is simple and it shows good results in previous studies (Breiman, 2001). The result "
    "shows that the model reaches 88% accuracy, which is better than the baseline [3].",
    "However, this study also has some limitations. We only use the data from one institution, so the result "
    "may not apply to other places. Therefore, future work should collect more data and use other methods.",
]
TEXT = "1. Introduction\n\n" + "\n\n".join(PARAS * 6) + "\n\nReferences\n\nBreiman, L. (2001). Random forests; a study.\n"


class AnalyzeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = analyze.analyze(TEXT)

    def test_language_and_counts(self):
        self.assertEqual(self.p["language"], "en")
        self.assertEqual(self.p["sentences"]["count"], 10 * 6)
        self.assertEqual(self.p["citations"], {"author_year_parenthetical": 6, "numeric_bracket": 6})

    def test_references_and_citations_do_not_count_as_punctuation(self):
        counts = self.p["punctuation"]["counts"]
        self.assertEqual(counts["semicolon"], 0)   # only in the reference list
        self.assertEqual(counts["parentheses"], 0)  # only around a citation
        self.assertEqual(counts["percent_sign"], 6)

    def test_comma_habits(self):
        pun = self.p["punctuation"]
        self.assertEqual(pun["comma_after_opening_connector"], {"with_comma": 30, "without_comma": 0})
        self.assertEqual(pun["comma_before_conjunction"]["because"], {"with_comma": 12, "total": 12})

    def test_word_preferences(self):
        use = self.p["word_preferences"]["use"]
        self.assertEqual(use["use"], 24)
        self.assertEqual(use["utilize"], 0)

    def test_abbreviations_do_not_split_sentences(self):
        self.assertEqual(len(analyze.sentences_of("Smith et al. Found it, e.g. The result. It works.")), 2)

    def test_indonesian(self):
        text = ("Penelitian ini menggunakan data dari satu institusi, sehingga hasilnya belum tentu berlaku "
                "untuk tempat lain. Namun, model yang digunakan dapat membantu staf untuk menemukan siswa "
                "yang membutuhkan bantuan. Selain itu, sistem ini mudah digunakan karena staf hanya perlu "
                "mengisi formulir. ") * 3
        p = analyze.analyze(text)
        self.assertEqual(p["language"], "id")
        self.assertEqual(p["word_preferences"]["kontras"]["namun"], 3)

    def test_violations_and_guide(self):
        self.assertEqual(analyze.violations(self.p, "Fine, plain text (Smith, 2020)."), [])
        found = analyze.violations(self.p, "The results — robust; it's great!")
        for label in ("em dashes (—)", "semicolons", "exclamation marks", "contractions"):
            self.assertIn(label, found)
        text = guide.render(self.p)
        self.assertIn("NEVER used", text)
        self.assertIn("“use” 24×", text)

    def test_rewrite_revises_when_a_never_used_mark_appears(self):
        replies = iter(["A result — with a dash.", "A result, with a comma."])
        with mock.patch.object(llm, "complete", side_effect=lambda *a, **k: next(replies)) as m:
            self.assertEqual(llm.rewrite(self.p, "x"), "A result, with a comma.")
        self.assertEqual(m.call_count, 2)
        self.assertIn("em dashes", m.call_args_list[1].args[1])

    def test_provider_choice(self):
        keys = ("STYLE_AGENT_PROVIDER", "GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
        clean = {k: "" for k in keys}
        with mock.patch.dict("os.environ", clean):
            self.assertEqual(llm.provider(), "claude")
        with mock.patch.dict("os.environ", {**clean, "GEMINI_API_KEY": "x"}):
            self.assertEqual(llm.provider(), "gemini")
        with mock.patch.dict("os.environ", {**clean, "GEMINI_API_KEY": "x", "ANTHROPIC_API_KEY": "y"}):
            self.assertEqual(llm.provider(), "claude")
        with mock.patch.dict("os.environ", {**clean, "ANTHROPIC_API_KEY": "y", "STYLE_AGENT_PROVIDER": "gemini"}):
            self.assertEqual(llm.provider(), "gemini")


class PdfTidyTest(unittest.TestCase):
    def test_rebuilds_paragraphs_from_wrapped_pages(self):
        body = ["We build a graph from offshore-leak records and the registry, and",
                "we treat membership as a proxy for offshore structuring, a juris-",
                "dictionally restricted signal taken from the same offshore-",
                "leak records as before.",
                "0.91 0.88 0.93 12.5 3",
                "2 Related Work",
                "Method.The idea that ownership structure betrays wrongdoing is not",
                "new."]
        head = "My Paper Title, Conference 2026"
        pages = ["\n".join([head] + body + ["1"]), head + "\nSecond page text ends here.\n2",
                 head + "\nThird page text ends here.\n3"]
        blocks = extract.tidy_pdf(pages).split("\n\n")
        self.assertEqual(len(blocks), 4)  # header, page numbers, table row and heading are gone
        self.assertEqual(blocks[0], "We build a graph from offshore-leak records and the registry, and we treat "
                         "membership as a proxy for offshore structuring, a jurisdictionally restricted signal "
                         "taken from the same offshore-leak records as before.")
        self.assertEqual(blocks[1], "Method. The idea that ownership structure betrays wrongdoing is not new.")


if __name__ == "__main__":
    unittest.main()
