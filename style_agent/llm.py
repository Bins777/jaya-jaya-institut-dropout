"""The generation half: rewrite text into the author's voice, suggest words, and
(optionally) add a qualitative reading of the style. Uses the Claude API.

Prompts are built by pure functions, so `--print-prompt` works with no API key
and the prompt can be pasted into any other model.
"""
import os

from . import analyze, guide

MODEL = os.environ.get("STYLE_AGENT_MODEL", "claude-opus-5-5")


class LLMError(RuntimeError):
    pass


def complete(system, user, effort="high"):
    try:
        import anthropic
    except ImportError:
        raise LLMError("This command needs the Anthropic SDK: pip install anthropic")
    try:
        client = anthropic.Anthropic()
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=64000,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            # If the model declines a request, the API retries it on a fallback model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            # The style profile is identical on every call, so cache it.
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        ) as stream:
            message = stream.get_final_message()
    except anthropic.AuthenticationError:
        raise LLMError("No valid Claude credentials. Set ANTHROPIC_API_KEY (or run `ant auth login`).")
    except anthropic.RateLimitError:
        raise LLMError("Rate limited by the Claude API. Wait a moment and try again.")
    except anthropic.APIStatusError as e:
        raise LLMError(f"Claude API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        raise LLMError("Could not reach the Claude API. Check your internet connection.")
    except TypeError:  # no credentials at all surfaces as a TypeError in the SDK
        raise LLMError("No Claude credentials found. Set ANTHROPIC_API_KEY (or run `ant auth login`), "
                       "or use `rewrite --print-prompt` to get a prompt you can paste into any model.")
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
{guide.render(profile)}
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
        broken = analyze.violations(profile, result)
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
{guide.render(profile)}
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
    return complete(DEEP_SYSTEM, f"<statistical_profile>\n{guide.render(profile)}\n</statistical_profile>\n\n"
                                 f"<author_text>\n{corpus_text}\n</author_text>")
