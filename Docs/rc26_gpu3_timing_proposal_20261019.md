# rc26_gpu3 timing: where it fails, what was tried, what would close it for real (2026-10-19)

## Builds and experiments (same RTL features; no ECO, no hand placement, no new replication)
| Run | Change | Routed WNS |
|---|---|---|
| attempt 1 | as rc26_gpu2 + G1-G5, G7 | -0.191 (repair passes -0.076) |
| attempt 2 | X0Y0 exclusive to the SRAM-driving set | -0.776 (the 6809 core pushed away) |
| experiment A | X0Y0 shared + the SRAM pin mux (GavinDebug flash module) in pb_sram | -0.209 |
| experiment B | A + the SceneEngine off X0Y3 | worse before routing (stopped) |
| attempt 3 | A + SceneEngine area cut (898 flip-flops fewer, benches BAD 0) | -0.358: the sprite hit -> multiplier path (see the correction) |

The SceneEngine grew 3,527 LUTs / 2,067 flip-flops with G2b + G4 (out-of-context synthesis); that filled the GPU's
rows, which pushed CPU-side logic into the SRAM pads' region. G2b stays; the cut keeps its behavior bit-exact.

## Correction (2026-10-19): attempt 3's worst paths are the sprite engine, not the MMU
Attempt 3's own report (impl_1/CFP95139K2_Top_timing_summary_postroute_physopted.rpt, 08:43; audit in
wildbits-buildkit/notes/k2-gpu3-timing-audit-20261019.md): -0.358 on 16 endpoints of the sprite register BRAM ->
Sprite_State_Machine.v Y hit (Y1 = Y + size, the line compare, Line_Number_In_Sprite) -> the SpriteOffCalc DSP
input (100 Mhz, 6.97 ns data + 3.13 ns DSP setup), plus MEM_UBn_o -0.048 and MEM_A_o[8] -0.007. The same sprite
path was +0.040 in attempt 1. Three marginal groups, and placement picks which one fails worst in a run:
- sprite hit -> multiplier (100 Mhz): fix = a register between the hit/line-number logic and the DSP input (or the
  DSP's own input register), the sprite sequencing realigned by one cycle and checked against the sprite benches;
- the MMU's FramePortRAM (200 Mhz): item 1 below;
- the SRAM pins: item 2 below.

## The MMU and SRAM paths (attempts 1, 2 and experiment A)
- MMU `CPU_Addy_Registered` -> `FramePortRAM` (200 Mhz, one tick, 6-7 logic levels): -0.07 to -0.21
- SRAM strobe pins (`MEM_WEn_o`, `MEM_OEn_o`, `MEM_UBn_o`, `MEM_LBn_o`; 7.5/8.0 ns max delay): -0.02 to -0.10,
  some driven by `Read_Valid_reg_rep__N` - copies made by the `(* max_fanout = 8 *)` on `Read_Valid` (MMU line 163,
  since rc23): the replicated-select pattern behind the rc26 video corruption
- `DrawTime_Valid` -> line FIFO write enable (4.5 ns): -0.07; 6809 `InstPage2` -> MMU address register (6.0 ns): -0.15
rc26_gpu2 met by +0.004 on the same paths: they have always been at the edge.

## Proposal (MMU RTL; needs Roger's yes, the OS module check and fpga/check_scheduler_constraints.sh first)
1. FramePortRAM: its decode runs MMU block lookup -> the I/O page's sector decode (TinyVKY2K2_IO_Page0_Devices
   `IO_Sectored_CS_o`: sectors $C0-$C3, blocks 4/5) -> back into the MMU, all in the one tick CaptureTick -> +1. Its
   only use is AccessEnd at +2. Two honest ways to give it two ticks (the frame stays 15 ticks either way):
   a) capture it at +2 and set AccessEnd for a port-RAM frame at +3, with a two-tick multicycle bound from the
      registered CPU address / MMU registers to FramePortRAM only (true because the address is held from
      CaptureTick to the end of the frame) - an exception, so it is written out and checked against the scheduler;
   b) a register inside the decode (the sector select captured at +1, FramePortRAM at +2, AccessEnd at +3) - no
      exception, but the sector select is shared by every I/O device's decode, so only FramePortRAM's copy moves.
2. The SRAM control strobes from registers in the I/O blocks, constrained against the 200 Mhz launch (the open item
   in the core rules), and the `max_fanout` on `Read_Valid` removed: pin timing no longer depends on placement, and
   no copies of a select drive the SRAM pins.
