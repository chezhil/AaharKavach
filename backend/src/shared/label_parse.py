"""Turn OCR'd label text into a product name and an ingredient list.

Deterministic on purpose: it runs with no model configured, and when the agent
*is* available it still owns only transcription — the verdict is always the
matcher's. A misread label must not be able to talk its way to "safe".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Where the ingredient list starts, and where it stops. Indian labels use all
# of these, often in the same panel.
START = re.compile(r"\bINGREDIENTS?\b\s*[:\-]?", re.IGNORECASE)
STOP = re.compile(
    r"\b(CONTAINS|ALLERGEN|ALLERGY|NUTRITION(AL)?|NUTRIENTS?|BEST BEFORE|"
    r"MFG|MANUFACTUR|PACKED|NET (WT|WEIGHT|QTY)|STORE IN|FSSAI|BATCH|MRP|"
    r"CUSTOMER CARE|MARKETED BY)\b",
    re.IGNORECASE,
)
# Split on commas and semicolons that are not inside brackets.
SPLIT = re.compile(r"[,;](?![^(\[]*[)\]])")
NOISE = re.compile(r"^[\s\.\-–—*•·|]+|[\s\.\-–—*•·|]+$")


@dataclass
class ParsedLabel:
    product_name: str = ""
    ingredients: list[str] = field(default_factory=list)
    contains_note: str = ""

    @property
    def found_ingredients(self) -> bool:
        return bool(self.ingredients)


def _tidy(token: str) -> str:
    token = NOISE.sub("", token)
    token = re.sub(r"\s+", " ", token)
    # Percentages and bare numbers are quantities, not ingredients.
    token = re.sub(r"\s*\(\s*\d+(\.\d+)?\s*%\s*\)\s*$", "", token)
    return token.strip()


def _plausible(token: str) -> bool:
    """Filter OCR debris without dropping real short names like 'Salt'."""
    if len(token) < 3 or len(token) > 60:
        return False
    letters = sum(c.isalpha() for c in token)
    return letters >= 3 and letters / len(token) > 0.5


def parse_label(text: str) -> ParsedLabel:
    if not text or not text.strip():
        return ParsedLabel()

    flat = " ".join(line.strip() for line in text.splitlines() if line.strip())

    start = START.search(flat)
    if not start:
        # No "INGREDIENTS" heading — some panels just list them. Fall back to
        # the whole text rather than returning nothing.
        segment, name_part = flat, ""
    else:
        segment = flat[start.end() :]
        name_part = flat[: start.start()]

    stop = STOP.search(segment)
    contains_note = ""
    if stop:
        contains_note = segment[stop.start() :].strip()[:200]
        segment = segment[: stop.start()]

    ingredients = []
    seen = set()
    for raw in SPLIT.split(segment):
        token = _tidy(raw)
        if not token or not _plausible(token):
            continue
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        ingredients.append(token)

    # The product name is whatever sat above the ingredient list.
    name = ""
    if name_part:
        words = [w for w in name_part.split() if w]
        name = " ".join(words[-8:]).title() if words else ""

    return ParsedLabel(
        product_name=_tidy(name),
        ingredients=ingredients[:40],
        contains_note=contains_note,
    )
