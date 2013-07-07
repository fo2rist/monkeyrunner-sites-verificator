@echo off
%~dp0\compare.exe %1 %2 %3 %4 %5 %6 %7 %8 > TEMP_OUT.txt 2>&1
type TEMP_OUT.txt
del TEMP_OUT.txt