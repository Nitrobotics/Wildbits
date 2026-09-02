@echo off
REM usage: k2dump {outfile} [port]   -- dumps all 512K of RAM, then RESETS the machine
if [%2]==[] (set P=COM9) else (set P=%2)
python "%~dp0k2dump.py" %1 --port %P%
