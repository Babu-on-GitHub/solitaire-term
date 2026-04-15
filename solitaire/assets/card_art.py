"""
Card art generation for all sizes.

Each card is a list of fixed-width strings (one per line).
PEEK_LINES = 2 means the first two lines (top border + rank header) are
shown for stacked / face-down cards; the rest is hidden by widget height.

Card anatomy for width W, height H:
  Line 0            : top border
  Line 1            : rank top-left
  Lines 2 .. H-3    : suit art (H-4 lines)
  Line H-2          : rank bottom-right
  Line H-1          : bottom border

Width layout (inner = W - 2, i.e. everything between the two `|` chars):
  rank top  : | <rank> <spaces…>  |
  rank bot  : | <spaces…> <rank>  |
  suit line : |   <symbol centrd> |
  back line : |/\\/\\/\\/…        |
  blank line: |<spaces>           |
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from solitaire.engine.card import Card, Rank, Suit

# ── Constants ────────────────────────────────────────────────────────────────

PEEK_LINES: int = 2

_RANK_LABELS: dict[int, str] = {1: "A", 11: "J", 12: "Q", 13: "K"}


def _rank_label(rank: Rank) -> str:
    return _RANK_LABELS.get(rank.value, str(rank.value))


# ── Card size definitions ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class CardSize:
    name: str
    width: int           # total card width including borders
    height: int          # total card height including borders
    min_term_width: int  # minimum terminal columns needed for 7 tableau cols


# Largest-first so pick_size() can short-circuit on first match.
# min_term_width = 7 * (width + 1) + 4  (7 cols, 1-char gap each, 2 pad sides)
SIZES: tuple[CardSize, ...] = (
    CardSize("xlarge", 13, 9, 102),
    CardSize("large",  11, 9,  88),
    CardSize("medium",  9, 7,  74),
    CardSize("small",   7, 5,   0),   # always-available fallback
)


def pick_size(terminal_width: int | None = None) -> CardSize:
    """Return the largest card size that fits in the terminal."""
    if terminal_width is None:
        terminal_width, _ = shutil.get_terminal_size()
    for size in SIZES:
        if terminal_width >= size.min_term_width:
            return size
    return SIZES[-1]


# ── Line builders ─────────────────────────────────────────────────────────────

def _top(w: int) -> str:
    return "." + "-" * (w - 2) + "."


def _bot(w: int) -> str:
    return "`" + "-" * (w - 2) + "'"


def _rank_top(rank: str, suit: str, w: int) -> str:
    inner = w - 2
    return "|" + (" " + rank + suit).ljust(inner) + "|"


def _rank_bot(rank: str, suit: str, w: int) -> str:
    inner = w - 2
    return "|" + (suit + rank + " ").rjust(inner) + "|"


def _blank(w: int) -> str:
    return "|" + " " * (w - 2) + "|"


def _suit(suit: Suit, w: int) -> str:
    inner = w - 2
    return "|" + suit.value.center(inner) + "|"


def _back(w: int) -> str:
    """One interior line of the card-back hatching pattern."""
    inner = w - 2
    pattern = "/\\" * ((inner // 2) + 1)
    return "|" + pattern[:inner] + "|"


def _empty_frame(w: int, h: int, label: str = "") -> list[str]:
    """Full-height ASCII frame for an empty slot (dim style applied by caller)."""
    mid = h // 2
    lines: list[str] = [
        _top(w),
        *[_blank(w)] * (h - 2),
        _bot(w),
    ]
    if label:
        lines[mid] = "|" + label.center(w - 2) + "|"
    return lines


# ── Full card art ─────────────────────────────────────────────────────────────

def make_card_lines(card: Card, size: CardSize) -> list[str]:
    """Return the full card art as a list of strings (one per line)."""
    w = size.width
    rank = _rank_label(card.rank)
    n_art = size.height - 4  # lines between rank_top and rank_bot

    # Placeholder suit art: symbol centered on the middle art line, rest blank.
    art: list[str] = []
    mid = n_art // 2
    for i in range(n_art):
        art.append(_suit(card.suit, w) if i == mid else _blank(w))

    suit = card.suit.value
    return [_top(w), _rank_top(rank, suit, w), *art, _rank_bot(rank, suit, w), _bot(w)]


def make_facedown_lines(size: CardSize) -> list[str]:
    """Return the full face-down card art as a list of strings."""
    w = size.width
    n_interior = size.height - 2
    return [_top(w), *[_back(w) for _ in range(n_interior)], _bot(w)]


# ── Peek helpers (always PEEK_LINES = 2) ─────────────────────────────────────

def peek_card(card: Card, size: CardSize) -> list[str]:
    """Top border + rank line for a face-up card."""
    return make_card_lines(card, size)[:PEEK_LINES]


def peek_facedown(size: CardSize) -> list[str]:
    """Top border + back-pattern line for a face-down card."""
    return make_facedown_lines(size)[:PEEK_LINES]
