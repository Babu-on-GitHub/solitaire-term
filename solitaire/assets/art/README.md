# Card Art

One `.txt` file per rank per size. Edit freely — changes take effect on the next run.

## Card sizes

| Folder      | Card (W × H) | Interior lines | Interior width | Min terminal width |
|-------------|:------------:|:--------------:|:--------------:|:-----------------:|
| `small`     |    7 × 5     |       1        |       5        |        —          |
| `medium`    |    9 × 7     |       3        |       7        |       74          |
| `large`     |   11 × 9     |       5        |       9        |       88          |
| `xlarge`    |   13 × 9     |       5        |       11       |      102          |
| `xxlarge`   |   17 × 12    |       8        |       15       |      130          |

`small` is the always-available fallback (no minimum terminal width).  
The game automatically picks the largest size that fits; resize the terminal and it adapts.

## File naming and fallback order

For each card the loader tries four names in order, stopping at the first match:

1. `<rank>_<suit>.txt` — specific to one rank **and** suit (e.g. `ace_hearts.txt`)
2. `<rank>.txt` — all suits of that rank share the same art (e.g. `jack.txt`)
3. `default_<suit>.txt` — suit-specific background for all ranks
4. `default.txt` — universal background for all ranks and suits

Suit names are lowercase: `clubs`, `diamonds`, `hearts`, `spades`.  
Rank names: `ace`, `2`–`10`, `jack`, `queen`, `king`.

If none of the four files exist for a given size, the engine falls back to generated art (pip grids, ace shapes, face-card boxes, or a centered suit symbol).

## File contents — interior lines only

Files contain **only the interior** of the card. Borders and rank corners are added by the engine:

```
.-----------.     ← top border        (not in file)
| A♠        |     ← rank top-left     (not in file)
|           |
|  your     |     ← interior lines    (this is what the file contains)
|  art      |
|           |
|        ♠A |     ← rank bottom-right (not in file)
`-----------'     ← bottom border     (not in file)
```

Each file should have at most `H - 4` lines, each at most `W - 2` characters wide (see table above). Lines or characters beyond those limits are silently handled by cropping and centering.

## Centering and cropping

The loader always produces exactly `H - 4` lines of exactly `W - 2` characters:

**Vertical** — if the file has fewer lines than needed, blank lines are padded equally top and bottom (odd remainder goes to the bottom). If the file has more lines than needed, the excess is cropped symmetrically from top and bottom, keeping the middle.

**Horizontal** — the widest line in the block sets the reference width. If that width is narrower than `W - 2`, the whole block is centered (equal spaces left and right, odd remainder on the right). If it is wider, the block is cropped symmetrically left and right, keeping the center columns. Short lines within the block are space-padded on the right before centering or cropping is applied.

In short: write any size art you like and it will be fitted to the card automatically.

## Card anatomy reference

```
.-----------.     W = 11, H = 9  (large)
| A♠        |     rank top:    "| " + rank + suit + padding + "|"
|           |
|           |     \
|           |      interior lines — H - 4 = 5 lines, W - 2 = 9 chars each
|           |     /
|           |
|        ♠A |     rank bottom: "|" + padding + suit + rank + " |"
`-----------'
```
