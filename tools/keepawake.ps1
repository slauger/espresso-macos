# keepawake.ps1 - Prevents idle screen lock inside a Windows (Citrix) session
# by periodically sending the harmless F15 key, which resets the input idle timer.
#
# Usage (inside the Citrix session):
#   powershell -ExecutionPolicy Bypass -File keepawake.ps1
#   powershell -ExecutionPolicy Bypass -File keepawake.ps1 -IntervalSeconds 120
#
# Stop with Ctrl+C.

param(
    [int]$IntervalSeconds = 60
)

# Fail early with a clear message if the environment is locked down
if ($ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage') {
    Write-Error "PowerShell is running in $($ExecutionContext.SessionState.LanguageMode) mode - COM objects are blocked, this script cannot work here."
    exit 1
}

try {
    $wsh = New-Object -ComObject WScript.Shell
} catch {
    Write-Error "Could not create WScript.Shell COM object (blocked by policy?): $_"
    exit 1
}

Write-Host "keepawake started - sending F15 every $IntervalSeconds seconds. Press Ctrl+C to stop."

$count = 0
while ($true) {
    $wsh.SendKeys('{F15}')
    $count++
    Write-Host ("[{0}] keypress #{1} sent" -f (Get-Date -Format 'HH:mm:ss'), $count)
    Start-Sleep -Seconds $IntervalSeconds
}
