# Fran16 command protocol

Fran16 is the UltiMusE III graphics server. This describes nitros9 `wb/ultimuse` at b7db9d55e: `level2/wildbits/ultimuse/port/cmds/Fran16.asm` (the command table `tblInitData` and the reader `dispatch`) and `equates.asm`.

## The connection
- UMusE3 forks Fran16 with three paths:
  - **stdin** is the command pipe. UMusE3 writes to it through its own stdout (`printf`/`putchar`) and flushes it before every key poll.
  - **stdout** (path 1) is the reply pipe. UMusE3 keeps its end as the path in `FranReply` ($1100).
  - **path 2** is `/term`. Fran allocates and frees the bitmaps there (SS.AScrn/SS.DScrn).
- The fork parameters are the 3 bytes of `FranParam`: the module's two tail blocks, then CR. Fran copies the symbol bank from those blocks.
- At start-up Fran sets up both screens: it DMA-clears bitmap 0, then creates bitmap 1 and DMA-copies bitmap 0 into it. It then writes **one ready byte** on the reply pipe. UMusE3's first `PianoHookInstall` waits for that byte.

## The byte stream
| Byte | Meaning |
|---|---|
| $00-$7F | Text for the current text window (ignored when none is open). CR = new line, FF = clear and home, BS = backspace, CAN ($18) = erase to line start, BEL = bell. Anything else draws an 8x6 glyph. |
| $80-$D2 | A command. The table below gives its argument count, and exactly that many argument bytes follow. |
| anything else | Prints `**Fran: Illegal Cmd $xx` in the text window and skips input to resynchronize. |

- **Arguments:** each is one byte (arg0, arg1 ...). A 16-bit value is two bytes, high first.
- **Units:**
  - **col** is an 8-dot byte column, 0-79.
  - **row** is a canvas row, 0-191, counted from the **bottom**.
  - **x** is a dot, 0-639.
  - Bitmap rows 192-239 belong to UMusE3 (the keyboard), and Fran never draws there.
- **End of file inside a command:** Fran prints `Fran: EOF in Cmd $xx; need n args, got m.` on stderr, rings the bell and stops reading. Between commands, Fran frees everything and exits.
- **Double buffering:** Fran draws on the hidden page, and `$CA` shows it. `$B8`, echoed text and menus also draw on the shown page.
- **Replies:** menu answers (`$B9`) and the start-up ready byte. Error text also lands on the reply pipe (see Known defects).

## Commands
Arguments are listed in order. "hi,lo" = a 16-bit value in two bytes. "–" = no arguments, or ignored ones.

### Windows, text, menus
| Cmd | Name | Args | Does |
|---|---|---|---|
| $83 | gtext | – (1) | Opens the centered 32x18 text window, unless it is already open. |
| $C6 | owsta | col, top row, width, lines, save, style | Opens a new text window and makes it current. Style 1 is a double frame, 2 rounded, anything else plain. Saves the background when `save` is non-zero. |
| $C7 | wkillcmd | – (1) | Closes the current window and restores its background. Swallowed once after a menu toggle row. |
| $CC | acura | on/off, – | Turns the text cursor (an underline) on or off. |
| $C3 | patience | – (1) | Opens a 33x3 box that reads "Patience...this takes time...". |
| $B0 | gaboa | flag | Non-zero opens the 32x18 window with "RELEASE TO ABORT". 0 closes it and leaves text mode. |
| $C0 | phrsa | col, row, skip-row-6 | Flips the page, then reads one CR-ended line from the pipe and draws it opaque at row+4. |
| $C4 | menua | menu 0-22, – | The old fixed menus. 7 and 12 draw the Layout/Setup side panel; the others open a window and print their strings. Sends no answer. |
| $B9 | ctxma | col, top row, rows (≤32), width | Condensed menu (details below). |
| $C9 | yesno | col, top row | Draws a 36x4 YES / NO! box. Fran never sends the choice. |

`$B9` exchange:
1. Fran reads one line per row from the pipe: the key letter, the label, then CR. A $10 byte dims the row; $60/$7F makes it a checkbox.
2. Fran then reads 4-byte mouse packets: x (a word), row, code.
3. On the reply pipe it sends 0 for each pointer move, then the key clicked or typed, or CR.

### Layout state (stored, nothing drawn)
| Cmd | Name | Args | Does |
|---|---|---|---|
| $88 | defsa | staff 0-6 (bit 7 = gray lines), clef, bottom row | Defines a staff. |
| $89 | udfsa | count | Keeps only the first `count` staves. |
| $8A | defpa | part 1-16, staff, flags, 3 ignored | Defines a part. |
| $8B | udfpa | part | Drops the parts from `part` up. |
| $8C | sksa | key (signed) | Stores the key signature. |
| $8E | stsa | numerator, denominator | Stores the time signature. |
| $94 | dfrna | kind ($20 = rest), value, modifier, mark | Sets the brush record that `$92` draws. |
| $9A | scura | record 0-37, – | Selects the cursor symbol the toolbox uses. |

### Staves and score marks
| Cmd | Name | Args | Does |
|---|---|---|---|
| $9C | drsa | bottom row (≤173), bar flag, clef, dotted flag | One full-width staff, with optional bar and clef. |
| $9D | ersa | – | Erases the last `$9C` staff. |
| $9E | dralstcl | bar flag, indent, dotted flag | Redraws every defined staff with its clef. |
| $9F | drsha | staff, ink (0 erases), – | A layout-screen staff with its number and clef. |
| $BD | drsys | – (1) | The system bracket in column 0, across all staves. |
| $B1 | slaya | –, range flag, – | The whole layout screen. With the flag set, it first reads nparts+1 pitch bytes from the pipe. |
| $A1 | drsta | flags (b0 draw/erase, b6 = 128th), col, row, mods | A 16x16 rest plus its modifier. Erasing also sets the rectangle `$AC`/`$AD` use. |
| $A9 | arta | set, col, row, type (0 tie .. 4 staccato), stem-down | Articulation mark. Type 2 draws nothing. |
| $A3 | daksa | col, key (signed) | Key-signature sign and count, on every staff. |
| $A4 | datsa | col, numerator, denominator glyph | Time signature, on every staff. |
| $A8 | diasa | col, item, number hi,lo | On every staff, with the number below: bar/repeat, segno, coda or block mark. Item 21 clears the column. |
| $A5 | dxlva | col, row, level 0-7 | Dynamic mark, ppp to fff. |
| $A2 | dmcha | col, row, n | An `H` glyph with n+1 beside it. |
| $A6 | dinsa | col, row, n | An `I` glyph with n beside it. |
| $AB | dpeva | col, row, n | An `E` glyph with n beside it (the number is left out when n is negative). |
| $A7 | dglia | col, type, value | Top event line: tempo ($19), dynamic ($1A), and the $1B, $1F/$21 and $22 marks. |
| $AA | dcrsa | col, level, count, type | Top line: `>` or `<` with a dynamic mark (types 0/1), or the level as a number (types 2/3). Below it, the count, prefixed `A` (2) or `R` (3). |
| $B2 | dlaba | col, char1, char2 | A boxed 1-2 character label on rows 174-183. |
| $C1 | dbcda | col, row, value | A number in digit symbols, stacked downward. |

### Lines, boxes, areas
| Cmd | Name | Args | Does |
|---|---|---|---|
| $B4 | hlina | x1 hi,lo, x2 hi,lo, row, color | Horizontal line: color 1 = ink, 0 = paper, anything else = a pattern. |
| $B5 | vlina | x hi,lo, row1, row2, set | Vertical line, in ink or paper. |
| $D0 | blinea | x1 hi,lo, y1, x2 hi,lo, y2, thick | Beam line (slope up to 45°). Fran remembers it for `$D1`/`$D2`. |
| $D1 | bagnla | row offset (signed) | Redraws the last beam higher or lower. |
| $D2 | (L07C5) | row offset, from-x hi,lo, to-x hi,lo | Draws part of the last beam. |
| $B6 | boxa | col1, row1, col2, row2 | Outline box in ink. |
| $B8 | nboxa | col1, row1, col2, row2 | Inverts a rectangle on both pages (hover highlight). |
| $BC | clra | col1, row1, col2, row2, – | Clears a rectangle to paper, by DMA when it is large. |
| $90 | claa | pattern | Fills the whole picture: 0 = paper, 1 = ink, anything else = stipple. |
| $91 | cssa | – | Clears the sheet area (rows 8-184). |
| $98 | mainbord | – | Clears column 0 on rows 8-184. |
| $97 | dmenbar | – | Draws the top menu bar (rows 185-191). |
| $95 | scrla | total hi,lo, start hi,lo, end hi,lo | Scroll bar on rows 0-7, with the thumb. |
| $96 | scrma | – (1) | Scroll bar with a 2-unit thumb (see Known defects). |
| $AC | getnbak | – (1) | Saves the rectangle around the last erased rest. |
| $AD | putnbak | – (1) | Restores that rectangle. |

### Toolbox, drag, brush
| Cmd | Name | Args | Does |
|---|---|---|---|
| $99 | rftba | bottom row, mode, flag | Draws the toolbox (columns 16-60). |
| $92 | drepa | col, row, tool | Saves the area under it, then draws the brush box. |
| $93 | erbrush | – (1) | Restores the brush box's background. |
| $C2 | dragset | kind (0 off, 1 clef, else part icon), index, – | Arms or disarms the drag glyph. |
| $9B | dcura | x hi,lo, row, – | Moves the drag glyph. |

### Refresh, printer, no-ops
| Cmd | Name | Args | Does |
|---|---|---|---|
| $CA | pollmark | – (1) | Present: shows the drawn page and brings the other page up to date. UMusE3 sends it before waiting for the user. |
| $AE, $B7, $CB, $CD | unimp | – (0/4/0/1) | Only makes Fran drop the next CR. |
| $BF | prtboss | op ('b' 'd' 'e' 'q' '1'), printer type, squeeze, FF, margin, – | Printer control to `/p`. The bitmap dump is a stub. |
| $BE | squeeze | – (1) | Squeezes out blank rows. Still in the old 1-bit format. |
| $CE | dumpa | printer type, – | Sets the printer type. The dump is a stub. |
| $87 | pala | register, color | No-op since 2026-09-09. |
| $CF | beepa | – (1) | No-op (the beep is silenced). |
| $C5 | keynop | – (14) | No-op since 2026-09-28 (the piano keys are drawn by UMusE3). |

## Known defects
- **`$CA` is in the table twice:** `pollmark` (Fran16.asm line 13495) and `FrRenderFocusedPart` = $CA (equates.asm line 51, table line 13499). The first match wins, so the focused-part renderer never runs.
- **`$96 scrma`** takes 1 argument but reads `<arg1`, which it never receives. The thumb position is a leftover byte.
- **`$C2 dragset`** caps the index at 6 for every kind: the limit check tests A instead of the kind.
- **`$B8 nboxa` without double buffering** (no DMA, as under MAME): the two inversions cancel out, so no hover shows.
- **Error text on the reply pipe:** when a window's background save fails to allocate, Fran prints `al%d`, and `$C7` can print `**Can't free`. Both go on path 1, where UMusE3 can read them as a menu answer.
- **`$C9 yesno`** draws the buttons but never reports the choice.
