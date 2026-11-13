param([ValidateRange(1024,65535)][int]$Port = 8766, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'Resolve-Python.ps1')
$pythonPath = Resolve-CompanionPython -ProjectRoot $projectRoot
$workPath = Join-Path $projectRoot '.work'
New-Item -ItemType Directory -Path $workPath -Force | Out-Null
$appUrl = 'http://127.0.0.1:' + $Port
$running = $false
try {
    $status = Invoke-RestMethod -Uri ($appUrl + '/api/status') -TimeoutSec 2
    if ($status.character.name -eq 'Mira') { $running = $true }
} catch { }
if (-not $running) {
    $serverArguments = @('-u', '-m', 'backend.server', '--port', $Port, '--character', 'mira')
    $process = Start-Process -FilePath $pythonPath -ArgumentList $serverArguments -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $workPath 'mira-server.log') -RedirectStandardError (Join-Path $workPath 'mira-server-errors.log')
    $process.Id | Set-Content -LiteralPath (Join-Path $workPath 'mira-server.pid')
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 300
        try {
            $status = Invoke-RestMethod -Uri ($appUrl + '/api/status') -TimeoutSec 2
            if ($status.character.name -eq 'Mira') { $running = $true; break }
        } catch { }
        if ($process.HasExited) { throw 'The server stopped. Check .work/mira-server-errors.log.' }
    }
    if (-not $running) { throw 'Startup timed out. Check .work/mira-server-errors.log.' }
}
Write-Output ('Lantern & Leaf is running at ' + $appUrl)
if (-not $NoBrowser) { Start-Process $appUrl }
