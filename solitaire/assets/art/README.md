# Card Art

One `.txt` file per rank per size. Edit freely — changes take effect on the next run.

## Dimensions

Each file contains the **interior** lines only (no card borders, no rank corners).

| Folder    | Lines | Chars/line | Card size  |
|-----------|------:|----------:|------------|
| `small`   |     1 |         5 | 7 × 5      |
| `medium`  |     3 |         7 | 9 × 7      |
| `large`   |     5 |         9 | 11 × 9     |
| `xlarge`  |     5 |        11 | 13 × 9     |
| `xxlarge` |    10 |        15 | 17 × 14    |

Lines or characters beyond the limits are silently cropped. Short lines are space-padded on the right.

## Card anatomy

```
.-----------.     ← top border
| A♠        |     ← rank top-left  (not in file)
|           |
|  your     |     ← interior lines (this is what the files contain)
|  art      |
|           |
|        ♠A |     ← rank bottom-right  (not in file)
`-----------'     ← bottom border
```

## Files

`ace.txt`, `2.txt` … `10.txt`, `jack.txt`, `queen.txt`, `king.txt`
