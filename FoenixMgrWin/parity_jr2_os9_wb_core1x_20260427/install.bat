@echo off
REM Reprogram flash sectors based on a CSV file

python ../fnxmgr.py --port COM4 --flash-bulk bulk.csv
cd ../..
