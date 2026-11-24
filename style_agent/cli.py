"""Command line for the style agent. Run `python -m style_agent --help`."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from . import analyze, extract, guide


def _paths(data_dir):
    root = Path(data_dir)
    return root, root / "corpus", root / "profile.json"


def load_profile(data_dir):
    _, _, pfile = _paths(data_dir)
    if not pfile.exists():
        sys.exit("No style profile yet. Teach it first:  python -m style_agent learn <your-paper>")
    return json.loads(pfile.read_text(encoding="utf-8"))


def read_input(args):
    if getattr(args, "file", None):
        return extract.load(args.file)
    if args.text:
        return " ".join(args.text)
    if sys.stdin.isatty():
        print("Paste the text, then press Ctrl-D (Ctrl-Z then Enter on Windows):", file=sys.stderr)
    return sys.stdin.read()


def print_checks(profile, text):
    broken = analyze.violations(profile, text)
    notes = analyze.drift(profile, text)
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
        text = extract.load(path)
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]  # same document twice = stored once
        (corpus / f"{Path(path).stem}-{digest}.txt").write_text(text, encoding="utf-8")
        print(f"Read {path} ({len(analyze.words_of(text)):,} words)")
    docs = [f.read_text(encoding="utf-8") for f in sorted(corpus.glob("*.txt"))]
    if not docs:
        sys.exit("Nothing to learn from. Pass at least one document.")
    # Each document is cleaned on its own (so its reference list is dropped), then pooled.
    pooled = "\n\n".join(analyze.clean(d) for d in docs)
    profile = analyze.analyze(pooled)
    profile["documents"] = len(docs)
    if args.deep:
        from . import llm
        print("Running deep analysis with Claude...")
        profile["qualitative"] = llm.deep_analysis(profile, pooled)
    elif pfile.exists() and not args.reset:
        old = json.loads(pfile.read_text(encoding="utf-8"))
        if old.get("qualitative"):
            profile["qualitative"] = old["qualitative"]
    pfile.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    words = profile["lexical"]["total_words"]
    print(f"Profile saved to {pfile} ({profile['documents']} document(s), {words:,} words of prose).")
    if words < 1500:
        print("Note: under 1,500 words is a thin sample. Add more of your writing for a sharper profile.")
    print("See it with:  python -m style_agent report")


def cmd_report(args):
    profile = load_profile(args.data)
    print(json.dumps(profile, ensure_ascii=False, indent=2) if args.json else guide.render(profile))


def cmd_rewrite(args):
    from . import llm
    profile = load_profile(args.data)
    text = read_input(args).strip()
    if not text:
        sys.exit("No text given.")
    if args.print_prompt:
        print(llm.rewrite_system(profile) + "\n\n-----\n\n" + llm.rewrite_user(text, args.note))
        return
    result = llm.rewrite(profile, text, args.note)
    if args.output:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(result)
    print_checks(profile, result)


def cmd_suggest(args):
    from . import llm
    profile = load_profile(args.data)
    print(llm.suggest(profile, " ".join(args.request)))


def cmd_check(args):
    profile = load_profile(args.data)
    text = read_input(args).strip()
    broken, notes = print_checks(profile, text)
    if not broken and not notes:
        short = len(analyze.words_of(text)) < 60
        print("No hard-rule breaks." + (" (Text is too short to compare rhythm and vocabulary.)" if short
                                        else " Rhythm, commas and vocabulary are within your usual range."))


def cmd_chat(args):
    from . import llm
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
                print(llm.suggest(profile, line[1:].strip()))
            else:
                result = llm.rewrite(profile, line)
                print(result)
                print_checks(profile, result)
        except llm.LLMError as e:
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
    ap = argparse.ArgumentParser(prog="style_agent",
                                 description="Learns how you write and rewrites other text in your wording.")
    ap.add_argument("--data", default="style_agent_data", help="where the profile is stored (default: %(default)s)")
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
