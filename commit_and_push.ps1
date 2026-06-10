Set-Location "C:\AFA_2027_QTM_Crypto"
git add -A
$msg = "Session update " + (Get-Date -Format "yyyy-MM-dd HH:mm")
git commit -m $msg
git push
Write-Host "`nDone: $msg"
Start-Sleep -Seconds 3
