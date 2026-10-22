param(
    [ValidateSet('Debug', 'Release')][string]$Configuration = 'Release',
    [string]$SourceRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) '.driver-source'),
    [string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'driver-artifacts'),
    [switch]$RestoreOnly
)
$ErrorActionPreference = 'Stop'
$lock = Get-Content (Join-Path $PSScriptRoot 'upstream.lock.json') -Raw | ConvertFrom-Json
function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}
if (-not (Test-Path (Join-Path $SourceRoot '.git'))) {
    throw 'Fetch the pinned upstream source first; see drivers/README.md.'
}
$actualCommit = (& git -C $SourceRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actualCommit -ne $lock.commit) { throw 'Upstream commit differs from the lock file' }
$changes = & git -C $SourceRoot status --porcelain --untracked-files=no
if ($LASTEXITCODE -ne 0 -or $changes) { throw 'Baseline source has tracked modifications' }
Invoke-Checked git @('-C', $SourceRoot, 'submodule', 'update', '--init', '--depth', '1', 'wil')
$wilCommit = (& git -C (Join-Path $SourceRoot 'wil') rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $wilCommit -ne $lock.wilCommit) { throw 'WIL commit differs from the lock file' }

$packages = Join-Path $SourceRoot 'packages'
[xml]$config = Get-Content (Join-Path $PSScriptRoot 'packages.x64.config')
foreach ($package in $config.packages.package) {
    if ($package.version -ne $lock.kitVersion) { throw 'NuGet kit versions differ from the lock file' }
}
$nuget = (Get-Command nuget -ErrorAction Stop).Source
Invoke-Checked $nuget @('restore', (Join-Path $PSScriptRoot 'packages.x64.config'),
    '-PackagesDirectory', $packages, '-Source', 'https://api.nuget.org/v3/index.json', '-NonInteractive')
if ($RestoreOnly) { return }

$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$msbuild = & $vswhere -latest -products '*' -requires Microsoft.Component.MSBuild -find 'MSBuild\**\Bin\amd64\MSBuild.exe'
if ($LASTEXITCODE -ne 0 -or -not $msbuild) { throw 'Visual Studio x64 MSBuild not found' }
$msbuild = @($msbuild)[0]
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$OutputRoot = (Resolve-Path $OutputRoot).Path
$manifest = [ordered]@{
    artifactKind = $lock.artifactKind; upstreamCommit = $actualCommit; wilCommit = $wilCommit
    kitVersion = $lock.kitVersion; configuration = $Configuration; platform = 'x64'
    msbuild = $msbuild; runnerImage = $env:ImageVersion; buildSucceeded = $false
    warning = 'Unmodified Microsoft SysVAD baseline; not HomePodCast Audio; not production signed.'
}
$manifestPath = Join-Path $OutputRoot 'build-manifest.json'
$manifest | ConvertTo-Json | Set-Content -LiteralPath $manifestPath -Encoding utf8
Invoke-Checked $msbuild @((Join-Path $SourceRoot $lock.solution), '/m', '/t:Build',
    "/p:Configuration=$Configuration", '/p:Platform=x64', '/p:SignMode=Off',
    '/p:WindowsTargetPlatformVersion=10.0.28000.0',
    "/bl:$(Join-Path $OutputRoot 'sysvad.binlog')", '/fl',
    "/flp:logfile=$(Join-Path $OutputRoot 'sysvad.log');verbosity=normal")
$binaries = @(Get-ChildItem (Join-Path $SourceRoot 'audio/sysvad') -Filter '*.sys' -Recurse)
if (-not $binaries) { throw 'MSBuild completed but no driver binary was produced' }
foreach ($file in $binaries) {
    $relative = [IO.Path]::GetRelativePath($SourceRoot, $file.FullName)
    $destination = Join-Path $OutputRoot $relative
    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $destination
}
foreach ($extension in @('*.inf', '*.cat', '*.dll', '*.pdb')) {
    foreach ($file in Get-ChildItem (Join-Path $SourceRoot 'audio/sysvad') -Filter $extension -Recurse) {
        $destination = Join-Path $OutputRoot ([IO.Path]::GetRelativePath($SourceRoot, $file.FullName))
        New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $destination
    }
}
Copy-Item (Join-Path $SourceRoot 'LICENSE') (Join-Path $OutputRoot 'UPSTREAM-LICENSE.txt')
Copy-Item (Join-Path $PSScriptRoot 'README.md') (Join-Path $OutputRoot 'README.md')
$manifest.buildSucceeded = $true
$manifest.files = @(Get-ChildItem $OutputRoot -Recurse -File | Where-Object Extension -In '.sys','.inf','.cat','.dll' |
    ForEach-Object { @{ path = [IO.Path]::GetRelativePath($OutputRoot, $_.FullName); sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash } })
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
