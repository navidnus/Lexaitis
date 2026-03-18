"""
Text library for Lexaitis.

Each entry in BUNDLED_TEXTS maps a display name to metadata about where the
source file lives and how to strip boilerplate from it.
"""

from __future__ import annotations

import pathlib
import re

_HERE = pathlib.Path(__file__).parent

# ---------------------------------------------------------------------------
# Gutenberg boilerplate stripping
# ---------------------------------------------------------------------------

_GUTENBERG_START_RE = re.compile(
    r"\*{3}\s*START OF THE PROJECT GUTENBERG EBOOK[^\n]*\n",
    re.IGNORECASE,
)
_GUTENBERG_END_RE = re.compile(
    r"\*{3}\s*END OF THE PROJECT GUTENBERG EBOOK[^\n]*",
    re.IGNORECASE,
)


def _strip_gutenberg(text: str) -> str:
    """Remove Project Gutenberg header/footer boilerplate."""
    m = _GUTENBERG_START_RE.search(text)
    if m:
        text = text[m.end():]
    m = _GUTENBERG_END_RE.search(text)
    if m:
        text = text[: m.start()]
    return text.strip()


# ---------------------------------------------------------------------------
# Text registry
# ---------------------------------------------------------------------------

#  display_name -> {file, gutenberg, description}
BUNDLED_TEXTS: dict[str, dict] = {
    "Alice in Wonderland — Lewis Carroll": {
        "file": "alice_in_wonderland.txt",
        "gutenberg": True,
        "description": (
            "Carroll's classic fantasy novel (~27 k tokens). "
            "Relatively small vocabulary; good for exploring low n with "
            "vivid, varied output."
        ),
    },
    "Pride and Prejudice — Jane Austen": {
        "file": "pride_and_prejudice.txt",
        "gutenberg": True,
        "description": (
            "Austen's novel of manners (~120 k tokens, first 30 k used). "
            "Long, complex sentences — try high n to see repetition emerge."
        ),
    },
    "Moby-Dick — Herman Melville": {
        "file": "moby_dick.txt",
        "gutenberg": True,
        "description": (
            "Melville's epic (~210 k tokens, first 30 k used). "
            "Rich nautical and philosophical vocabulary."
        ),
    },
    "Hamlet — William Shakespeare": {
        "file": "hamlet.txt",
        "gutenberg": True,
        "description": (
            "Shakespeare's tragedy in verse and prose (~30 k tokens). "
            "Poetic metre makes n-gram patterns especially striking."
        ),
    },
    "Gettysburg Address — Abraham Lincoln": {
        "file": "gettysburg_address.txt",
        "gutenberg": False,
        "description": (
            "Lincoln's 272-word address (1863). "
            "Very short — high n will reproduce the text almost verbatim; "
            "useful for demonstrating sparsity."
        ),
    },
    "Declaration of Independence": {
        "file": "declaration_of_independence.txt",
        "gutenberg": False,
        "description": (
            "The 1776 founding document (~1,300 words). "
            "Formal eighteenth-century prose with long parallel constructions."
        ),
    },
}

CUSTOM_LABEL = "Custom text (paste below)"


def load_text(display_name: str) -> str:
    """Load and return the cleaned text for *display_name*."""
    if display_name not in BUNDLED_TEXTS:
        raise KeyError(f"Unknown text: {display_name!r}")

    meta = BUNDLED_TEXTS[display_name]
    path = _HERE / meta["file"]
    raw = path.read_text(encoding="utf-8", errors="ignore")

    if meta["gutenberg"]:
        raw = _strip_gutenberg(raw)

    return raw


def all_display_names() -> list[str]:
    return list(BUNDLED_TEXTS.keys())


def description_for(display_name: str) -> str:
    return BUNDLED_TEXTS.get(display_name, {}).get("description", "")
