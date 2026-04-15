from enum import Enum

class Suit(Enum):
    CLUBS = "♣"
    DIAMONDS = "♦"
    HEARTS = "♥"
    SPADES = "♠"

class Rank(Enum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

class Card:
    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit

    @property
    def is_red(self) -> bool:
        return self.suit in (Suit.HEARTS, Suit.DIAMONDS)

    @property
    def is_black(self) -> bool:
        return self.suit in (Suit.CLUBS, Suit.SPADES)

    def __repr__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))
