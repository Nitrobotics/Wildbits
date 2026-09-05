@echo off
REM Reprogram flash sectors based on a CSV file

python fnxmgr.py --flash-bulk %1
