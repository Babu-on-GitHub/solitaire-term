# solitaire-term

Klondike Solitaire in the terminal, built with [Textual](https://textual.textualize.io/) and with cat themed ascii art.

![demo](/images/Screenshot%202026-04-16%20at%2012.35.05.png)

## Features

- **Draw 1 or Draw 3** — choose the mode at the start of every new game
- **Full ASCII card art** — five card sizes selected automatically from your terminal width, best played on the highest size.
- **Mouse inputs** — play entirely by mouse, just like you used to on you mom's Windows XP desktop growing up.

## Requirements

| Requirement | Minimum |
|-------------|---------|
| Python | 3.11+ |
| Terminal width | 40 columns (7-wide cards) |
| Terminal width for best experience | 130+ columns (17-wide cards, full art) |
| Color support | 16-color ANSI (red/black suits, highlighting) |
| Unicode support | Basic — card suits (♠ ♥ ♦ ♣) and box-drawing characters |

The game auto-selects the largest card size that fits your terminal. Resize the window and it adapts instantly.

## Running

Install dependencies and launch with [uv](https://github.com/astral-sh/uv):

```bash
uv run python main.py
```

Or with a plain Python environment:

```bash
pip install textual
python main.py
```

## Controls

| Key / Action | Effect |
|---|---|
| Click stock | Draw card(s) |
| Click a card | Select it |
| Click another card / empty column | Move selected card(s) there |
| Click selected card again | Deselect |
| `Enter` | Draw card(s) from stock |
| `U` | Undo last move |
| `R` | New game (draw mode dialog appears) |
| `Q` | Quit |

### Two-click move system

1. Click the card (or stack base) you want to move — it highlights.
2. Click the destination card or empty column — the move is made if valid.
3. Click the highlighted card again to cancel the selection.

In Draw-3 mode the waste pile shows the top three cards: the back two are peeked (rank + suit visible), the front card is fully rendered and is the one that can be played.

## Card size tiers

| Terminal width | Card size | Dimensions |
|---|---|---|
| 130+ | xxlarge | 17 × 12 |
| 102–129 | xlarge | 13 × 9 |
| 88–101 | large | 11 × 9 |
| 74–87 | medium | 9 × 7 |
| < 74 | small | 7 × 5 |

## Running tests

```bash
uv run pytest
```
