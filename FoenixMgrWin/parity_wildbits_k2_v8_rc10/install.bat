@echo off
REM Reprogram the K2 flash: FEU /f0 blocks (f0-f4) + booter blocks (booter_0-2)
REM Run from inside this folder. K2 FoenixMgr debug port = COM9.

python ../fnxmgr.py --port COM9 --flash-bulk bulk.csv
