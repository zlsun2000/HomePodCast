$ErrorActionPreference = 'Stop'
$testRoot = Join-Path $env:LOCALAPPDATA 'HomePodCastTest'
$python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
$runId = Get-Date -Format 'yyyyMMdd-HHmmss'
$existing = @(Get-ChildItem -Path $testRoot -Filter 'homepod-dependencies-*' -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending | Select-Object -First 1)
$deps = if ($existing.Count) { $existing[0].FullName } else { Join-Path $testRoot "homepod-dependencies-$runId" }
$report = Join-Path $testRoot "homepod-report-$runId.json"
$errorFile = Join-Path $testRoot "homepod-error-$runId.txt"
try {
    if (-not (Test-Path -LiteralPath $python)) { throw 'Run the audio probe first to install the test runtime.' }
    if (-not $existing.Count) {
        Write-Host 'Installing isolated, version-checked audio and streaming dependencies...'
        & $python -m pip install --disable-pip-version-check --target $deps 'pyatv==0.18.0' 'srptools==1.0.1' 'numpy==2.5.3' 'SoundCard==0.4.6' 'pycaw==20260927' 'comtypes==1.4.17'
        if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed (exit code $LASTEXITCODE)." }
    } else {
        Write-Host 'Reusing the isolated HomePod test dependencies.'
    }
    $env:PYTHONPATH = "$PSScriptRoot;$deps"
    & $python -c "import inspect; from srptools import SRPClientSession; inspect.signature(SRPClientSession).bind(object(), 'test'); print('SRP compatibility check passed')"
    if ($LASTEXITCODE -ne 0) { throw 'SRP dependency compatibility check failed.' }
    Write-Host 'Connecting to HomePod. Listen for two tones with a silent interval.'
    & $python (Join-Path $PSScriptRoot 'vm_homepod_test.py') $report
    if (-not (Test-Path -LiteralPath $report)) { throw "No report was produced (exit code $LASTEXITCODE)." }
    Write-Host 'Please share the report and say whether you heard both tones and silence between them.'
    Start-Process notepad.exe -ArgumentList ('"' + $report + '"')
} catch {
    $message = "Test preparation failed: $($_.Exception.Message)"
    Set-Content -LiteralPath $errorFile -Value $message -Encoding UTF8
    Write-Host $message -ForegroundColor Red
    Start-Process notepad.exe -ArgumentList ('"' + $errorFile + '"')
}
