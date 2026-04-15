import random
from typing import List
from solitaire.engine.card import Card, Rank, Suit


class Deck:
    def __init__(self):
        self.cards: List[Card] = []
        self._reset()

    def _reset(self):
        self.cards = [Card(rank, suit) for rank in Rank for suit in Suit]

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card:
        return self.cards.pop()

    def __len__(self):
        return len(self.cards)

    def __repr__(self) -> str:
        return f"Deck({len(self.cards)} cards left)"
