@echo off
cd /d C:\AFA_2027_QTM_Crypto
if exist .git\index.lock del .git\index.lock
git add -A
git commit -m "Session update"
git push
echo.
echo ===========================
echo Done. Check output above.
echo ===========================
pause
