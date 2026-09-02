@echo off
REM Reprogram the Jr2 flash: FEU /f0 blocks (f0-f4) + booter blocks (booter_0-2)
REM Run from inside this folder. Jr2 FoenixMgr debug port = COM5.

python ..nxmgr.py --port COM5 --flash-bulk bulk.csv
