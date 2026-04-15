"""
Card art generation for all sizes.

Each card is a list of fixed-width strings (one per line).
PEEK_LINES = 2 means the first two lines (top border + rank header) are
shown for stacked / face-down cards; the rest is hidden by widget height.

Card anatomy for width W, height H:
  Line 0            : top border
  Line 1            : rank top-left  (rank + suit symbol)
  Lines 2 .. H-3    : interior art   (H-4 lines)
  Line H-2          : rank bottom-right
  Line H-1          : bottom border

Interior art by size:
  small  (7×5,  1 interior line)  : blank — no art
  medium (9×7,  3 interior lines) : ace shape, face-card box
  large  (11×9, 5 interior lines) : ace shape, face-card box w/ crown
  xlarge (13×9, 5 interior lines) : ace shape, pip grid, face-card box w/ crown
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

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


_ASSETS_DIR = Path(__file__).parent

_RANK_NAMES: dict[Rank, str] = {
    Rank.ACE:   "ace",
    Rank.TWO:   "2",   Rank.THREE: "3",  Rank.FOUR:  "4",
    Rank.FIVE:  "5",   Rank.SIX:   "6",  Rank.SEVEN: "7",
    Rank.EIGHT: "8",   Rank.NINE:  "9",  Rank.TEN:   "10",
    Rank.JACK:  "jack", Rank.QUEEN: "queen", Rank.KING: "king",
}


def pick_size(terminal_width: int | None = None) -> CardSize:
    """Return the largest card size that fits in the terminal."""
    if terminal_width is None:
        terminal_width, _ = shutil.get_terminal_size()
    for size in SIZES:
        if terminal_width >= size.min_term_width:
            return size
    return SIZES[-1]


# ── Primitive line builders ───────────────────────────────────────────────────

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


def _back(w: int) -> str:
    """One interior line of the card-back hatching pattern."""
    inner = w - 2
    pattern = "/\\" * ((inner // 2) + 1)
    return "|" + pattern[:inner] + "|"


def _empty_frame(w: int, h: int, label: str = "") -> list[str]:
    """Full-height ASCII frame for an empty slot (dim style applied by caller)."""
    mid = h // 2
    lines: list[str] = [_top(w), *[_blank(w)] * (h - 2), _bot(w)]
    if label:
        lines[mid] = "|" + label.center(w - 2) + "|"
    return lines


# ── Interior art helpers ──────────────────────────────────────────────────────

def _centered(s: str, count: int, inner: int) -> str:
    """Return `count` copies of `s` centered in `inner` columns."""
    sp = (inner - count) // 2
    ep = inner - count - sp
    return " " * sp + s * count + " " * ep


def _art_ace(s: str, n: int, inner: int) -> list[str]:
    """
    Inverted-triangle ace art using suit symbol `s`.
    Returns n strings each exactly `inner` chars wide (no borders).

    Shape (n=5):  two bumps at top, tapering to a point — heart-like.
    Shape (n=3):  small triangle — suits medium cards.
    """
    if n == 5:
        pad = (inner - 7) // 2
        rp  = inner - 7 - 2 * pad          # handles odd (inner - 7)
        lines = [
            " " * pad + s + " " * 5 + s + " " * (pad + rp),   # twin bumps
            " " * pad + s * 7           + " " * (pad + rp),   # solid band
        ]
        for syms in (5, 3, 1):
            lines.append(_centered(s, syms, inner))
        return lines
    elif n == 3:
        return [_centered(s, syms, inner) for syms in (5, 3, 1)]
    else:
        # n=1 or any other size: single centered symbol
        return [_centered(s, 1, inner)] * n


# ── Pip art (xlarge only: n=5, inner=11) ─────────────────────────────────────

# (row, col) positions within a 5×11 grid for each pip count.
# Left col=3, center col=5, right col=7.
_PIP_LAYOUTS: dict[int, list[tuple[int, int]]] = {
    2:  [(0, 5), (4, 5)],
    3:  [(0, 5), (2, 5), (4, 5)],
    4:  [(0, 3), (0, 7), (4, 3), (4, 7)],
    5:  [(0, 3), (0, 7), (2, 5), (4, 3), (4, 7)],
    6:  [(0, 3), (0, 7), (2, 3), (2, 7), (4, 3), (4, 7)],
    7:  [(0, 3), (0, 7), (1, 5), (2, 3), (2, 7), (4, 3), (4, 7)],
    8:  [(0, 3), (0, 7), (1, 5), (2, 3), (2, 7), (3, 5), (4, 3), (4, 7)],
    9:  [(0, 3), (0, 7), (1, 3), (1, 7), (2, 5), (3, 3), (3, 7), (4, 3), (4, 7)],
    10: [(0, 3), (0, 7), (1, 3), (1, 7), (2, 3), (2, 7), (3, 3), (3, 7), (4, 3), (4, 7)],
}


def _art_pip(s: str, rank_val: int, n: int, inner: int) -> list[str]:
    """
    Classic pip-grid art. Only generates for xlarge (n=5, inner=11);
    returns blank lines for any other size.
    """
    if n != 5 or inner != 11 or rank_val not in _PIP_LAYOUTS:
        return [" " * inner] * n
    grid = [[" "] * inner for _ in range(n)]
    for r, c in _PIP_LAYOUTS[rank_val]:
        grid[r][c] = s
    return ["".join(row) for row in grid]


# ── Face-card art (J, Q, K) ───────────────────────────────────────────────────

def _crown_row(char: str, inner: int) -> str:
    """Alternating char/space crown row, exactly `inner` wide."""
    pattern = (char + " ") * ((inner + 1) // 2)
    return pattern[:inner]


def _art_face(rank: Rank, n: int, inner: int) -> list[str]:
    """
    Simple box art for face cards.

    J  — plain box, rank letter centred and mirrored top/bottom.
    Q  — crown row (@ symbols) above box.
    K  — crown row (* symbols) above box.

    Returns n strings each exactly `inner` chars wide (no borders).
    """
    box_inner = 5                         # "+-----+" body width
    box_w     = box_inner + 2             # 7 chars total
    pad       = (inner - box_w) // 2
    extra     = inner - box_w - 2 * pad   # ≥0, handles odd widths

    lp = " " * pad
    rp = " " * (pad + extra)

    r        = rank.name[0]              # "J", "Q", "K"
    box_top  = lp + "+" + "-" * box_inner + "+" + rp
    box_bot  = lp + "+" + "-" * box_inner + "+" + rp
    body     = lp + "|" + " " * box_inner + "|" + rp
    label    = lp + "|  " + r + "  |" + rp

    if n == 5:
        if rank == Rank.KING:
            crown = lp + _crown_row("*", box_w) + rp
            return [crown, box_top, label, body, box_bot]
        elif rank == Rank.QUEEN:
            crown = lp + _crown_row("@", box_w) + rp
            return [crown, box_top, label, body, box_bot]
        else:   # Jack — double-headed
            return [box_top, label, body, label, box_bot]
    elif n == 3:
        # No inner box — avoids double-border artefact when inner == box_w.
        # Use a dash rule top/bottom instead and center the rank letter.
        rule = "-" * inner
        mid  = r.center(inner)
        if rank == Rank.KING:
            return [_crown_row("*", inner), mid, rule]
        elif rank == Rank.QUEEN:
            return [_crown_row("@", inner), mid, rule]
        else:
            return [rule, mid, rule]
    else:
        return [" " * inner] * n


# ── Custom art file loader ────────────────────────────────────────────────────

@lru_cache(maxsize=None)
def _load_card_art(rank_name: str, size: CardSize) -> tuple[str, ...] | None:
    """
    Load interior art lines from ``solitaire/assets/art/<size>/<rank>.txt``.

    Returns a tuple of exactly ``size.height - 4`` strings, each exactly
    ``size.width - 2`` chars wide (cropped / space-padded as needed).
    Returns None if the file does not exist (caller falls back to generated art).
    """
    path = _ASSETS_DIR / "art" / size.name / f"{rank_name}.txt"
    if not path.exists():
        return None
    n     = size.height - 4
    inner = size.width - 2
    lines = path.read_text().splitlines()
    lines = lines[:n]                           # crop excess height
    while len(lines) < n:
        lines.append("")                        # pad missing lines
    return tuple(line[:inner].ljust(inner) for line in lines)


def reload_card_art() -> None:
    """Clear the art cache so edited files take effect without a restart."""
    _load_card_art.cache_clear()


# ── Interior dispatcher ───────────────────────────────────────────────────────

def _card_interior(card: Card, size: CardSize) -> list[str]:
    """
    Return the bordered interior lines for a card (between rank_top and rank_bot).
    Each element is a full-width bordered string: "|" + inner_content + "|".
    """
    n     = size.height - 4
    inner = size.width - 2

    custom = _load_card_art(_RANK_NAMES[card.rank], size)
    if custom is not None:
        return ["|" + line + "|" for line in custom]

    s = card.suit.value

    if size.name == "small":
        inner_lines: list[str] = [" " * inner] * n
    elif card.rank == Rank.ACE:
        inner_lines = _art_ace(s, n, inner)
    elif card.rank.value <= 10:             # 2–10
        inner_lines = _art_pip(s, card.rank.value, n, inner)
    else:                                   # J, Q, K
        inner_lines = _art_face(card.rank, n, inner)

    return ["|" + line + "|" for line in inner_lines]


# ── Full card / facedown art ──────────────────────────────────────────────────

def make_card_lines(card: Card, size: CardSize) -> list[str]:
    """Return the full card art as a list of strings (one per line)."""
    w    = size.width
    rank = _rank_label(card.rank)
    suit = card.suit.value
    art  = _card_interior(card, size)
    return [_top(w), _rank_top(rank, suit, w), *art, _rank_bot(rank, suit, w), _bot(w)]


def make_facedown_lines(size: CardSize) -> list[str]:
    """Return the full face-down card art as a list of strings."""
    w = size.width
    n_interior = size.height - 2
    return [_top(w), *[_back(w) for _ in range(n_interior)], _bot(w)]


# ── Foundation empty frame ────────────────────────────────────────────────────

def foundation_empty_frame(suit: Suit, size: CardSize) -> list[str]:
    """
    Full card-height frame for an empty foundation slot.
    Small size: centred suit symbol (simple).
    Larger sizes: suit-art using the ace triangle pattern.
    """
    w     = size.width
    h     = size.height
    inner = w - 2
    s     = suit.value

    if size.name == "small":
        return _empty_frame(w, h, s)

    n_interior = h - 2                     # rows between top/bottom border
    art_rows   = min(n_interior, 5)
    art        = _art_ace(s, art_rows, inner)

    pad     = n_interior - art_rows
    top_pad = pad // 2
    bot_pad = pad - top_pad

    interior = (
        [_blank(w)] * top_pad
        + ["|" + line + "|" for line in art]
        + [_blank(w)] * bot_pad
    )
    return [_top(w), *interior, _bot(w)]


# ── Peek helpers (always PEEK_LINES = 2) ─────────────────────────────────────

def peek_card(card: Card, size: CardSize) -> list[str]:
    """Top border + rank line for a face-up card."""
    return make_card_lines(card, size)[:PEEK_LINES]


def peek_facedown(size: CardSize) -> list[str]:
    """Top border + back-pattern line for a face-down card."""
    return make_facedown_lines(size)[:PEEK_LINES]
