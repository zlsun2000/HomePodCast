$ErrorActionPreference = 'Stop'
$testRoot = Join-Path $env:LOCALAPPDATA 'HomePodCastTest'
$runId = Get-Date -Format 'yyyyMMdd-HHmmss'
$report = Join-Path $testRoot "runtime-report-$runId.json"
$errorFile = Join-Path $testRoot "test-error-$runId.txt"
$deps = Join-Path $testRoot 'dependencies'
$python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
New-Item -ItemType Directory -Force -Path $testRoot | Out-Null
try {
    if (-not (Test-Path -LiteralPath $python)) {
        $installer = Join-Path $testRoot 'python-3.13.17-amd64.exe'
        $url = 'https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.exe'
        $sha256 = '5da012101ba2e17113a9a1cd901e9ce1441086f2b7ecb5de06ec94163899a190'
        Write-Host 'Downloading the official Python 3.13.17 installer...'
        Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
        if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash -ne $sha256) {
            throw 'Python installer SHA256 does not match the official release.'
        }
        Write-Host 'Installing Python for the current VM user...'
        $process = Start-Process -FilePath $installer -ArgumentList '/quiet', 'InstallAllUsers=0', 'Include_launcher=0', 'PrependPath=0', 'Include_test=0' -WindowStyle Hidden -Wait -PassThru
        if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $python)) {
            throw "Python installation failed (exit code $($process.ExitCode))."
        }
    }
    Write-Host 'Installing audio test dependencies into the VM test folder...'
    & $python -m pip install --disable-pip-version-check --target $deps -r (Join-Path $PSScriptRoot 'probe-requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed (exit code $LASTEXITCODE)." }
    $env:PYTHONPATH = $deps
    Write-Host 'Finding the HomePodCast Audio endpoint...'
    $json = & $python (Join-Path $PSScriptRoot 'probe_endpoint.py') --list
    if ($LASTEXITCODE -ne 0) { throw "Endpoint enumeration failed (exit code $LASTEXITCODE)." }
    $endpoints = @(ConvertFrom-Json -InputObject ($json -join "`n"))
    if ($endpoints.Count -ne 1 -or -not $endpoints[0].id) {
        throw "Expected exactly one HomePodCast Audio endpoint; found $($endpoints.Count). Run the probe with --list to inspect candidates."
    }
    Write-Host 'Testing PCM channels, volume and mute. Please wait...'
    & $python (Join-Path $PSScriptRoot 'probe_endpoint.py') --source-id $endpoints[0].id --output $report
    $probeExitCode = $LASTEXITCODE
    if (-not (Test-Path -LiteralPath $report)) { throw "The test did not produce a report (exit code $probeExitCode)." }
    Write-Host "Test finished (exit code $probeExitCode). Report: $report"
    Write-Host 'Please share the report contents with Codex.'
    Start-Process notepad.exe -ArgumentList ('"' + $report + '"')
} catch {
    $message = "Test preparation failed: $($_.Exception.Message)"
    Set-Content -LiteralPath $errorFile -Value $message -Encoding UTF8
    Write-Host $message -ForegroundColor Red
    Write-Host "Please share this error with Codex: $errorFile"
    Start-Process notepad.exe -ArgumentList ('"' + $errorFile + '"')
}
