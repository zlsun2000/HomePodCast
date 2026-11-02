param([string]$Output = 'docs/P4_DRIVER_TOOLCHAIN.json')

$kitsRoot = 'C:\Program Files (x86)\Windows Kits\10'
$installed = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows Kits\Installed Roots' -ErrorAction SilentlyContinue
if (-not $installed.KitsRoot10) {
    $installed = Get-ItemProperty 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows Kits\Installed Roots' -ErrorAction SilentlyContinue
}
if ($installed.KitsRoot10) { $kitsRoot = $installed.KitsRoot10 }
$vswhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
$compilerTools = @()
foreach ($name in @('msbuild', 'cl', 'InfVerif', 'signtool')) {
    $command = Get-Command $name -ErrorAction SilentlyContinue
    if ($command) { $compilerTools += @{ name = $name; path = $command.Source } }
}
$wdkHeaders = @(Get-ChildItem -Path "$kitsRoot\Include\*\km\portcls.h" -ErrorAction SilentlyContinue | ForEach-Object FullName)
$vsInstallations = @()
if (Test-Path -LiteralPath $vswhere) {
    $vsInstallations = @(& $vswhere -all -products '*' -format json | ConvertFrom-Json)
}
$report = @{
    checkedAt = (Get-Date).ToUniversalTime().ToString('o')
    kitsRoot = $kitsRoot
    kitsRootExists = (Test-Path -LiteralPath $kitsRoot)
    wdkPortclsHeaders = $wdkHeaders
    vswhereExists = (Test-Path -LiteralPath $vswhere)
    visualStudioInstallations = $vsInstallations
    commandsOnPath = $compilerTools
    note = 'Read-only discovery of registered/standard installations and PATH; custom unregistered locations may require explicit configuration.'
}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Output -Encoding utf8
$report | ConvertTo-Json -Depth 8
