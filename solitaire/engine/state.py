from __future__ import annotations

from dataclasses import dataclass, field

from solitaire.engine.card import Card, Suit

FOUNDATION_SUITS: tuple[Suit, ...] = (
    Suit.CLUBS,
    Suit.DIAMONDS,
    Suit.HEARTS,
    Suit.SPADES,
)


@dataclass
class GameState:
    """
    Complete game state. All lists use index -1 as top / most recent card.

    Invariants:
    - len(tableau) == 7
    - len(face_up_counts) == 7
    - 0 <= face_up_counts[i] <= len(tableau[i]) for all i
    - len(foundations) == 4
    - All 52 cards are distributed across all piles at all times.
    """

    stock: list[Card] = field(default_factory=list)
    waste: list[Card] = field(default_factory=list)
    foundations: list[list[Card]] = field(
        default_factory=lambda: [[], [], [], []]
    )
    tableau: list[list[Card]] = field(
        default_factory=lambda: [[] for _ in range(7)]
    )
    face_up_counts: list[int] = field(
        default_factory=lambda: [0] * 7
    )
    draw_mode: int = 1

    # --- Tableau helpers ---

    def tableau_face_up(self, col: int) -> list[Card]:
        pile = self.tableau[col]
        n_up = self.face_up_counts[col]
        return pile[len(pile) - n_up:] if n_up > 0 else []

    def tableau_top(self, col: int) -> Card | None:
        pile = self.tableau[col]
        return pile[-1] if pile else None

    # --- Foundation helpers ---

    def foundation_top(self, suit_idx: int) -> Card | None:
        pile = self.foundations[suit_idx]
        return pile[-1] if pile else None

    def foundation_suit_index(self, suit: Suit) -> int:
        return FOUNDATION_SUITS.index(suit)

    # --- Waste helpers ---

    def waste_top(self) -> Card | None:
        return self.waste[-1] if self.waste else None

    # --- Win / debug ---

    def is_won(self) -> bool:
        return all(len(f) == 13 for f in self.foundations)

    def card_count(self) -> int:
        return (
            len(self.stock)
            + len(self.waste)
            + sum(len(f) for f in self.foundations)
            + sum(len(t) for t in self.tableau)
        )
