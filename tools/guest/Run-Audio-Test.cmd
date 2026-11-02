@echo off
echo HomePodCast Audio test: installs a local Python runtime if needed and downloads test dependencies.
echo This tests the VM endpoint and does not send audio to HomePod.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Test-Audio.ps1"
echo.
echo The test window can now be closed.
pause
