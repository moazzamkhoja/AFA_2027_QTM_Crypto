@echo off
cd /d C:\AFA_2027_QTM_Crypto
echo Exporting Claude conversation transcripts (this may take a minute)...
echo.
echo [1/2] Sweeping all transcript locations INCLUDING the Store-app package tree...
python 04_code\export_ai_transcripts.py "%USERPROFILE%\.claude" "%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\local-agent-mode-sessions" "%APPDATA%\Claude" "%LOCALAPPDATA%\Claude"
echo.
echo [2/2] Copying raw June files for inspection (gitignored folder)...
if not exist 06_documentation\ai_transcripts_raw mkdir 06_documentation\ai_transcripts_raw
copy /y "%USERPROFILE%\.claude\projects\C--Users-zdd251\bee03d1d-8b6c-43b6-aa09-c9079926c952.jsonl" 06_documentation\ai_transcripts_raw\ >nul
copy /y "%USERPROFILE%\.claude\projects\C--Users-zdd251\fe14d0f8-b7e0-477c-a64b-d4117b529302.jsonl" 06_documentation\ai_transcripts_raw\ >nul
copy /y "%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\local-agent-mode-sessions\20e3184b-b6fa-4097-9251-5a37be8d056e\85dd0e98-0394-46e0-9e71-e1da00099b50\local_49e8b9dd-02e1-4d8c-b13f-8a451b3b560c\audit.jsonl" 06_documentation\ai_transcripts_raw\audit_local_49e8b9dd.jsonl >nul
dir 06_documentation\ai_transcripts_raw
echo.
echo ===========================================
echo Done. Exported files are in:
echo   06_documentation\ai_transcripts\
dir /b 06_documentation\ai_transcripts | find /c ".md"
echo transcript files exported (count above).
echo.
echo Next: tell Claude "transcripts exported" and it
echo will inspect the June files and rebuild Volume II.
echo ===========================================
pause
