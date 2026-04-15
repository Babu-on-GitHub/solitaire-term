from __future__ import annotations

from pathlib import Path

from textual import events, on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Static

from solitaire.assets.card_art import CardSize, pick_size
from solitaire.engine.game_logic import KlondikeEngine
from solitaire.engine.moves import Location, PileType
from solitaire.ui.piles import (
    FoundationWidget,
    StockWidget,
    TableauColumnWidget,
    WasteWidget,
)
from solitaire.ui.widgets import CardWidget, EmptyPileWidget


class WinScreen(ModalScreen):
    DEFAULT_CSS = """
    WinScreen {
        align: center middle;
    }
    WinScreen > Horizontal {
        width: 44;
        height: 9;
        border: double $success;
        background: $surface;
        align: center middle;
        padding: 2 4;
    }
    #win-title { text-align: center; }
    #win-sub { text-align: center; color: $text-muted; }
    """

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static("[bold green] You Win! [/bold green]", id="win-title")
            yield Static("  Press any key to play again  ", id="win-sub")

    def on_key(self) -> None:
        self.dismiss()

    def on_click(self) -> None:
        self.dismiss()


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

    def compose(self) -> ComposeResult:
        state = self.engine.state
        yield Header()
        with Container(id="game-board"):
            with Horizontal(id="top-area"):
                with Horizontal(id="stock-waste"):
                    yield StockWidget(
                        has_cards=bool(state.stock),
                        size=self.card_size,
                        id="stock",
                    )
                    yield WasteWidget(
                        top_card=state.waste_top(),
                        waste_top_index=len(state.waste) - 1,
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
        yield Footer()

    async def on_mount(self) -> None:
        correct_size = pick_size(self.size.width)
        if correct_size != self.card_size:
            self.card_size = correct_size
            await self.recompose()
        self._apply_top_area_height()

    def _apply_top_area_height(self) -> None:
        self.query_one("#top-area").styles.height = self.card_size.height

    async def on_resize(self, event: events.Resize) -> None:
        new_size = pick_size(event.size.width)
        if new_size != self.card_size:
            self.card_size = new_size
            self.selected_location = None
            await self.recompose()
            self._apply_top_area_height()

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
            state.waste_top(), len(state.waste) - 1, selected=waste_sel
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

    def action_new_game(self) -> None:
        self.selected_location = None
        self.engine.new_game()
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
        def _on_dismiss(_result: object) -> None:
            self.action_new_game()

        self.push_screen(WinScreen(), callback=_on_dismiss)
