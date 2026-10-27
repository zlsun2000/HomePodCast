param([string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'driver-artifacts'))
$ErrorActionPreference = 'Stop'
$manifestPath = Join-Path $OutputRoot 'build-manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -AsHashtable
if ($manifest.artifactKind -ne 'homepodcast-audio-prototype' -or -not $manifest.buildSucceeded -or -not $manifest.infVerified) {
    throw 'A compiled and INF-verified prototype artifact is required.'
}
$manifest.packageSucceeded = $false
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8
$binaryDir = Join-Path $OutputRoot "audio/sysvad/TabletAudioSample/x64/$($manifest.configuration)"
$packages = Join-Path (Split-Path -Parent $PSScriptRoot) '.driver-source/packages'
& (Join-Path $PSScriptRoot 'sign_test_package.ps1') -Binary (Join-Path $binaryDir 'HomePodCastAudio.sys') `
    -Inf (Join-Path $binaryDir 'HomePodCastAudio.inf') -PackageRoot (Join-Path $OutputRoot 'test-package') `
    -Packages $packages -KitVersion $manifest.kitVersion
$manifest.signing = 'ephemeral-development-test'
$manifest.packageSucceeded = $true
$manifest.files = @(Get-ChildItem $OutputRoot -Recurse -File | Where-Object Extension -In '.sys','.inf','.cat','.dll','.cer' |
    ForEach-Object { @{ path = [IO.Path]::GetRelativePath($OutputRoot, $_.FullName); sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash } })
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8
