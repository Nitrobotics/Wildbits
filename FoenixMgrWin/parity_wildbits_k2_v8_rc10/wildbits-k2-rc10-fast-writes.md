# WildBits K2 v8_rc10 — turbo fast RAM writes

**Date:** 2026-09-03  **Platform:** F256 WildBits K2 (Core2X, DIP-gated turbo)
**Status:** field-verified: boots Level 2, sprites correct, sprtest2, format /f1

## What changed

The turbo MMU's stretch design gave pure-RAM **reads** a 24-tick bus frame (8.39 MHz E) and
left every **write** at the stock 32 ticks. Three earlier attempts at fast writes (v7, v7b and
the first rc10 spin) froze at the end of the FEU's "Loading Sector" copy loop. A RAM dump of the
frozen kernel showed the L2 kernel's module validation rejecting every module: its DAT-slot
remaps (`sta/std >$FFA8`) were not taking effect when preceded by fast-written stack pushes.
The common factor of all three failures was a **shortened E-high phase after a write**.

The first rc10 spin kept the write frame at 24 ticks but gives it a **stock-length E-high**: the fast-write
decision is taken at t6 (the edge that registers the address) from live decodes, E rises at t8
instead of t16, Q runs t8..t15, and the frame wraps at t23. That spin booted.

The shipping rc10 moves the SRAM write into the **read slot**: the slot is claimed at t6 exactly like a
read, WEn pulses t8..t9, the slot is released at t10, and the write data is captured into a
200 MHz register at t6 (the CPU's data path settles ~19 ns after E falls; the address is
registered at the same 30 ns point). The graphics engine therefore sees a fast write with the
same t5..t8 draw-time pre-emption it gets before a read. The first rc10 spin had the write in
a mid-frame slot (t13..t16) with no pre-emption, which cut in-flight sprite fetches: sprites
vanished and sprtest2 froze. The read-slot write fixed both.

IO, MMU-table, vector, flash, EXRAM and sectored-VKY writes are untouched (full 32-tick frames
with IO_Data_Valid), as are DMA, debug and bus-free cycles.

## What to expect

`wildspeed` still reports 8.89 MHz: its loop is opcode fetches only. Memory copies and fills
gain roughly 10-12%, ordinary code 3-6%, screen/disk/WiFi nothing.

## Verification (K2, 2026-09-03)

| test | result |
|---|---|
| FEU boot, Loading Sector, Level 2 boot to shell | pass |
| ILA capture of the tick ISR: RAM writes as 24t frames, IO writes 32t with IO_Data_Valid | confirmed |
| sprtest (128 sprites, 4 CLUTs), sprtest2 | pass |
| format /f1 (flash write stress through rbmem's slot window) | pass |

Remaining on the standard list: dir /f0 and /f1, mouse, wizi remote-shell soak, held-key with
WiFi traffic.

## Build notes

Sources: `source/TyVKy2K2turbo_MMU_FNX6809.v` under `TURBO_FASTWRITE` (with `CORE2X_TURBO
CORE2X_STRETCH`); `RC10_ILA` adds 21 debug taps and the shipped bitstream carries a 4096-deep
ILA on the frame machine and CPU bus (probes file `wildbits_k2_6809_v8_rc10.ltx`). Hold
clean (+0.054 ns); the only setup violators are the long-standing WiFi TX-FIFO 24->6 MHz sync
path and an ILA probe-pipeline path (observation only). The Jr2 build does not define
`TURBO_FASTWRITE`; a Jr2 fast-write core is a separate decision.
