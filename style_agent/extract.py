"""Load a document (.txt, .md, .tex, .docx, .pdf) as plain text."""
from pathlib import Path


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
        return "\n\n".join((page.extract_text() or "") for page in PdfReader(str(p)).pages)
    if suffix in {".txt", ".md", ".tex", ".rst", ""}:
        return p.read_text(encoding="utf-8", errors="replace")
    raise RuntimeError(f"Unsupported file type '{suffix}'. Use .txt, .md, .docx or .pdf.")
