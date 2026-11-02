$ErrorActionPreference = 'Stop'
$vbox = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
$workspace = Split-Path -Parent $PSScriptRoot
$base = Join-Path $workspace '.vm'
$vmName = 'HomePodCast-DriverTest'
$disk = Join-Path $base "$vmName\system.vdi"

function Invoke-VBox {
    & $vbox @args
    if ($LASTEXITCODE -ne 0) { throw "VBoxManage failed: $($args[0])" }
}

$existing = & $vbox list vms
if ($LASTEXITCODE -ne 0) { throw 'Cannot read registered virtual machines' }
if ($existing | Where-Object { $_ -match ('^"' + [regex]::Escape($vmName) + '" ') }) {
    throw 'The test VM is already registered; inspect it instead of recreating it.'
}
if (Test-Path -LiteralPath (Join-Path $base $vmName)) {
    throw 'A VM directory already exists; inspect it before continuing.'
}

New-Item -ItemType Directory -Path $base -Force | Out-Null
Invoke-VBox createvm --name $vmName --ostype Windows11_64 --basefolder $base --register
Invoke-VBox modifyvm $vmName --memory 8192 --cpus 4 --firmware efi64 --tpm-type 2.0 --ioapic on --graphicscontroller vboxsvga --vram 128 --nic1 nat --boot1 dvd --boot2 disk --boot3 none --boot4 none --audio-enabled on --audio-out off --audio-in off
Invoke-VBox createmedium disk --filename $disk --size 102400 --format VDI --variant Standard
Invoke-VBox storagectl $vmName --name SATA --add sata --controller IntelAhci --portcount 2
Invoke-VBox storageattach $vmName --storagectl SATA --port 0 --device 0 --type hdd --medium $disk
Invoke-VBox storageattach $vmName --storagectl SATA --port 1 --device 0 --type dvddrive --medium emptydrive
Invoke-VBox showvminfo $vmName --machinereadable
