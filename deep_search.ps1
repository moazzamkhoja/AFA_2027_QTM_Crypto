# deep_search.ps1 -- exhaustive hunt for lost Claude Cowork transcripts (June 10-29, 2026)
# Run via deep_search.bat (as Administrator for shadow-copy and Recycle Bin access).
# Writes findings to deep_search_report.txt in the repo. READ-ONLY: changes nothing.

$ErrorActionPreference = 'SilentlyContinue'
$report = "C:\AFA_2027_QTM_Crypto\deep_search_report.txt"
"DEEP SEARCH REPORT  $(Get-Date)" | Out-File $report
$markers = 'QTM|AFA 2027|AFA_2027|conviction ratio|quantity theory'

function Log($s) { $s | Out-File $report -Append; Write-Host $s }

Log "`n=== 1. All .jsonl files on all fixed drives (any date) ==="
$drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Free -ne $null } | ForEach-Object { $_.Root }
foreach ($d in $drives) {
  Get-ChildItem -Path $d -Recurse -Filter *.jsonl -Force -File |
    ForEach-Object { Log ("  {0}  {1:N0} bytes  created {2}  modified {3}" -f $_.FullName, $_.Length, $_.CreationTime, $_.LastWriteTime) }
}

Log "`n=== 2. Project markers inside Claude app internal storage (LevelDB/IndexedDB/logs/cache) ==="
$appdirs = @("$env:APPDATA\Claude", "$env:LOCALAPPDATA\Claude", "$env:APPDATA\AnthropicClaude", "$env:LOCALAPPDATA\AnthropicClaude", "$env:USERPROFILE\.claude")
foreach ($dir in $appdirs) {
  if (-not (Test-Path $dir)) { continue }
  Log "  scanning $dir ..."
  Get-ChildItem -Path $dir -Recurse -Force -File -Include *.ldb,*.log,*.sqlite,*.db,*.json,*.bin |
    ForEach-Object {
      if (Select-String -Path $_.FullName -Pattern $markers -Quiet) {
        Log ("  MATCH: {0}  {1:N0} bytes  modified {2}" -f $_.FullName, $_.Length, $_.LastWriteTime)
      }
    }
}

Log "`n=== 3. Recycle Bin ==="
foreach ($d in $drives) {
  Get-ChildItem -Path "$d`$Recycle.Bin" -Recurse -Force -File |
    Where-Object { $_.Extension -in '.jsonl','.json','.md' -or $_.Length -gt 10000 } |
    Select-Object -First 200 |
    ForEach-Object { Log ("  {0}  {1:N0} bytes  deleted-file modified {2}" -f $_.FullName, $_.Length, $_.LastWriteTime) }
}

Log "`n=== 4. Volume Shadow Copies (restore points that may hold June files) ==="
$shadows = vssadmin list shadows 2>&1
Log ($shadows | Out-String)

Log "`n=== 5. Windows File History / backup locations ==="
foreach ($p in @("$env:USERPROFILE\OneDrive", "D:\FileHistory", "E:\FileHistory")) {
  if (Test-Path $p) {
    Get-ChildItem -Path $p -Recurse -Filter *.jsonl -Force -File |
      ForEach-Object { Log ("  {0}  modified {1}" -f $_.FullName, $_.LastWriteTime) }
  }
}

Log "`n=== 6. Temp folders ==="
foreach ($p in @($env:TEMP, "C:\Windows\Temp")) {
  Get-ChildItem -Path $p -Recurse -Force -File -Include *.jsonl |
    ForEach-Object { Log ("  {0}  modified {1}" -f $_.FullName, $_.LastWriteTime) }
}

Log "`n=== 7. Any file on C: containing project markers, created in June 2026 ==="
Get-ChildItem -Path "C:\Users" -Recurse -Force -File -Include *.json,*.jsonl,*.txt,*.log |
  Where-Object { $_.CreationTime -ge '2026-06-01' -and $_.CreationTime -le '2026-06-30' -and $_.Length -gt 5000 -and $_.FullName -notlike '*AFA_2027_QTM_Crypto*' } |
  ForEach-Object {
    if (Select-String -Path $_.FullName -Pattern $markers -Quiet) {
      Log ("  MATCH: {0}  {1:N0} bytes  created {2}" -f $_.FullName, $_.Length, $_.CreationTime)
    }
  }

Log "`nDONE. Report saved to $report"
Write-Host "`nFinished. Tell Claude: 'deep search done'."
