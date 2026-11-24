"""Load a document (.txt, .md, .tex, .docx, .pdf) as plain text."""
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
