@echo off
echo This will play two quiet test tones on your HomePod, with a muted interval between them.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Test-HomePod.ps1"
echo The test window can now be closed.
pause
