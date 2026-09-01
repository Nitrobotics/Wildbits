# WildBits WizFi Driver Hardening — Remote Shell over /wz0–/wz3

**Date:** 2026-08-31 (branch `wb/wizfi_tx_packets`)
**File changed:** `level1/wildbits/modules/wizfi.asm`
**Field verdict:** no dropped keystrokes and no protocol leaks after
heavy interactive + bulk (`dir` loop) testing over a PuTTY session.

## Background

The 2026-08-26 rework removed the Timer0 machinery and left packet-mode
TX kicking a CIPSEND on every CR/LF — one packet per output line, and
interactive echo traffic produced tiny packets with no coalescing. The
goal was to re-employ the old Timer0 behavior (dump the TX buffer
periodically so packet sizes track shell activity) **without giving
Timer0 back**. The batching itself was straightforward; making it
survive a real remote shell exposed four stacked defects, each found by
field symptoms and fixed in sequence.

## The batching design (what Timer0 became)

A repeating 1-tick **F$VIRQ** on the 60Hz clock (installed vrn.asm
style: an F$IRQ entry polls the packet's own `Vi.Stat` byte; `TickSvc`
clears `Vi.IFlag`, keeping the $80 repeat marker) drains the output
ring. Socket bytes on `/wz0–/wz3` coalesce for up to 16.7ms and leave
as **one CIPSEND sized by activity**. `Write`'s packet-mode per-CR kick
is replaced by a nearly-full early flush (`TXTHRESH` = 192 of the
256-byte ring) so bulk streams aren't throttled to tick pace. Raw
`/wz` (the AT command channel) keeps its per-byte drain untouched.
Install failure degrades soft — threshold kick and the WizFi-edge drain
still flush; no interrupt is load-bearing. `Term` removes the VIRQ and
both poll-table entries (IOMan removal matches on the static pointer,
one entry per call).

## Root cause 1: handshake loops destroyed interleaved receive

**Symptom:** shell missed typed characters; typing had to be slow.

The CIPSEND handshake's `"> "` prompt-wait and "SEND OK" purge popped
the RX FIFO indiscriminately — any `+IPD` keystroke data arriving
during a handshake was consumed as if it were response text. The flaw
predates the batching, but per-CR kicks only handshook at line ends;
the tick flush handshakes *while the user is typing*, sixty times a
second.

**Fix — `HsPop`:** every byte popped during a handshake runs through
`PktByte` (the existing +IPD state machine) first. Payload bytes are
parked for their socket; header-in-progress bytes are consumed; only
genuine response noise reaches the prompt/purge matchers.

## Root cause 2: the parking lot was one byte deep

**Symptom:** still missing characters; output corrupted during `dir`.

`ParkOther` parked a **single byte** per channel (`vpr_data`) — every
multi-byte `+IPD` run arriving mid-handshake overwrote the slot byte by
byte, keeping only the last. Worse, `GetVpPtr` used a 4-byte stride for
5-byte slot records, so adjacent channels' slots **overlapped by one
byte**. And the documented gap remained: direct-pop readers never
retrieved parked bytes at all.

**Fix — per-channel receive queues:** the `D.WZStatTbl` page now holds
8-byte slot records (stride fixed, no overlap) plus four **32-byte
rings** (`$20 + chan*32`; depth is one equate, `vpq_size`). `ParkOther`
enqueues (overwriting oldest on overflow); `Read` **dequeues before
polling the FIFO** — which also closes the old multi-socket hand-off
gap. `vpr_stat` bit 7 now means "queue non-empty" and stays compatible
with the SS.Ready pollers.

## Root cause 3: the tick flush launched into incoming traffic

**Symptom:** unnecessary handshake/traffic collisions at the worst
moments.

**Fix:** `TickSvc` checks `RxFCheck` and defers its flush one tick when
inbound bytes are waiting. With `HsPop`, collisions are *safe*; this
makes them *rare*. `Write`'s threshold kick still bounds output latency
when the ring fills.

## Root cause 4: prompt timeout sent payload blind — stream desync

**Symptom (rare, under sustained bulk output):** the literal text
`AT+CIPSEND=0,1` printed at the remote terminal; truncated `dir`
output.

Under load the module sometimes answers a CIPSEND with `busy p...`
instead of `"> "`. The old path "no prompt: send anyway" pushed payload
into **command mode**, desynchronizing the handshake stream — a later
command line then rode out inside a stale `">"` data-collection phase
and appeared on the wire as socket data.

**Fix — abort and retry:** if the prompt never arrives, the burst is
**aborted**. `OutPktPickup` has not advanced at that point, so the ring
is intact and the identical bytes retry cleanly on the next tick or
threshold kick. A busy module now costs one invisible tick instead of a
desync cascade.

## Module CRC lineage (`ident wizfi`)

| CRC | Revision |
|---|---|
| `$A36AC6` | plain post-Timer0 driver (main) |
| `$B25259` | + tick batching |
| `$7387BB` | + HsPop, receive queues, stride fix, Read dequeue |
| `$E1BEA2` | + abort-on-no-prompt — **field-verified good** |

## Notes for future work

- `vpq_size equ 32` is the tuning knob if extreme input bursts during
  heavy output ever shed oldest bytes; the stat page has room for 64.
- The handshake waits still run IRQ-masked (bounded, ~hundreds of ms
  worst case per timeout). If bulk throughput needs another step,
  moving the prompt/purge waits out of masked context is the next
  lever.
- Never level-trigger on this interrupt controller (poller poisoning);
  Timer0 remains free for other uses.
- lwasm gotcha: the `os9` macro breaks `@`-local label scope — loop
  labels that cross an `os9` call must be global.
