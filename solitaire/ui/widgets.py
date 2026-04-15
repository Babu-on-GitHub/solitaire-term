from __future__ import annotations

from textual.message import Message
from textual.widgets import Static

from solitaire.assets.card_art import (
    CardSize,
    PEEK_LINES,
    SIZES,
    make_card_lines,
    make_facedown_lines,
    peek_card,
    peek_facedown,
    _empty_frame,
)
from solitaire.engine.card import Card
from solitaire.engine.moves import Location


def _apply_color(text: str, card: Card) -> str:
    """Wrap card art in red markup for red suits."""
    if card.is_red:
        return f"[red]{text}[/red]"
    return text


class CardWidget(Static):
    """
    Renders one playing card (full or peeked).

    peek=True  → shows only the top 2 lines (border + rank header).
    peek=False → shows the full card art.
    Face-down cards use a hatch pattern; face-up cards show rank + suit.
    Red-suit cards are wrapped in [red] markup.
    Selected cards receive CSS class 'selected'.
    Clicking a face-up card posts CardWidget.Clicked(location).
    """

    class Clicked(Message):
        def __init__(self, location: Location) -> None:
            super().__init__()
            self.location = location

    def __init__(
        self,
        card: Card,
        face_up: bool,
        location: Location,
        selected: bool = False,
        size: CardSize | None = None,
        peek: bool = False,
        **kwargs,
    ) -> None:
        self.card = card
        self.face_up = face_up
        self.location = location
        self._selected = selected
        self._card_size = size if size is not None else SIZES[-1]
        self._peek = peek
        super().__init__(self._build_content(), **kwargs)

    # ------------------------------------------------------------------

    def _build_content(self) -> str:
        lines = self._get_lines()
        text = "\n".join(lines)
        if self.face_up:
            return _apply_color(text, self.card)
        return f"[dim]{text}[/dim]"

    def _get_lines(self) -> list[str]:
        if self._peek:
            return (
                peek_card(self.card, self._card_size)
                if self.face_up
                else peek_facedown(self._card_size)
            )
        return (
            make_card_lines(self.card, self._card_size)
            if self.face_up
            else make_facedown_lines(self._card_size)
        )

    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        self.styles.width = self._card_size.width
        self.styles.height = PEEK_LINES if self._peek else self._card_size.height
        if self._selected:
            self.add_class("selected")

    def on_click(self) -> None:
        if self.face_up:
            self.post_message(CardWidget.Clicked(self.location))


class EmptyPileWidget(Static):
    """
    Dimmed card-frame placeholder shown when a tableau column is empty.
    Clicking it posts Clicked so the app can treat it as a move target.
    """

    class Clicked(Message):
        def __init__(self, location: Location) -> None:
            super().__init__()
            self.location = location

    def __init__(
        self,
        location: Location,
        size: CardSize | None = None,
        **kwargs,
    ) -> None:
        self._location = location
        self._card_size = size if size is not None else SIZES[-1]
        lines = _empty_frame(self._card_size.width, self._card_size.height)
        super().__init__("[dim]" + "\n".join(lines) + "[/dim]", **kwargs)

    def on_mount(self) -> None:
        self.styles.width = self._card_size.width
        self.styles.height = self._card_size.height

    def on_click(self) -> None:
        self.post_message(EmptyPileWidget.Clicked(self._location))
