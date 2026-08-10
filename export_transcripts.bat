@echo off
cd /d C:\AFA_2027_QTM_Crypto
echo Exporting Claude conversation transcripts (this may take a minute)...
echo.
python 04_code\export_ai_transcripts.py "%USERPROFILE%\.claude\projects" "%APPDATA%\Claude\local-agent-mode-sessions"
echo.
echo ===========================================
echo Done. Exported files are in:
echo   06_documentation\ai_transcripts\
dir /b 06_documentation\ai_transcripts | find /c ".md"
echo transcript files exported (count above).
echo.
echo Next: tell Claude "transcripts exported" and it
echo will build the Volume II PDF and finish the package.
echo ===========================================
pause
