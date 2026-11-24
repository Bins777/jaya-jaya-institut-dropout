"""Bundle the style_agent package into one file, mystyle.py, that runs on its own.

    python build_mystyle.py
"""
import re
from pathlib import Path

SRC = Path(__file__).parent / "style_agent"
ORDER = ["lexicon", "extract", "analyze", "guide", "llm", "cli"]
PREFIXES = r"\b(?:lx|extract|guide|llm|analyze)\.(?=[A-Za-z_])"

HEADER = '''"""mystyle.py - learns how you write, then rewrites other text in your wording.

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
'''

parts = [HEADER]
for name in ORDER:
    src = (SRC / f"{name}.py").read_text(encoding="utf-8")
    src = re.sub(r'\A"""(.*?)"""\n', "", src, flags=re.S)                     # module docstring
    src = re.sub(r"^[ \t]*from \.\S* import .*\n", "", src, flags=re.M)        # package-internal imports
    src = re.sub(PREFIXES, "", src)                                           # lx.STOPWORDS -> STOPWORDS
    if name == "cli":
        src = src.replace('default="style_agent_data"', 'default=str(Path(__file__).resolve().parent / "style_agent_data")')
        src = src.replace('prog="style_agent"', 'prog="mystyle.py"').replace("python -m style_agent", "python mystyle.py")
    parts.append(f"\n# {'=' * 30} {name} {'=' * 30}\n" + src)

out = Path(__file__).parent / "mystyle.py"
out.write_text("".join(parts), encoding="utf-8")
print(f"Wrote {out} ({len(out.read_text(encoding='utf-8').splitlines())} lines)")
