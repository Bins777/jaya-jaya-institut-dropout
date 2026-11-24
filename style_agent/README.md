# Style agent

Learns how you write from your own documents, then rewrites other text (for
example something an AI wrote) into your wording, punctuation and level.

## How it works

1. **Learn (offline).** `analyze.py` reads your document and measures it. Nothing
   leaves your computer in this step.
   - **Word choice:** your most used words, habitual word pairings, recurring
     phrasings, connectors, and which word you pick among alternatives with the
     same meaning (*use* vs *utilize*, *however* vs *but*, *namun* vs *tetapi*).
   - **Sentences:** length (average, range, short/medium/long mix), paragraph
     size, how you open sentences.
   - **Punctuation and symbols:** commas per sentence, whether you put a comma
     before *and/but/because/which* and after *However/Therefore*, list commas,
     semicolons, colons, parentheses, dashes of every kind, quotes, slashes,
     `%` vs "percent", digits vs spelled-out numbers, and the marks you never use.
   - **Voice and level:** first person, passive voice, contractions, hedging,
     emphasis, British/American spelling, vocabulary richness, readability
     (LIX for any language, Flesch-Kincaid for English).
   - Reference lists and citations such as `(Smith, 2020)` or `[3]` are set
     aside so they do not distort the punctuation numbers.
2. **Profile.** The measurements and a few representative paragraphs of yours
   are saved to `style_agent_data/profile.json`. `guide.py` renders them as a
   readable style guide. Learning more documents later pools them all.
3. **Rewrite (Claude API).** `llm.py` gives the model your style guide and
   sample paragraphs and asks it to rewrite the text in your voice while keeping
   the meaning, numbers, terms and citations exactly.
4. **Check (offline).** The result is measured the same way. If it uses a mark
   you never use (for instance an em dash), it is sent back once for correction.
   Remaining differences in rhythm, commas or vocabulary are reported.

English and Indonesian are recognised automatically. Other languages still get
all the language-independent measurements.

## Use

The quickest way is the single file `mystyle.py` in the repository root (built
from this package by `build_mystyle.py`). Run it with no arguments, or with the
Run button in VS Code, and it asks for your document and then lets you paste text:

```powershell
pip install -U anthropic pypdf python-docx
setx ANTHROPIC_API_KEY "your-key"      # then open a new terminal
python mystyle.py
```

To use Gemini instead of Claude, install `google-genai` and set `GEMINI_API_KEY`
instead of `ANTHROPIC_API_KEY`. With both keys set, Claude is used unless
`STYLE_AGENT_PROVIDER=gemini`. The Gemini model is `gemini-flash-latest`; change
it with `STYLE_AGENT_GEMINI_MODEL`.

The package form takes the same commands:

```bash
pip install anthropic python-docx pypdf     # only anthropic is needed for rewriting
export ANTHROPIC_API_KEY=...                # not needed for learn / report / check

python -m style_agent learn my_paper.docx            # .txt .md .docx .pdf, one or many
python -m style_agent learn my_paper.docx --deep     # also add Claude's qualitative reading
python -m style_agent report                         # your style guide

python -m style_agent rewrite "Text that Claude wrote..."
python -m style_agent rewrite -f draft.txt -o draft_mine.txt
python -m style_agent suggest "a word for 'very important' in a conclusion"
python -m style_agent check -f draft.txt             # offline: how far is this from my style?
python -m style_agent chat                           # paste sentences, get them back in your wording
```

No API key? `rewrite --print-prompt "..."` prints the complete prompt (your
style guide, samples and the text) to paste into any model.

`--deep` sends the full text of your documents to the Claude API; plain `learn`
does not. `rewrite`, `suggest` and `chat` send the style guide and the stored
sample paragraphs. The model is `claude-opus-5-5`; set `STYLE_AGENT_MODEL` to
change it.

`style_agent_data/` holds a copy of your documents and is git-ignored.

## Tests

```bash
python -m unittest discover -s tests
```
