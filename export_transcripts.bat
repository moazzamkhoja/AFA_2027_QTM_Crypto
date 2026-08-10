@echo off
cd /d C:\AFA_2027_QTM_Crypto
echo Exporting Claude conversation transcripts (this may take a minute)...
echo.
echo Sweeping all known transcript locations...
python 04_code\export_ai_transcripts.py "%USERPROFILE%\.claude" "%APPDATA%\Claude" "%APPDATA%\AnthropicClaude" "%LOCALAPPDATA%\Claude" "%LOCALAPPDATA%\AnthropicClaude"
echo.
echo ===========================================
echo Done. Exported files are in:
echo   06_documentation\ai_transcripts\
dir /b 06_documentation\ai_transcripts | find /c ".md"
echo transcript files exported (count above).
echo.
echo Next: tell Claude "transcripts exported" and it
echo will rebuild the Volume II PDF.
echo ===========================================
pause
