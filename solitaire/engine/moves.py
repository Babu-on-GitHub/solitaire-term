from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from solitaire.engine.card import Card


class PileType(Enum):
    STOCK = auto()
    WASTE = auto()
    FOUNDATION = auto()
    TABLEAU = auto()


@dataclass(frozen=True)
class Location:
    """
    Identifies a position in the game state.

    pile_index:
      STOCK/WASTE → always 0
      FOUNDATION  → 0-3 (matches FOUNDATION_SUITS order)
      TABLEAU     → 0-6

    card_index:
      Index within the pile list (0 = bottom).
      -1 means an empty pile slot was clicked (no card at that position).
    """
    pile_type: PileType
    pile_index: int
    card_index: int = -1


@dataclass
class MoveRecord:
    """Snapshot sufficient to undo a single move."""
    move_type: str  # "draw" | "recycle" | "move"

    # For "draw" and "recycle"
    prev_stock: list | None = None
    prev_waste: list | None = None

    # For "move" — source
    from_pile_type: PileType | None = None
    from_pile_idx: int | None = None
    from_pile_snapshot: list | None = None
    from_face_up_count: int | None = None  # tableau only

    # For "move" — destination
    to_pile_type: PileType | None = None
    to_pile_idx: int | None = None
    to_pile_snapshot: list | None = None
    to_face_up_count: int | None = None  # tableau only
