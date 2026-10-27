param(
    [Parameter(Mandatory)][string]$Binary,
    [Parameter(Mandatory)][string]$Inf,
    [Parameter(Mandatory)][string]$PackageRoot,
    [Parameter(Mandatory)][string]$Packages,
    [Parameter(Mandatory)][string]$KitVersion
)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted') {
    throw 'Test package signing is restricted to an ephemeral GitHub-hosted runner.'
}
if (Test-Path -LiteralPath $PackageRoot) { throw 'Use a fresh package output directory.' }
$tools = Join-Path $Packages "Microsoft.Windows.WDK.x64.$KitVersion/c/bin/10.0.28000.0"
$sdk = Join-Path $Packages "Microsoft.Windows.SDK.CPP.$KitVersion/c/bin/10.0.28000.0/x64"
$signtool = Join-Path $sdk 'signtool.exe'
$inf2cat = Join-Path $tools 'x86/Inf2Cat.exe'
foreach ($path in @($Binary, $Inf, $signtool, $inf2cat)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required file not found: $path" }
}
function Invoke-SigningTool([string]$Program, [string[]]$Arguments) {
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo.FileName = $Program
    $process.StartInfo.UseShellExecute = $false
    $process.StartInfo.CreateNoWindow = $true
    $process.StartInfo.RedirectStandardOutput = $true
    $process.StartInfo.RedirectStandardError = $true
    foreach ($argument in $Arguments) { $process.StartInfo.ArgumentList.Add($argument) }
    try {
        if (-not $process.Start()) { throw "Cannot start signing tool: $Program" }
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(120000)) {
            $process.Kill($true)
            $process.WaitForExit()
            Write-Output $stdout.GetAwaiter().GetResult()
            Write-Output $stderr.GetAwaiter().GetResult()
            throw "Signing/verification tool timed out after 120 seconds: $Program"
        }
        Write-Output $stdout.GetAwaiter().GetResult()
        Write-Output $stderr.GetAwaiter().GetResult()
        if ($process.ExitCode -ne 0) { throw "Signing/verification tool failed: $Program ($($process.ExitCode))" }
    }
    finally { $process.Dispose() }
}
New-Item -Path $PackageRoot -ItemType Directory | Out-Null
$certificate = $null
$rootCertificateInstalled = $false
try {
    $certificate = New-SelfSignedCertificate -Type CodeSigningCert -Subject 'CN=HomePodCast Development Test' `
        -CertStoreLocation 'Cert:\CurrentUser\My' -KeyAlgorithm RSA -KeyLength 2048 `
        -KeyExportPolicy NonExportable -HashAlgorithm SHA256 -NotAfter (Get-Date).AddMonths(3)
    $publicCert = Join-Path $PackageRoot 'HomePodCast-Development.cer'
    Export-Certificate -Cert $certificate -FilePath $publicCert | Out-Null
    # Only public certificate material enters the artifact. Private key remains
    # non-exportable in this ephemeral runner's store and is removed below.
    Invoke-SigningTool $signtool @('sign', '/v', '/s', 'My', '/sha1', $certificate.Thumbprint,
        '/fd', 'SHA256', '/ph', $Binary)
    Copy-Item -LiteralPath $Binary -Destination (Join-Path $PackageRoot 'HomePodCastAudio.sys')
    Copy-Item -LiteralPath $Inf -Destination (Join-Path $PackageRoot 'HomePodCastAudio.inf')
    Invoke-SigningTool $inf2cat @("/driver:$PackageRoot", '/os:10_NI_X64,10_GE_X64', '/uselocaltime', '/verbose')
    $catalog = Join-Path $PackageRoot 'HomePodCastAudio.cat'
    if (-not (Test-Path -LiteralPath $catalog)) { throw 'Catalog generation produced no catalog' }
    Invoke-SigningTool $signtool @('sign', '/v', '/s', 'My', '/sha1', $certificate.Thumbprint,
        '/fd', 'SHA256', $catalog)
    # Verify cryptographic signatures and catalog membership with the temporary
    # test trust anchor. This is not production kernel-policy certification.
    # Import-Certificate into the root store can show an interactive trust prompt
    # and hang on a headless runner. certutil's forced user-store operation is
    # non-interactive and uses the same per-tool timeout as the signing tools.
    Invoke-SigningTool 'certutil.exe' @('-user', '-f', '-addstore', 'Root', $publicCert)
    $rootCertificateInstalled = $true
    Invoke-SigningTool $signtool @('verify', '/pa', '/v', $catalog)
    Invoke-SigningTool $signtool @('verify', '/pa', '/v', '/c', $catalog,
        (Join-Path $PackageRoot 'HomePodCastAudio.sys'))
    Invoke-SigningTool $signtool @('verify', '/pa', '/v', (Join-Path $PackageRoot 'HomePodCastAudio.sys'))
    [ordered]@{
        signing = 'ephemeral-development-test'; certificateThumbprint = $certificate.Thumbprint
        certificateExpires = $certificate.NotAfter.ToUniversalTime().ToString('o')
        privateKeyExported = $false; catalogVerified = $true; runtimeVerified = $false
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PackageRoot 'test-signing.json') -Encoding utf8
}
finally {
    if ($rootCertificateInstalled) {
        Invoke-SigningTool 'certutil.exe' @('-user', '-f', '-delstore', 'Root', $certificate.Thumbprint)
    }
    if ($certificate) { Remove-Item -LiteralPath $certificate.PSPath -Force -DeleteKey }
}
