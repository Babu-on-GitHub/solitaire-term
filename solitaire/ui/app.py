from __future__ import annotations

from pathlib import Path

from textual import events, on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static

from solitaire.assets.card_art import CardSize, pick_size
from solitaire.engine.game_logic import KlondikeEngine
from solitaire.engine.moves import Location, PileType
from solitaire.ui.piles import (
    FoundationWidget,
    StockWidget,
    TableauColumnWidget,
    WasteWidget,
)
from solitaire.assets.win_art import WIN_ART
from solitaire.ui.widgets import CardWidget, EmptyPileWidget




class DrawModeScreen(ModalScreen):
    """Modal dialog shown at every new game start to choose draw mode."""

    def compose(self) -> ComposeResult:
        with Vertical(id="draw-mode-box"):
            yield Static("New Game", id="draw-mode-title")
            with Horizontal(id="draw-mode-buttons"):
                yield Button("Draw 1", id="draw1", variant="default")
                yield Button("Draw 3", id="draw3", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(1 if event.button.id == "draw1" else 3)

    def on_key(self, event: events.Key) -> None:
        if event.key == "1":
            self.dismiss(1)
        elif event.key == "3":
            self.dismiss(3)


class WinScreen(ModalScreen):
    def compose(self) -> ComposeResult:
        with Horizontal(id="win-box"):
            yield Static(WIN_ART, id="win-art")
            yield Static("press any key to play again", id="win-sub")

    def on_key(self) -> None:
        self.dismiss()
        self.app.action_new_game()

    def on_click(self) -> None:
        self.dismiss()
        self.app.action_new_game()


class SolitaireApp(App):
    TITLE = "Klondike Solitaire"
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "new_game", "New Game"),
        ("u", "undo", "Undo"),
        ("enter", "draw", "Draw"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.engine = KlondikeEngine()
        self.selected_location: Location | None = None
        self.card_size: CardSize = pick_size()
        self._game_won: bool = False

    def compose(self) -> ComposeResult:
        state = self.engine.state
        with Container(id="game-board") as board:
            board.border_title = " Klondike Solitaire "
            board.border_subtitle = " q: Quit | r: New | u: Undo | enter: Draw "
            with Horizontal(id="top-area"):
                with Horizontal(id="stock-waste"):
                    yield StockWidget(
                        has_cards=bool(state.stock),
                        size=self.card_size,
                        id="stock",
                    )
                    yield WasteWidget(
                        waste=state.waste,
                        draw_mode=state.draw_mode,
                        size=self.card_size,
                        id="waste",
                    )
                yield Static("", id="top-spacer")
                with Horizontal(id="foundations"):
                    for i in range(4):
                        pile = state.foundations[i]
                        yield FoundationWidget(
                            suit_idx=i,
                            top_card=pile[-1] if pile else None,
                            pile_len=len(pile),
                            size=self.card_size,
                            id=f"foundation-{i}",
                        )
            with Horizontal(id="tableau"):
                for col in range(7):
                    yield TableauColumnWidget(
                        col_idx=col,
                        pile=state.tableau[col],
                        face_up_count=state.face_up_counts[col],
                        selected_card_indices=set(),
                        size=self.card_size,
                        id=f"tableau-{col}",
                    )

    async def on_mount(self) -> None:
        self.theme = "textual-ansi"
        correct_size = pick_size(self.size.width)
        if correct_size != self.card_size:
            self.card_size = correct_size
            await self.recompose()
        self._apply_top_area_height()
        await self.push_screen(DrawModeScreen(), self._on_draw_mode_selected)

    def _apply_top_area_height(self) -> None:
        self.query_one("#top-area").styles.height = self.card_size.height

    async def on_resize(self, event: events.Resize) -> None:
        new_size = pick_size(event.size.width)
        if new_size != self.card_size:
            self.card_size = new_size
            self.selected_location = None
            was_won = self._game_won
            await self.recompose()
            self._apply_top_area_height()
            if was_won and not isinstance(self.screen, WinScreen):
                self._show_win_screen()

    def refresh_board(self) -> None:
        """Update all pile widgets to reflect current engine state."""
        state = self.engine.state
        sel = self.selected_location

        sel_col: dict[int, set[int]] = {i: set() for i in range(7)}
        if sel is not None and sel.pile_type == PileType.TABLEAU:
            col = sel.pile_index
            for idx in range(sel.card_index, len(state.tableau[col])):
                sel_col[col].add(idx)

        waste_sel = sel is not None and sel.pile_type == PileType.WASTE
        f_sel = (
            {sel.pile_index}
            if sel is not None and sel.pile_type == PileType.FOUNDATION
            else set()
        )

        self.query_one("#stock", StockWidget).set_state(bool(state.stock))
        self.query_one("#waste", WasteWidget).set_state(
            state.waste, state.draw_mode, selected=waste_sel
        )
        for i in range(4):
            pile = state.foundations[i]
            self.query_one(f"#foundation-{i}", FoundationWidget).set_state(
                top_card=pile[-1] if pile else None,
                pile_len=len(pile),
                selected=i in f_sel,
            )
        for col in range(7):
            self.query_one(f"#tableau-{col}", TableauColumnWidget).set_state(
                state.tableau[col],
                state.face_up_counts[col],
                sel_col[col],
            )

    def _handle_card_click(self, location: Location) -> None:
        """Two-click state machine: select, then move."""
        if self.selected_location is None:
            self.selected_location = location
            self.refresh_board()
        elif self.selected_location == location:
            # Deselect
            self.selected_location = None
            self.refresh_board()
        else:
            success = self.engine.move(self.selected_location, location)
            self.selected_location = None
            self.refresh_board()
            if success and self.engine.has_won():
                self._show_win_screen()

    @on(CardWidget.Clicked)
    def on_card_widget_clicked(self, message: CardWidget.Clicked) -> None:
        self._handle_card_click(message.location)

    @on(WasteWidget.Clicked)
    def on_waste_widget_clicked(self, message: WasteWidget.Clicked) -> None:
        self._handle_card_click(message.location)

    @on(FoundationWidget.Clicked)
    def on_foundation_widget_clicked(self, message: FoundationWidget.Clicked) -> None:
        self._handle_card_click(message.location)

    @on(EmptyPileWidget.Clicked)
    def on_empty_pile_widget_clicked(self, message: EmptyPileWidget.Clicked) -> None:
        if self.selected_location is not None:
            self._handle_card_click(message.location)

    @on(StockWidget.Clicked)
    def on_stock_widget_clicked(self, _message: StockWidget.Clicked) -> None:
        self.selected_location = None
        if self.engine.state.stock:
            self.engine.draw_stock()
        else:
            self.engine.recycle_stock()
        self.refresh_board()

    def action_quit(self) -> None:
        self.exit()

    async def action_new_game(self) -> None:
        await self.push_screen(DrawModeScreen(), self._on_draw_mode_selected)

    def _on_draw_mode_selected(self, draw_mode: int) -> None:
        self._game_won = False
        self.selected_location = None
        self.engine.new_game(draw_mode)
        self.refresh_board()

    def action_undo(self) -> None:
        self.selected_location = None
        self.engine.undo()
        self.refresh_board()

    def action_draw(self) -> None:
        self.selected_location = None
        if self.engine.state.stock:
            self.engine.draw_stock()
        else:
            self.engine.recycle_stock()
        self.refresh_board()

    def _show_win_screen(self) -> None:
        self._game_won = True
        self.push_screen(WinScreen())
