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

#  display_name -> {file, gutenberg, category, description}
BUNDLED_TEXTS: dict[str, dict] = {

    # ── Fiction ──────────────────────────────────────────────────────────────

    "Alice in Wonderland — Lewis Carroll": {
        "file": "alice_in_wonderland.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Carroll's classic fantasy novel (~27 k tokens). "
            "Relatively small vocabulary; good for exploring low n."
        ),
    },
    "Pride and Prejudice — Jane Austen": {
        "file": "pride_and_prejudice.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Austen's novel of manners (~120 k tokens). "
            "Long, complex sentences — try high n to see repetition emerge."
        ),
    },
    "Moby-Dick — Herman Melville": {
        "file": "moby_dick.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Melville's epic (~210 k tokens). "
            "Rich nautical and philosophical vocabulary."
        ),
    },
    "Jane Eyre — Charlotte Brontë": {
        "file": "jane_eyre.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Brontë's gothic romance (~190 k tokens). "
            "Intimate first-person narration."
        ),
    },
    "Great Expectations — Charles Dickens": {
        "file": "great_expectations.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Dickens's coming-of-age novel (~190 k tokens). "
            "Vivid characterisation; varied sentence rhythm."
        ),
    },
    "A Tale of Two Cities — Charles Dickens": {
        "file": "tale_of_two_cities.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Dickens's historical novel (~140 k tokens). "
            "Famous for its rhetorical, parallel sentence structures."
        ),
    },
    "Adventures of Huckleberry Finn — Mark Twain": {
        "file": "huckleberry_finn.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Twain's vernacular masterpiece (~120 k tokens). "
            "Colloquial American English — very different from Victorian prose."
        ),
    },
    "The Adventures of Tom Sawyer — Mark Twain": {
        "file": "tom_sawyer.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Twain's boyhood adventure (~75 k tokens). "
            "Lively dialogue and American regional speech."
        ),
    },
    "The Picture of Dorian Gray — Oscar Wilde": {
        "file": "dorian_gray.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Wilde's aesthetic novel (~80 k tokens). "
            "Witty, aphoristic prose; distinctive epigrams."
        ),
    },
    "Frankenstein — Mary Shelley": {
        "file": "frankenstein.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Shelley's gothic science fiction (~80 k tokens). "
            "Elevated Romantic prose with nested narration."
        ),
    },
    "Dracula — Bram Stoker": {
        "file": "dracula.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Stoker's epistolary vampire novel (~165 k tokens). "
            "Multiple narrative voices — diary entries, letters, telegrams."
        ),
    },
    "The War of the Worlds — H.G. Wells": {
        "file": "war_of_the_worlds.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Wells's science fiction classic (~60 k tokens). "
            "Journalistic, urgent prose style."
        ),
    },
    "The Strange Case of Dr Jekyll and Mr Hyde — R.L. Stevenson": {
        "file": "jekyll_and_hyde.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Stevenson's psychological novella (~25 k tokens). "
            "Short but stylistically dense — good for sparsity demos."
        ),
    },
    "The Metamorphosis — Franz Kafka": {
        "file": "metamorphosis.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Kafka's surrealist novella in translation (~20 k tokens). "
            "Flat, matter-of-fact prose describing impossible events."
        ),
    },
    "Crime and Punishment — Fyodor Dostoevsky": {
        "file": "crime_and_punishment.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Dostoevsky's psychological novel in translation (~250 k tokens). "
            "Interior monologue; long, anxious sentences."
        ),
    },
    "The Adventures of Sherlock Holmes — Arthur Conan Doyle": {
        "file": "sherlock_holmes.txt",
        "gutenberg": True,
        "category": "Fiction",
        "description": (
            "Doyle's twelve short detective stories (~110 k tokens). "
            "Clear, methodical prose; strong dialogue."
        ),
    },

    # ── Drama ─────────────────────────────────────────────────────────────────

    "Hamlet — William Shakespeare": {
        "file": "hamlet.txt",
        "gutenberg": True,
        "category": "Drama",
        "description": (
            "Shakespeare's tragedy in verse and prose (~30 k tokens). "
            "Poetic metre makes n-gram patterns especially striking."
        ),
    },
    "Macbeth — William Shakespeare": {
        "file": "macbeth.txt",
        "gutenberg": True,
        "category": "Drama",
        "description": (
            "Shakespeare's shortest tragedy (~20 k tokens). "
            "Dense imagery; short, percussive lines."
        ),
    },
    "Romeo and Juliet — William Shakespeare": {
        "file": "romeo_and_juliet.txt",
        "gutenberg": True,
        "category": "Drama",
        "description": (
            "Shakespeare's romantic tragedy (~26 k tokens). "
            "Mix of verse, prose, and sonnets."
        ),
    },
    "A Midsummer Night's Dream — William Shakespeare": {
        "file": "midsummer_night.txt",
        "gutenberg": True,
        "category": "Drama",
        "description": (
            "Shakespeare's fairy comedy (~18 k tokens). "
            "Playful, musical language; good contrast with the tragedies."
        ),
    },

    # ── Poetry ────────────────────────────────────────────────────────────────

    "Leaves of Grass — Walt Whitman": {
        "file": "leaves_of_grass.txt",
        "gutenberg": True,
        "category": "Poetry",
        "description": (
            "Whitman's free verse collection (~125 k tokens). "
            "Long, cumulative lines — very different from prose n-gram output."
        ),
    },

    # ── Non-fiction / Essays ──────────────────────────────────────────────────

    "On the Origin of Species — Charles Darwin": {
        "file": "origin_of_species.txt",
        "gutenberg": True,
        "category": "Non-fiction",
        "description": (
            "Darwin's scientific argument (~230 k tokens). "
            "Dense, cautious prose; good contrast with fictional styles."
        ),
    },
    "Walden — Henry David Thoreau": {
        "file": "walden.txt",
        "gutenberg": True,
        "category": "Non-fiction",
        "description": (
            "Thoreau's philosophical memoir (~100 k tokens). "
            "Aphoristic, meditative sentences."
        ),
    },
    "Common Sense — Thomas Paine": {
        "file": "common_sense.txt",
        "gutenberg": True,
        "category": "Non-fiction",
        "description": (
            "Paine's revolutionary pamphlet (~25 k tokens). "
            "Combative, rhetorical prose; pairs well with the Declaration."
        ),
    },
    "The Prince — Niccolò Machiavelli": {
        "file": "the_prince.txt",
        "gutenberg": True,
        "category": "Non-fiction",
        "description": (
            "Machiavelli's political treatise in translation (~45 k tokens). "
            "Instructional, analytical register."
        ),
    },
    "Meditations — Marcus Aurelius": {
        "file": "meditations.txt",
        "gutenberg": True,
        "category": "Non-fiction",
        "description": (
            "Aurelius's Stoic reflections in translation (~40 k tokens). "
            "Short, aphoristic fragments — interesting for unigram/bigram models."
        ),
    },

    # ── Speeches & Documents ─────────────────────────────────────────────────

    "Gettysburg Address — Abraham Lincoln": {
        "file": "gettysburg_address.txt",
        "gutenberg": False,
        "category": "Speeches & Documents",
        "description": (
            "Lincoln's 272-word address (1863). "
            "Very short — demonstrates sparsity at high n dramatically."
        ),
    },
    "Second Inaugural Address — Abraham Lincoln": {
        "file": "lincoln_second_inaugural.txt",
        "gutenberg": False,
        "category": "Speeches & Documents",
        "description": (
            "Lincoln's 700-word second inaugural (1865). "
            "Measured, Biblical cadence; pairs well with the Gettysburg Address."
        ),
    },
    "Declaration of Independence": {
        "file": "declaration_of_independence.txt",
        "gutenberg": False,
        "category": "Speeches & Documents",
        "description": (
            "The 1776 founding document (~1,300 words). "
            "Formal eighteenth-century prose with long parallel constructions."
        ),
    },
    "Pearl Harbor Address — Franklin D. Roosevelt": {
        "file": "fdr_pearl_harbor.txt",
        "gutenberg": False,
        "category": "Speeches & Documents",
        "description": (
            "FDR's 500-word address to Congress, December 8 1941. "
            "Direct, declarative sentences — very different register from Lincoln."
        ),
    },
}

CUSTOM_LABEL = "Custom text (paste below)"

# Ordered list of categories for display grouping
CATEGORIES = [
    "Fiction",
    "Drama",
    "Poetry",
    "Non-fiction",
    "Speeches & Documents",
]


def load_text(display_name: str) -> str:
    """Load and return the cleaned text for *display_name*."""
    if display_name not in BUNDLED_TEXTS:
        raise KeyError(f"Unknown text: {display_name!r}")

    meta = BUNDLED_TEXTS[display_name]
    path = _HERE / meta["file"]
    raw = path.read_text(encoding="utf-8", errors="ignore")

    if meta["gutenberg"]:
        raw = _strip_gutenberg(raw)

    return raw.strip()


def all_display_names() -> list[str]:
    return list(BUNDLED_TEXTS.keys())


def display_names_by_category() -> dict[str, list[str]]:
    """Return display names grouped by category, in canonical order."""
    groups: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    for name, meta in BUNDLED_TEXTS.items():
        cat = meta.get("category", "Other")
        groups.setdefault(cat, []).append(name)
    return {cat: names for cat, names in groups.items() if names}


def description_for(display_name: str) -> str:
    return BUNDLED_TEXTS.get(display_name, {}).get("description", "")


def category_for(display_name: str) -> str:
    return BUNDLED_TEXTS.get(display_name, {}).get("category", "")
