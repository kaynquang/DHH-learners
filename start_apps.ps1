<#
Start the DHH-learners apps without going through .venv\Scripts\python.exe.

Why: on this machine Windows Smart App Control blocked that unsigned launcher ("An Application Control policy has blocked this file"), so
nothing could start from the venv. The interpreter the venv was made from still runs, and the venv's packages are plain files, so this script
runs that interpreter with the venv's site-packages on PYTHONPATH. If the venv launcher works again, the normal commands in HANDOFF.md work too.

Usage (PowerShell, from anywhere):
  .\start_apps.ps1              # learner app (8502) and Dev app (8501), opens the browser on the learner app
  .\start_apps.ps1 -Only learner|dev
  .\start_apps.ps1 -Test        # run the learner and GOP tests instead
  .\start_apps.ps1 -NoBrowser
Restarts a server that is already listening on the port (Streamlit keeps helper modules in memory).
#>
param([ValidateSet("both", "learner", "dev")] [string] $Only = "both", [switch] $Test, [switch] $NoBrowser)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root ".venv"
$home_ = ((Get-Content (Join-Path $venv "pyvenv.cfg")) | Where-Object { $_ -match "^home\s*=" }) -replace "^home\s*=\s*", ""
$python = Join-Path $home_.Trim() "python.exe"
$env:PYTHONPATH = Join-Path $venv "Lib\site-packages"
$appDir = Join-Path $root "app"

if ($Test) {
    Set-Location $root
    & $python -m pytest app\tests\test_learner_lessons.py app\tests\test_gop.py app\tests\test_stops.py app\tests\test_noise.py app\tests\test_stars.py app\tests\test_spectro.py app\tests\test_vtl.py app\tests\test_f_bars.py app\tests\test_f_meter.py app\tests\test_f_rumble.py app\tests\test_affricate_check.py -q -p no:cacheprovider --rootdir app
    exit $LASTEXITCODE
}

function Start-App($script, $port) {
    Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Milliseconds 700
    Start-Process -FilePath $python -ArgumentList "-m", "streamlit", "run", $script, "--server.port", $port, "--server.headless", "true" `
        -WorkingDirectory $appDir -WindowStyle Hidden
}

$apps = @()
if ($Only -ne "dev") { $apps += @{ script = "learner_app.py"; port = 8502; name = "learner" } }
if ($Only -ne "learner") { $apps += @{ script = "streamlit_app.py"; port = 8501; name = "dev" } }
foreach ($a in $apps) { Start-App $a.script $a.port }

foreach ($a in $apps) {
    $up = $false
    for ($i = 0; $i -lt 40 -and -not $up; $i++) {
        try { $up = (Invoke-WebRequest "http://localhost:$($a.port)/_stcore/health" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200 } catch { Start-Sleep -Milliseconds 500 }
    }
    "$($a.name) app, port $($a.port): $(if ($up) { 'up' } else { 'NOT up' })"
}
if (-not $NoBrowser -and $apps.Count -gt 0) { Start-Process "http://localhost:$($apps[0].port)/" }








