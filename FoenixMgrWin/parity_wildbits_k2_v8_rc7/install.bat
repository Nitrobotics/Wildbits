@echo off
REM Reprogram flash sectors based on a CSV file

python ../fnxmgr.py --port COM10 --flash-bulk bulk.csv
