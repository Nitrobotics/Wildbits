@echo off
REM Reprogram Jr2 flash sectors (FEU booter + f0) from platform-named blocks

python ../fnxmgr.py --port COM5 --flash-bulk bulk_jr2.csv
