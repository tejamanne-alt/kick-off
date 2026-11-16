# A prompt as it is pasted into a chat: the document wraps its lines at 120 characters, and a copy that kept those wraps
# broke sentences in the middle (docs/LEARNINGS.md A18). Used by every prompts page's generator.
import re

HEADING = re.compile(r"^[A-Z][A-Z ,'-]{2,}(\(.*)?$")      # THE PLANT, LEAVES (a LEAVES picture: ...)
ITEM = re.compile(r'^\s*(- |\d+\. )')                       # - a list item, 1. a step, with its indent


def unwrapped(text):
    """text with its wrapped lines joined: paragraphs, headings (an all-capitals line that opens a paragraph) and list
    items (and their indent) kept on lines of their own. Only line breaks change: the words are checked to be the same."""
    out, heads = [], set()
    for line in text.split('\n'):
        t = line.strip()
        prev = out[-1] if out else ''
        if t and prev and not ITEM.match(line) and len(out) - 1 not in heads:
            out[-1] = prev + ' ' + t
            continue
        if t and HEADING.match(t) and not prev:
            heads.add(len(out))
        out.append(line.rstrip() if ITEM.match(line) else t)
    flat = '\n'.join(out)
    if flat.split() != text.split():
        raise ValueError('unwrapped() changed the words of a prompt: ' + text[:60])
    return flat
