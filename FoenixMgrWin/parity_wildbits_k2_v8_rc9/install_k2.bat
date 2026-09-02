@echo off
REM Reprogram K2 flash sectors (FEU booter + f0) from platform-named blocks

python ../fnxmgr.py --port COM9 --flash-bulk bulk_k2.csv
