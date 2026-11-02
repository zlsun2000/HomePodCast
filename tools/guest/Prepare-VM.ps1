param()
$ErrorActionPreference = 'Stop'
Write-Host 'HomePodCast Audio: isolated VM test preparation'
try {
    $principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Run this script as administrator inside the test virtual machine.'
    }
    $computer = Get-CimInstance Win32_ComputerSystem
    if ($computer.Model -notmatch 'VirtualBox') {
        throw 'This script only runs inside an Oracle VirtualBox guest.'
    }
    $manifest = Get-Content (Join-Path $PSScriptRoot 'build-manifest.json') -Raw | ConvertFrom-Json
    $signing = Get-Content (Join-Path $PSScriptRoot 'test-signing.json') -Raw | ConvertFrom-Json
    if ($manifest.artifactKind -ne 'homepodcast-audio-prototype' -or -not $manifest.packageSucceeded -or
        -not $signing.catalogVerified -or $signing.privateKeyExported -ne $false) {
        throw 'This is not a verified HomePodCast development test package.'
    }
    foreach ($name in @('HomePodCastAudio.sys', 'HomePodCastAudio.inf', 'HomePodCastAudio.cat', 'HomePodCast-Development.cer')) {
        $entry = @($manifest.files | Where-Object { $_.path -replace '\\', '/' -eq "test-package/$name" })
        if ($entry.Count -ne 1) { throw "Package manifest does not uniquely list $name" }
        $actual = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $name) -Algorithm SHA256).Hash
        if ($actual -ne $entry[0].sha256) { throw "Package hash mismatch: $name" }
    }
    $certFile = Join-Path $PSScriptRoot 'HomePodCast-Development.cer'
    $cert = [Security.Cryptography.X509Certificates.X509Certificate2]::new($certFile)
    if ($cert.Thumbprint -ne $signing.certificateThumbprint -or $cert.NotAfter -le (Get-Date)) {
        throw 'The development certificate is incorrect or expired.'
    }
    if (Confirm-SecureBootUEFI) {
        throw 'Guest Secure Boot is enabled. Stop and report this; no boot settings were changed.'
    }
    # Never change disk encryption or suspend protection on the user's behalf.
    try {
        $systemVolume = Get-CimInstance -Namespace 'root/CIMV2/Security/MicrosoftVolumeEncryption' `
            -ClassName Win32_EncryptableVolume -Filter "DriveLetter='$env:SystemDrive'" -ErrorAction Stop
        if ($systemVolume) {
            $protection = Invoke-CimMethod -InputObject $systemVolume -MethodName GetProtectionStatus
            if ($protection.ReturnValue -ne 0 -or $protection.ProtectionStatus -ne 0) {
                throw 'System drive encryption protection is enabled or unknown. Stop and report this.'
            }
        }
    } catch {
        throw "Could not establish a safe guest disk-encryption state: $($_.Exception.Message)"
    }
    Write-Host 'Verified VirtualBox guest, package hashes, certificate and guest boot prerequisites.'
    & bcdedit.exe /set testsigning on
    if ($LASTEXITCODE -ne 0) { throw 'Could not enable test signing in this VM.' }
    foreach ($store in @('Root', 'TrustedPublisher')) {
        & certutil.exe -f -addstore $store $certFile
        if ($LASTEXITCODE -ne 0) { throw "Could not add the development certificate to $store." }
    }
    Write-Host ''
    Write-Host 'Preparation succeeded. Restart ONLY this virtual machine, then return to Codex.'
    Write-Host 'The driver has not yet been installed.'
} catch {
    Write-Host ''
    Write-Host "Preparation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Do not continue installation. Report this message in Codex; the VM snapshot remains available.'
    exit 1
}
