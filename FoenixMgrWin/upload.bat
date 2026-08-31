@echo off
REM Upload a binary file to the Foenix

if [%2%]==[] (
    python %FOENIXMGR%\fnxmgr.py --port COM5 --binary %1
) ELSE (
    python %FOENIXMGR%\fnxmgr.py --port COM5 --binary %1 --address %2
)
