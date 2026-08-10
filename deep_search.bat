@echo off
echo This deep search needs Administrator rights for shadow copies and Recycle Bin.
echo If you did not right-click "Run as administrator", close and re-run that way.
echo.
echo This may take 15-30 minutes (it scans whole drives). It changes NOTHING.
echo.
pause
powershell -ExecutionPolicy Bypass -NoProfile -File "C:\AFA_2027_QTM_Crypto\deep_search.ps1"
pause
