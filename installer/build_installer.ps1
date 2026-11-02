param(
    [Parameter(Mandatory=$true)][string]$CableZip,
    [string]$IsccPath = '',
    [string]$SignToolPath = '',
    [string]$ApplicationPath = '',
    [string]$CodeSigningThumbprint = '',
    [string]$TimestampUrl = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$zipHash = 'B950E39F01AF1D04EA623C8F6D8EB9B6EA5C477C637295FABF20631C85116BFB'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $CableZip).Hash -ne $zipHash) {
    throw 'VB-CABLE archive hash does not match the pinned official Pack45.'
}
if (-not $IsccPath) {
    $localIscc = Join-Path $root '.build-tools\inno\ISCC.exe'
    $runnerIscc = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
    if (Test-Path -LiteralPath $localIscc) { $IsccPath = $localIscc }
    elseif (Test-Path -LiteralPath $runnerIscc) { $IsccPath = $runnerIscc }
    else { $IsccPath = (Get-Command ISCC.exe -ErrorAction Stop).Source }
}
if (-not $SignToolPath) {
    $sdkBin = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'
    $signTool = Get-ChildItem -Path $sdkBin -Filter signtool.exe -Recurse -ErrorAction Stop |
        Where-Object { $_.FullName -match '\\x64\\signtool\.exe$' } |
        Sort-Object FullName -Descending | Select-Object -First 1
    if (-not $signTool) { throw 'Windows SDK x64 signtool.exe is required.' }
    $SignToolPath = $signTool.FullName
}
$cableDir = Join-Path $root ('build\vbcable-pack45-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $cableDir | Out-Null
Expand-Archive -LiteralPath $CableZip -DestinationPath $cableDir -Force
$vendorSetup = Join-Path $cableDir 'VBCABLE_Setup_x64.exe'
$catalog = Join-Path $cableDir 'vbaudio_cable64_win10.cat'
foreach ($file in @($vendorSetup, $catalog)) {
    $signature = Get-AuthenticodeSignature -LiteralPath $file
    if ($signature.Status -ne 'Valid') { throw "Invalid signature: $file" }
}
if ((Get-AuthenticodeSignature -LiteralPath $vendorSetup).SignerCertificate.Subject -notmatch 'BUREL VINCENT') {
    throw 'Unexpected VB-CABLE installer publisher.'
}
if ((Get-AuthenticodeSignature -LiteralPath $catalog).SignerCertificate.Subject -notmatch 'Microsoft Windows Hardware Compatibility Publisher') {
    throw 'Unexpected VB-CABLE catalog publisher.'
}
foreach ($name in @('vbMmeCable64_win10.inf','vbaudio_cable64_win10.sys','vbaudio_cable64arm_win10.sys')) {
    & $SignToolPath verify /pa /c $catalog (Join-Path $cableDir $name)
    if ($LASTEXITCODE -ne 0) { throw "Catalog verification failed: $name" }
}
$application = if ($ApplicationPath) { (Resolve-Path -LiteralPath $ApplicationPath).Path } else { Join-Path $root 'dist\HomePodCast.exe' }
if (-not (Test-Path -LiteralPath $application)) { throw 'Build dist\HomePodCast.exe first.' }
$version = (Select-String -LiteralPath (Join-Path $root 'app.py') -Pattern '^VERSION = "(.+)"').Matches[0].Groups[1].Value
$compilerArgs = @("/DAppVersion=$version", "/DCableDir=$cableDir", "/DAppExe=$application")
if ($CodeSigningThumbprint) {
    if ($CodeSigningThumbprint -notmatch '^[0-9a-fA-F]{40}$' -or $TimestampUrl -notmatch '^https?://[^\s"]+$') {
        throw 'Signing requires a 40-digit certificate thumbprint and an explicit HTTP(S) timestamp URL.'
    }
    & $SignToolPath verify /pa $application
    if ($LASTEXITCODE -ne 0) { throw 'The application must be signed before it is packaged.' }
    $compilerArgs += '/DSignedBuild=1'
    # Inno Setup substitutes $q and $f after receiving this single argument.
    $compilerArgs += ('/SHomePodCastSigner=$q' + $SignToolPath + '$q sign /sha1 ' + $CodeSigningThumbprint + ' /fd SHA256 /tr ' + $TimestampUrl + ' /td SHA256 $f')
}
& $IsccPath @compilerArgs (Join-Path $PSScriptRoot 'HomePodCast.iss')
if ($LASTEXITCODE -ne 0) { throw "Installer compiler failed: $LASTEXITCODE" }
if ($CodeSigningThumbprint) {
    & $SignToolPath verify /pa (Join-Path $root 'dist\HomePodCast-Setup.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Signed installer verification failed.' }
}
Write-Host 'Installer created:' (Join-Path $root 'dist\HomePodCast-Setup.exe')
