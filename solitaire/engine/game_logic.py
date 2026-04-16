from __future__ import annotations

from solitaire.engine.card import Card, Rank, Suit
from solitaire.engine.deck import Deck
from solitaire.engine.state import GameState, FOUNDATION_SUITS
from solitaire.engine.moves import Location, MoveRecord, PileType


class KlondikeEngine:
    """
    Pure game logic for Draw-1 Klondike Solitaire.

    Contract:
    - State is NEVER mutated before validation.
    - All public methods return bool (success/failure).
    - undo() reverts exactly the last successful mutating operation.
    """

    def __init__(self) -> None:
        self.state: GameState = GameState()
        self._undo_stack: list[MoveRecord] = []
        self.new_game()

    def debug_near_win(self) -> None:
        """Set up a state that is exactly 2 moves from winning.

        Three suits are complete on foundations. Spades has A–J (11 cards).
        Waste holds [K♠, Q♠] with Q♠ on top, so:
          move 1: Q♠ waste → foundation (spades becomes A–Q)
          move 2: K♠ waste → foundation (spades complete) → win
        """
        state = GameState()
        for suit in (Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS):
            idx = FOUNDATION_SUITS.index(suit)
            state.foundations[idx] = [Card(rank, suit) for rank in Rank]
        spades_idx = FOUNDATION_SUITS.index(Suit.SPADES)
        state.foundations[spades_idx] = [
            Card(rank, Suit.SPADES)
            for rank in list(Rank)[:11]  # A through J
        ]
        state.waste = [Card(Rank.KING, Suit.SPADES), Card(Rank.QUEEN, Suit.SPADES)]
        self.state = state
        self._undo_stack.clear()

    def new_game(self) -> None:
        deck = Deck()
        deck.shuffle()
        state = GameState()
        for col in range(7):
            for _ in range(col + 1):
                state.tableau[col].append(deck.draw())
            state.face_up_counts[col] = 1
        while len(deck) > 0:
            state.stock.append(deck.draw())
        self.state = state
        self._undo_stack.clear()

    def draw_stock(self) -> bool:
        """Move top of stock to waste. Returns False if stock is empty."""
        if not self.state.stock:
            return False
        record = MoveRecord(
            move_type="draw",
            prev_stock=self.state.stock.copy(),
            prev_waste=self.state.waste.copy(),
        )
        self.state.waste.append(self.state.stock.pop())
        self._push_undo(record)
        return True

    def recycle_stock(self) -> bool:
        """Flip waste back to stock. Returns False if stock non-empty or waste empty."""
        if self.state.stock or not self.state.waste:
            return False
        record = MoveRecord(
            move_type="recycle",
            prev_stock=self.state.stock.copy(),
            prev_waste=self.state.waste.copy(),
        )
        self.state.stock = list(reversed(self.state.waste))
        self.state.waste.clear()
        self._push_undo(record)
        return True

    def can_move(self, from_loc: Location, to_loc: Location) -> bool:
        """Validate a move without mutating state."""
        cards = self._get_cards_to_move(from_loc)
        if not cards:
            return False
        if to_loc.pile_type == PileType.TABLEAU:
            return self._is_valid_tableau_dest(cards[0], to_loc.pile_index)
        if to_loc.pile_type == PileType.FOUNDATION:
            if len(cards) != 1:
                return False
            return self._is_valid_foundation_dest(cards[0], to_loc.pile_index)
        return False

    def move(self, from_loc: Location, to_loc: Location) -> bool:
        """
        Execute a move after validating it.
        Returns False immediately (no state mutation) if invalid.
        """
        if not self.can_move(from_loc, to_loc):
            return False

        cards = self._get_cards_to_move(from_loc)

        record = MoveRecord(move_type="move")
        record.from_pile_type = from_loc.pile_type
        record.to_pile_type = to_loc.pile_type

        # Snapshot source
        if from_loc.pile_type == PileType.WASTE:
            record.from_pile_snapshot = self.state.waste.copy()
        elif from_loc.pile_type == PileType.FOUNDATION:
            record.from_pile_idx = from_loc.pile_index
            record.from_pile_snapshot = self.state.foundations[from_loc.pile_index].copy()
        elif from_loc.pile_type == PileType.TABLEAU:
            record.from_pile_idx = from_loc.pile_index
            record.from_pile_snapshot = self.state.tableau[from_loc.pile_index].copy()
            record.from_face_up_count = self.state.face_up_counts[from_loc.pile_index]

        # Snapshot destination
        if to_loc.pile_type == PileType.TABLEAU:
            record.to_pile_idx = to_loc.pile_index
            record.to_pile_snapshot = self.state.tableau[to_loc.pile_index].copy()
            record.to_face_up_count = self.state.face_up_counts[to_loc.pile_index]
        elif to_loc.pile_type == PileType.FOUNDATION:
            record.to_pile_idx = to_loc.pile_index
            record.to_pile_snapshot = self.state.foundations[to_loc.pile_index].copy()

        # Extract from source
        if from_loc.pile_type == PileType.WASTE:
            self.state.waste.pop()
        elif from_loc.pile_type == PileType.FOUNDATION:
            self.state.foundations[from_loc.pile_index].pop()
        elif from_loc.pile_type == PileType.TABLEAU:
            col = from_loc.pile_index
            n = len(cards)
            del self.state.tableau[col][-n:]
            self.state.face_up_counts[col] = max(0, self.state.face_up_counts[col] - n)
            # Flip new top if no face-up cards remain
            if self.state.tableau[col] and self.state.face_up_counts[col] == 0:
                self.state.face_up_counts[col] = 1

        # Place at destination
        if to_loc.pile_type == PileType.TABLEAU:
            col = to_loc.pile_index
            self.state.tableau[col].extend(cards)
            self.state.face_up_counts[col] += len(cards)
        elif to_loc.pile_type == PileType.FOUNDATION:
            self.state.foundations[to_loc.pile_index].extend(cards)

        self._push_undo(record)
        return True

    def undo(self) -> bool:
        """Undo the last successful operation. Returns False if nothing to undo."""
        if not self._undo_stack:
            return False
        record = self._undo_stack.pop()

        if record.move_type in ("draw", "recycle"):
            self.state.stock = record.prev_stock
            self.state.waste = record.prev_waste

        elif record.move_type == "move":
            # Restore source
            if record.from_pile_type == PileType.WASTE:
                self.state.waste = record.from_pile_snapshot
            elif record.from_pile_type == PileType.FOUNDATION:
                self.state.foundations[record.from_pile_idx] = record.from_pile_snapshot
            elif record.from_pile_type == PileType.TABLEAU:
                self.state.tableau[record.from_pile_idx] = record.from_pile_snapshot
                self.state.face_up_counts[record.from_pile_idx] = record.from_face_up_count

            # Restore destination
            if record.to_pile_type == PileType.TABLEAU:
                self.state.tableau[record.to_pile_idx] = record.to_pile_snapshot
                self.state.face_up_counts[record.to_pile_idx] = record.to_face_up_count
            elif record.to_pile_type == PileType.FOUNDATION:
                self.state.foundations[record.to_pile_idx] = record.to_pile_snapshot

        return True

    def has_won(self) -> bool:
        return self.state.is_won()

    # --- Private helpers ---

    def _get_cards_to_move(self, from_loc: Location) -> list[Card]:
        """Return the cards that would be picked up from from_loc (no mutation)."""
        if from_loc.pile_type == PileType.STOCK:
            return []
        if from_loc.pile_type == PileType.WASTE:
            top = self.state.waste_top()
            return [top] if top is not None else []
        if from_loc.pile_type == PileType.FOUNDATION:
            top = self.state.foundation_top(from_loc.pile_index)
            return [top] if top is not None else []
        if from_loc.pile_type == PileType.TABLEAU:
            col = from_loc.pile_index
            pile = self.state.tableau[col]
            idx = from_loc.card_index
            if idx < 0 or idx >= len(pile):
                return []
            face_down_count = len(pile) - self.state.face_up_counts[col]
            if idx < face_down_count:
                return []  # trying to take a face-down card
            return pile[idx:]
        return []

    def _is_valid_tableau_dest(self, card: Card, col: int) -> bool:
        top = self.state.tableau_top(col)
        if top is None:
            return card.rank == Rank.KING
        return (card.is_red != top.is_red) and (card.rank.value == top.rank.value - 1)

    def _is_valid_foundation_dest(self, card: Card, suit_idx: int) -> bool:
        if FOUNDATION_SUITS[suit_idx] != card.suit:
            return False
        top = self.state.foundation_top(suit_idx)
        if top is None:
            return card.rank == Rank.ACE
        return card.rank.value == top.rank.value + 1

    def _push_undo(self, record: MoveRecord) -> None:
        self._undo_stack.append(record)
        if len(self._undo_stack) > 1:
            self._undo_stack.pop(0)
