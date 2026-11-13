function Resolve-CompanionPython {
    param([string]$ProjectRoot)
    $candidates = @()
    if ($env:COMPANION_PYTHON) { $candidates += $env:COMPANION_PYTHON }
    $candidates += Join-Path $ProjectRoot '.venv/Scripts/python.exe'
    foreach ($name in @('python', 'python3')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command -and $command.Source -notlike '*\Microsoft\WindowsApps\*') {
            $candidates += $command.Source
        }
    }
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        $resolved = & $launcher.Source -3 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0) { $candidates += $resolved }
    }
    # Optional local override for computers using a portable Python installation.
    $localPath = Join-Path $ProjectRoot '.work/python-path.txt'
    if (Test-Path -LiteralPath $localPath) { $candidates += (Get-Content -LiteralPath $localPath -Raw).Trim() }
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
        & $candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { return $candidate }
    }
    throw 'Install Python 3.11+ and add it to PATH, or set COMPANION_PYTHON to python.exe.'
}
