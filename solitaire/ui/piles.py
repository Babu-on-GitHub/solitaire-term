from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static

from solitaire.assets.card_art import (
    CardSize,
    SIZES,
    foundation_empty_frame,
    make_card_lines,
    make_facedown_lines,
    _empty_frame,
)
from solitaire.engine.card import Card
from solitaire.engine.moves import Location, PileType
from solitaire.engine.state import FOUNDATION_SUITS
from solitaire.ui.widgets import CardWidget, EmptyPileWidget, _apply_color


PEEK_WIDTH = 5  # columns shown per peeked waste card (rank + suit visible for all ranks incl "10")


class StockWidget(Static):
    """The draw pile. Click to draw one card or recycle the waste."""

    class Clicked(Message):
        pass

    def __init__(
        self, has_cards: bool, size: CardSize | None = None, **kwargs
    ) -> None:
        self._card_size = size if size is not None else SIZES[-1]
        super().__init__(self._content(has_cards, self._card_size), **kwargs)
        self._has_cards = has_cards

    @staticmethod
    def _content(has_cards: bool, size: CardSize) -> str:
        lines = make_facedown_lines(size) if has_cards else _empty_frame(size.width, size.height, "\u21ba")
        return "[dim]" + "\n".join(lines) + "[/dim]"

    def set_state(self, has_cards: bool) -> None:
        self._has_cards = has_cards
        self.update(self._content(has_cards, self._card_size))

    def on_mount(self) -> None:
        self.styles.width = self._card_size.width
        self.styles.height = self._card_size.height

    def on_click(self) -> None:
        self.post_message(StockWidget.Clicked())


class WasteWidget(Static):
    """Shows the top card(s) of the waste pile. In draw-3 mode shows up to 3 cards fanned."""

    class Clicked(Message):
        def __init__(self, location: Location) -> None:
            super().__init__()
            self.location = location

    def __init__(
        self,
        waste: list[Card],
        draw_mode: int = 1,
        size: CardSize | None = None,
        **kwargs,
    ) -> None:
        self._card_size = size if size is not None else SIZES[-1]
        self._draw_mode = draw_mode
        self._waste = list(waste)
        super().__init__(self._content(waste, draw_mode, self._card_size), **kwargs)

    @staticmethod
    def _content(waste: list[Card], draw_mode: int, size: CardSize) -> str:
        top_card = waste[-1] if waste else None
        if draw_mode == 1:
            if top_card is not None:
                return _apply_color("\n".join(make_card_lines(top_card, size)), top_card)
            return "[dim]" + "\n".join(_empty_frame(size.width, size.height)) + "[/dim]"

        # Draw-3: composite display (up to 2 peeked + 1 full)
        if top_card is None:
            empty = _empty_frame(size.width, size.height)
            lines = [" " * (PEEK_WIDTH * 2) + ln for ln in empty]
            return "[dim]" + "\n".join(lines) + "[/dim]"

        peeked = waste[max(0, len(waste) - 3):-1] if len(waste) > 1 else []
        empty_slots = 2 - len(peeked)
        top_lines = make_card_lines(top_card, size)

        def _safe_peek_lines(card: Card, sz: CardSize) -> list[str]:
            """Simple border+rank lines for peeked cards — no [, ], or \\ chars."""
            full = make_card_lines(card, sz)
            blank = "|" + " " * (sz.width - 2) + "|"
            return [full[0], full[1], *[blank] * (sz.height - 4), full[-2], full[-1]]

        peeked_art = [_safe_peek_lines(c, size) for c in peeked]

        def color(text: str, card: Card) -> str:
            safe = text.replace("[", r"\[")
            return f"[red]{safe}[/red]" if card.is_red else safe

        result = []
        for row in range(size.height):
            line = " " * (PEEK_WIDTH * empty_slots)
            for card, art in zip(peeked, peeked_art):
                line += color(art[row][:PEEK_WIDTH], card)
            line += color(top_lines[row], top_card)
            result.append(line)
        return "\n".join(result)

    def _widget_width(self) -> int:
        if self._draw_mode == 3:
            return PEEK_WIDTH * 2 + self._card_size.width
        return self._card_size.width

    def set_state(
        self, waste: list[Card], draw_mode: int, selected: bool = False
    ) -> None:
        self._waste = list(waste)
        self._draw_mode = draw_mode
        top_card = waste[-1] if waste else None
        self.update(self._content(waste, draw_mode, self._card_size))
        self.styles.width = self._widget_width()
        if selected and top_card is not None:
            self.add_class("selected")
        else:
            self.remove_class("selected")

    def on_mount(self) -> None:
        self.styles.width = self._widget_width()
        self.styles.height = self._card_size.height

    def on_click(self) -> None:
        top_card = self._waste[-1] if self._waste else None
        if top_card is not None:
            self.post_message(
                WasteWidget.Clicked(Location(PileType.WASTE, 0, len(self._waste) - 1))
            )


class FoundationWidget(Static):
    """One of the four foundation piles. Shows top card or the suit placeholder."""

    class Clicked(Message):
        def __init__(self, location: Location) -> None:
            super().__init__()
            self.location = location

    def __init__(
        self,
        suit_idx: int,
        top_card: Card | None,
        pile_len: int,
        size: CardSize | None = None,
        **kwargs,
    ) -> None:
        self._card_size = size if size is not None else SIZES[-1]
        super().__init__(self._content(suit_idx, top_card, self._card_size), **kwargs)
        self._suit_idx = suit_idx
        self._top_card = top_card
        self._pile_len = pile_len

    @staticmethod
    def _content(suit_idx: int, top_card: Card | None, size: CardSize) -> str:
        if top_card is not None:
            return _apply_color("\n".join(make_card_lines(top_card, size)), top_card)
        suit = FOUNDATION_SUITS[suit_idx]
        return "[dim]" + "\n".join(foundation_empty_frame(suit, size)) + "[/dim]"

    def set_state(
        self, top_card: Card | None, pile_len: int, selected: bool = False
    ) -> None:
        self._top_card = top_card
        self._pile_len = pile_len
        self.update(self._content(self._suit_idx, top_card, self._card_size))
        if selected and top_card is not None:
            self.add_class("selected")
        else:
            self.remove_class("selected")

    def on_mount(self) -> None:
        self.styles.width = self._card_size.width
        self.styles.height = self._card_size.height

    def on_click(self) -> None:
        card_idx = self._pile_len - 1 if self._pile_len > 0 else -1
        self.post_message(
            FoundationWidget.Clicked(Location(PileType.FOUNDATION, self._suit_idx, card_idx))
        )


class TableauColumnWidget(Vertical):
    """One tableau column: face-down cards stacked below face-up cards."""

    def __init__(
        self,
        col_idx: int,
        pile: list[Card],
        face_up_count: int,
        selected_card_indices: set[int],
        size: CardSize | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._col_idx = col_idx
        self._pile = list(pile)
        self._face_up_count = face_up_count
        self._selected_indices = set(selected_card_indices)
        self._card_size = size if size is not None else SIZES[-1]

    def compose(self) -> ComposeResult:
        yield from self._build_children()

    def set_state(
        self,
        pile: list[Card],
        face_up_count: int,
        selected_card_indices: set[int],
    ) -> None:
        self._pile = list(pile)
        self._face_up_count = face_up_count
        self._selected_indices = set(selected_card_indices)
        for child in list(self.children):
            child.remove()
        self.mount(*self._build_children())

    def on_mount(self) -> None:
        self.styles.width = self._card_size.width

    def _build_children(self) -> list:
        if not self._pile:
            return [EmptyPileWidget(
                location=Location(PileType.TABLEAU, self._col_idx, -1),
                size=self._card_size,
            )]
        face_down_count = len(self._pile) - self._face_up_count
        last_idx = len(self._pile) - 1
        return [
            CardWidget(
                card=card,
                face_up=i >= face_down_count,
                location=Location(PileType.TABLEAU, self._col_idx, i),
                selected=i in self._selected_indices,
                size=self._card_size,
                peek=(i < last_idx),
            )
            for i, card in enumerate(self._pile)
        ]
