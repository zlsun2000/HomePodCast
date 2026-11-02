@echo off
echo This starts VM-only HomePodCast test preparation as administrator.
echo Please approve the Windows UAC prompt inside the virtual machine.
powershell.exe -NoProfile -Command "Start-Process -Verb RunAs -FilePath powershell.exe -ArgumentList @('-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File','%~dp0Prepare-VM.ps1')"
if errorlevel 1 pause
