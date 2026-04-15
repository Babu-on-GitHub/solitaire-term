import pytest
from solitaire.engine.card import Card, Rank, Suit
from solitaire.engine.state import GameState, FOUNDATION_SUITS
from solitaire.engine.game_logic import KlondikeEngine
from solitaire.engine.moves import Location, PileType


def c(rank: int, suit: Suit) -> Card:
    return Card(Rank(rank), suit)


S = Suit.SPADES
H = Suit.HEARTS
D = Suit.DIAMONDS
C = Suit.CLUBS

LOC_WASTE = Location(PileType.WASTE, 0, 0)


def test_deal():
    engine = KlondikeEngine()
    state = engine.state
    assert state.card_count() == 52
    for i in range(7):
        assert len(state.tableau[i]) == i + 1, f"col {i} wrong length"
        assert state.face_up_counts[i] == 1, f"col {i} wrong face-up count"
    assert len(state.stock) == 24  # 52 - (1+2+3+4+5+6+7)
    assert len(state.waste) == 0
    assert all(len(f) == 0 for f in state.foundations)


def test_draw_stock():
    engine = KlondikeEngine()
    initial_stock = len(engine.state.stock)
    assert engine.draw_stock()
    assert len(engine.state.stock) == initial_stock - 1
    assert len(engine.state.waste) == 1


def test_draw_stock_undo():
    engine = KlondikeEngine()
    top_card = engine.state.stock[-1]
    engine.draw_stock()
    assert engine.state.waste[-1] == top_card
    engine.undo()
    assert len(engine.state.waste) == 0
    assert engine.state.stock[-1] == top_card


def test_draw_stock_empty_fails():
    engine = KlondikeEngine()
    engine.state.stock.clear()
    assert not engine.draw_stock()


def test_recycle_stock():
    engine = KlondikeEngine()
    stock_count = len(engine.state.stock)
    for _ in range(stock_count):
        engine.draw_stock()
    assert len(engine.state.stock) == 0
    assert len(engine.state.waste) == stock_count
    assert engine.recycle_stock()
    assert len(engine.state.stock) == stock_count
    assert len(engine.state.waste) == 0


def test_recycle_stock_fails_when_stock_nonempty():
    engine = KlondikeEngine()
    assert not engine.recycle_stock()


def test_valid_tableau_move():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.tableau[0] = [c(5, H)]   # 5♥ (red)
    engine.state.face_up_counts[0] = 1
    engine.state.tableau[1] = [c(6, S)]   # 6♠ (black)
    engine.state.face_up_counts[1] = 1

    from_loc = Location(PileType.TABLEAU, 0, 0)
    to_loc = Location(PileType.TABLEAU, 1, 0)
    assert engine.can_move(from_loc, to_loc)
    assert engine.move(from_loc, to_loc)
    assert len(engine.state.tableau[0]) == 0
    assert engine.state.tableau[1] == [c(6, S), c(5, H)]
    assert engine.state.face_up_counts[1] == 2


def test_invalid_tableau_move_same_color():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.tableau[0] = [c(5, S)]   # 5♠ (black)
    engine.state.face_up_counts[0] = 1
    engine.state.tableau[1] = [c(6, C)]   # 6♣ (black)
    engine.state.face_up_counts[1] = 1

    from_loc = Location(PileType.TABLEAU, 0, 0)
    to_loc = Location(PileType.TABLEAU, 1, 0)
    assert not engine.can_move(from_loc, to_loc)
    assert not engine.move(from_loc, to_loc)
    # State unchanged
    assert len(engine.state.tableau[0]) == 1
    assert len(engine.state.tableau[1]) == 1


def test_invalid_tableau_move_wrong_rank():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.tableau[0] = [c(4, H)]   # 4♥ (red)
    engine.state.face_up_counts[0] = 1
    engine.state.tableau[1] = [c(6, S)]   # 6♠ (black) — must be 5 to accept 4
    engine.state.face_up_counts[1] = 1

    from_loc = Location(PileType.TABLEAU, 0, 0)
    to_loc = Location(PileType.TABLEAU, 1, 0)
    assert not engine.can_move(from_loc, to_loc)


def test_king_to_empty_tableau():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.waste = [c(13, S)]       # K♠
    engine.state.tableau[0] = []
    engine.state.face_up_counts[0] = 0

    from_loc = LOC_WASTE
    to_loc = Location(PileType.TABLEAU, 0, -1)
    assert engine.can_move(from_loc, to_loc)
    assert engine.move(from_loc, to_loc)
    assert engine.state.tableau[0] == [c(13, S)]


def test_non_king_to_empty_tableau_fails():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.waste = [c(12, H)]       # Q♥
    engine.state.tableau[0] = []
    engine.state.face_up_counts[0] = 0

    assert not engine.can_move(LOC_WASTE, Location(PileType.TABLEAU, 0, -1))


def test_move_to_foundation_ace():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.waste = [c(1, C)]        # A♣

    from_loc = LOC_WASTE
    to_loc = Location(PileType.FOUNDATION, 0, -1)  # foundation 0 = ♣
    assert engine.can_move(from_loc, to_loc)
    assert engine.move(from_loc, to_loc)
    assert engine.state.foundations[0] == [c(1, C)]
    assert len(engine.state.waste) == 0


def test_move_to_foundation_sequence():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.foundations[2] = [c(1, H), c(2, H)]  # foundation 2 = ♥, has A♥ 2♥
    engine.state.waste = [c(3, H)]                      # 3♥

    from_loc = LOC_WASTE
    to_loc = Location(PileType.FOUNDATION, 2, 1)
    assert engine.can_move(from_loc, to_loc)
    assert engine.move(from_loc, to_loc)
    assert len(engine.state.foundations[2]) == 3


def test_invalid_foundation_non_ace_on_empty():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.waste = [c(2, C)]  # 2♣ — not Ace

    assert not engine.can_move(LOC_WASTE, Location(PileType.FOUNDATION, 0, -1))
    assert not engine.move(LOC_WASTE, Location(PileType.FOUNDATION, 0, -1))
    assert engine.state.foundations[0] == []


def test_invalid_foundation_wrong_suit():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.foundations[0] = [c(1, C)]  # ♣ foundation has A♣
    engine.state.waste = [c(2, H)]            # 2♥ — wrong suit

    from_loc = LOC_WASTE
    to_loc = Location(PileType.FOUNDATION, 0, 0)
    assert not engine.can_move(from_loc, to_loc)


def test_multi_card_tableau_move():
    engine = KlondikeEngine()
    engine.state = GameState()
    # col 0: [8♦(down), 6♥(up), 5♠(up)] — sequence starts at index 1
    # 6♥ (red) and 5♠ (black) are a valid alternating-color run
    engine.state.tableau[0] = [c(8, D), c(6, H), c(5, S)]
    engine.state.face_up_counts[0] = 2
    # col 1: [7♣] face up (black 7 accepts red 6)
    engine.state.tableau[1] = [c(7, C)]
    engine.state.face_up_counts[1] = 1

    from_loc = Location(PileType.TABLEAU, 0, 1)  # pick up 6♥ and 5♠
    to_loc = Location(PileType.TABLEAU, 1, 0)
    assert engine.can_move(from_loc, to_loc)
    assert engine.move(from_loc, to_loc)
    # col 0 has only 8♦ left, auto-flipped
    assert engine.state.tableau[0] == [c(8, D)]
    assert engine.state.face_up_counts[0] == 1
    # col 1 has [7♣, 6♥, 5♠]
    assert engine.state.tableau[1] == [c(7, C), c(6, H), c(5, S)]
    assert engine.state.face_up_counts[1] == 3


def test_cannot_take_face_down_card():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.tableau[0] = [c(7, S), c(5, H)]
    engine.state.face_up_counts[0] = 1  # only 5♥ (index 1) is face-up

    # Try to take 7♠ (index 0 — face-down) to an empty column
    engine.state.tableau[1] = []
    engine.state.face_up_counts[1] = 0
    from_loc = Location(PileType.TABLEAU, 0, 0)
    to_loc = Location(PileType.TABLEAU, 1, -1)
    assert not engine.can_move(from_loc, to_loc)


def test_undo_tableau_move():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.tableau[0] = [c(5, H)]
    engine.state.face_up_counts[0] = 1
    engine.state.tableau[1] = [c(6, S)]
    engine.state.face_up_counts[1] = 1

    engine.move(Location(PileType.TABLEAU, 0, 0), Location(PileType.TABLEAU, 1, 0))
    assert engine.state.tableau[1] == [c(6, S), c(5, H)]

    engine.undo()
    assert engine.state.tableau[0] == [c(5, H)]
    assert engine.state.face_up_counts[0] == 1
    assert engine.state.tableau[1] == [c(6, S)]
    assert engine.state.face_up_counts[1] == 1


def test_flip_after_move():
    engine = KlondikeEngine()
    engine.state = GameState()
    # col 0: face-down 7♣ underneath face-up 5♥
    engine.state.tableau[0] = [c(7, C), c(5, H)]
    engine.state.face_up_counts[0] = 1
    engine.state.tableau[1] = [c(6, S)]
    engine.state.face_up_counts[1] = 1

    # Move 5♥ off col 0 — 7♣ should auto-flip
    engine.move(Location(PileType.TABLEAU, 0, 1), Location(PileType.TABLEAU, 1, 0))
    assert engine.state.tableau[0] == [c(7, C)]
    assert engine.state.face_up_counts[0] == 1  # auto-flipped


def test_undo_preserves_flip_state():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.tableau[0] = [c(7, C), c(5, H)]
    engine.state.face_up_counts[0] = 1  # only 5♥ face-up before move
    engine.state.tableau[1] = [c(6, S)]
    engine.state.face_up_counts[1] = 1

    engine.move(Location(PileType.TABLEAU, 0, 1), Location(PileType.TABLEAU, 1, 0))
    # 7♣ is now face-up; undo should restore it to face-down
    engine.undo()
    assert engine.state.tableau[0] == [c(7, C), c(5, H)]
    assert engine.state.face_up_counts[0] == 1  # back to only 5♥ face-up


def test_foundation_to_tableau():
    engine = KlondikeEngine()
    engine.state = GameState()
    engine.state.foundations[2] = [c(1, H), c(2, H), c(3, H)]  # ♥ foundation
    engine.state.tableau[0] = [c(4, S)]  # 4♠ (black) — can accept 3♥
    engine.state.face_up_counts[0] = 1

    from_loc = Location(PileType.FOUNDATION, 2, 2)
    to_loc = Location(PileType.TABLEAU, 0, 0)
    assert engine.can_move(from_loc, to_loc)
    assert engine.move(from_loc, to_loc)
    assert engine.state.foundations[2] == [c(1, H), c(2, H)]
    assert engine.state.tableau[0] == [c(4, S), c(3, H)]


def test_win_condition():
    engine = KlondikeEngine()
    engine.state = GameState()
    assert not engine.has_won()
    for i, suit in enumerate(FOUNDATION_SUITS):
        engine.state.foundations[i] = [c(r, suit) for r in range(1, 14)]
    assert engine.has_won()
    assert engine.state.is_won()


def test_undo_nothing_returns_false():
    engine = KlondikeEngine()
    assert not engine.undo()
