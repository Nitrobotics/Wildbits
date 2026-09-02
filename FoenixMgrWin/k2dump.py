#!/usr/bin/env python3
"""k2dump.py - dump the WildBits' entire RAM over the FPGA debug port.

Works even when the 6809 is wedged (the debug engine is CPU-independent).
NEVER read more than 0x64 bytes per transfer: a larger read wedges the FPGA
debug engine until the machine is POWER-CYCLED (wbreset does not revive it).
memory directly, and leaving debug mode RESETS the machine afterwards.

usage: python k2dump.py OUTFILE [--port COM9] [--size 0x80000] [--chunk 0x40]
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "FoenixMgr"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import foenix

ap = argparse.ArgumentParser()
ap.add_argument("outfile")
ap.add_argument("--port", default="COM9")
ap.add_argument("--size", default="0x80000", help="bytes to read (default 512K)")
ap.add_argument("--chunk", default="0x40", help="bytes per transfer; HARD LIMIT 0x64 or the FPGA debug engine wedges until power-cycle")
ap.add_argument("--start", default="0x0")
a = ap.parse_args()
size, chunk, start = int(a.size, 16), int(a.chunk, 16), int(a.start, 16)
if chunk > 0x64:
    raise SystemExit("chunk > 0x64 wedges the K2 debug engine (power-cycle to recover); refusing")

dev = foenix.FoenixDebugPort()
dev.open(a.port)
t0 = time.time()
try:
    try:
        dev.connection.serial_port.reset_input_buffer()   # drop stale bytes from an aborted transfer
    except Exception:
        pass
    dev.enter_debug()
    with open(a.outfile, "wb") as f:
        addr = start
        while addr < start + size:
            n = min(chunk, start + size - addr)
            data = dev.read_block(addr, n)
            if len(data) != n:
                raise SystemExit(f"short read at {addr:06X}: got {len(data)} of {n}")
            f.write(data)
            addr += n
            sys.stdout.write(f"\r{addr - start:06X}/{size:06X}")
            sys.stdout.flush()
finally:
    try:
        dev.exit_debug()   # NOTE: this resets the machine
    finally:
        dev.close()
print(f"\nwrote {size} bytes to {a.outfile} in {time.time() - t0:.1f}s (machine reset)")
