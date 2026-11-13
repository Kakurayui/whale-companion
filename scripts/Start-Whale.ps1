param([ValidateRange(1024,65535)][int]$Port = 8765, [switch]$NoDesktop)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$workPath = Join-Path $projectRoot '.work'
New-Item -ItemType Directory -Path $workPath -Force | Out-Null
. (Join-Path $PSScriptRoot 'Resolve-Python.ps1')
$pythonPath = Resolve-CompanionPython -ProjectRoot $projectRoot
$appUrl = 'http://127.0.0.1:' + $Port
$serverPath = Join-Path $projectRoot 'server.py'
$running = $false
$status = $null
try { $status = Invoke-RestMethod -Uri ($appUrl + '/api/status') -TimeoutSec 2 } catch {}
if ($status.character_id -eq 'feiyu') { $running = $true }
elseif ($status) {
    # Only replace this project's recorded legacy backend; never stop an unrelated process.
    $pidPath = Join-Path $workPath 'server.pid'
    if (-not (Test-Path -LiteralPath $pidPath)) { throw 'Port is occupied. Close the other app or use -Port 8766.' }
    $serverPid = [int](Get-Content -LiteralPath $pidPath)
    $oldProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$serverPid"
    if (-not $oldProcess -or -not $oldProcess.CommandLine.Contains($serverPath)) {
        throw 'Port is occupied by an unrecognized process. Use -Port 8766.'
    }
    [System.Diagnostics.Process]::GetProcessById($serverPid).Kill()
    Start-Sleep -Milliseconds 300
}
if (-not $running) {
    $serverArguments = @('-u', '-m', 'backend.server', '--port', $Port, '--character', 'feiyu')
    $process = Start-Process -FilePath $pythonPath -ArgumentList $serverArguments -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $workPath 'server.log') -RedirectStandardError (Join-Path $workPath 'server-errors.log')
    $process.Id | Set-Content -LiteralPath (Join-Path $workPath 'server.pid')
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 300
        try {
            $status = Invoke-RestMethod -Uri ($appUrl + '/api/status') -TimeoutSec 2
            if ($status.character_id -eq 'feiyu') { $running = $true; break }
        } catch {}
        if ($process.HasExited) { throw 'Backend stopped. Check .work/server-errors.log.' }
    }
    if (-not $running) { throw 'Backend startup timed out.' }
}
# Also restore the web preview when launching without the native pet.
$requiredAssets = @('desktop/skins/feiyu-02/manifest.json', 'desktop/skins/feiyu-03/manifest.json', 'desktop/icon.png', 'web/feiyu/pet.png')
$missingAssets = $requiredAssets | Where-Object { -not (Test-Path -LiteralPath (Join-Path $projectRoot $_)) }
if ($missingAssets) {
    & $pythonPath (Join-Path $projectRoot 'tools/setup_pet_assets.py')
    if ($LASTEXITCODE -ne 0) { throw 'Asset setup failed.' }
}
if (-not $NoDesktop) {
    $desktopPath = Join-Path $projectRoot 'desktop'
    $electronPath = Join-Path $desktopPath 'node_modules/electron/dist/electron.exe'
    if (-not (Test-Path -LiteralPath $electronPath)) {
        $env:ELECTRON_CACHE = Join-Path $workPath 'electron-cache'
        $env:electron_config_cache = Join-Path $workPath 'electron-cache'
        Push-Location $desktopPath
        try {
            & npm.cmd ci --cache (Join-Path $workPath 'npm-cache') --no-audit --no-fund
            if ($LASTEXITCODE -ne 0) { throw 'npm install failed. Check that Node.js is installed.' }
            & node node_modules/electron/install.js
            if ($LASTEXITCODE -ne 0) { throw 'Electron runtime download failed.' }
            # Electron 45 verifies that its sandbox can read its own binaries on Windows.
            & icacls (Join-Path $desktopPath 'node_modules/electron/dist') /grant '*S-1-15-2-1:(OI)(CI)(RX)' | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Electron runtime sandbox access could not be prepared.' }
        } finally { Pop-Location }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $desktopPath 'dist/renderer.js'))) {
        Push-Location $desktopPath
        try {
            & npm.cmd run build --cache (Join-Path $workPath 'npm-cache')
            if ($LASTEXITCODE -ne 0) { throw 'Desktop build failed.' }
        } finally { Pop-Location }
    }
    $env:COMPANION_PORT = [string]$Port
    # Electron's normal sandbox stays enabled. Its data directory is project-local.
    Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
    $desktopProcess = Start-Process -FilePath $electronPath -ArgumentList ('"' + $desktopPath + '"') -WorkingDirectory $desktopPath -WindowStyle Hidden -PassThru
    $desktopProcess.Id | Set-Content -LiteralPath (Join-Path $workPath 'desktop.pid')
    Start-Sleep -Milliseconds 1200
    $desktopProcess.Refresh()
    if ($desktopProcess.HasExited -and $desktopProcess.ExitCode -ne 0) { throw 'Desktop launch failed. See README.md troubleshooting.' }
}
Write-Output ('Whale Companion is ready at ' + $appUrl)
