@echo off
REM Reprogram flash sectors based on a CSV file

REM python fnxmgr.py --port COM5 --stop
python fnxmgr.py --port COM5 --flash-bulk diag\bulk.csv
REM python fnxmgr.py --port COM5 --start
python fnxmgr.py --port COM5 --boot FLASH



