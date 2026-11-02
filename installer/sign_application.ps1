param(
    [Parameter(Mandatory=$true)][string]$ApplicationPath,
    [Parameter(Mandatory=$true)][string]$CodeSigningThumbprint,
    [Parameter(Mandatory=$true)][string]$TimestampUrl,
    [Parameter(Mandatory=$true)][string]$SignToolPath
)
$ErrorActionPreference = 'Stop'
if ($CodeSigningThumbprint -notmatch '^[0-9a-fA-F]{40}$' -or $TimestampUrl -notmatch '^https?://[^\s"]+$') {
    throw 'Signing requires a 40-digit certificate thumbprint and an explicit HTTP(S) timestamp URL.'
}
$application = (Resolve-Path -LiteralPath $ApplicationPath).Path
& $SignToolPath sign /sha1 $CodeSigningThumbprint /fd SHA256 /tr $TimestampUrl /td SHA256 $application
if ($LASTEXITCODE -ne 0) { throw 'Application signing failed.' }
& $SignToolPath verify /pa $application
if ($LASTEXITCODE -ne 0) { throw 'Application signature verification failed.' }
