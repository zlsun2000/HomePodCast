#ifndef AppVersion
  #error AppVersion must be supplied by build_installer.ps1
#endif
#ifndef CableDir
  #error CableDir must be supplied by build_installer.ps1
#endif
#ifndef AppExe
  #error AppExe must be supplied by build_installer.ps1
#endif

[Setup]
AppId={{E89CB09F-36E1-4CD8-B8BF-109AC26E6957}
AppName=HomePodCast
AppVersion={#AppVersion}
AppPublisher=HomePodCast contributors
DefaultDirName={localappdata}\Programs\HomePodCast
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
MinVersion=10.0.16299
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=HomePodCast-Setup
SetupIconFile=..\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
InfoBeforeFile=VB-CABLE-NOTICE.txt
UninstallDisplayIcon={app}\HomePodCast.exe
#ifdef SignedBuild
SignTool=HomePodCastSigner
SignedUninstaller=yes
#endif
; The driver is shared software and is never removed by this uninstaller.

[Files]
Source: "{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#CableDir}\*"; DestDir: "{app}\VBCABLE"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "VB-CABLE-NOTICE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\HomePodCast"; Filename: "{app}\HomePodCast.exe"
Name: "{autoprograms}\Configure HomePodCast Virtual Audio"; Filename: "{app}\HomePodCast.exe"; Parameters: "--configure-virtual-audio"

[Run]
Filename: "{app}\HomePodCast.exe"; Parameters: "--configure-virtual-audio"; Description: "Configure virtual audio (VB-CABLE by VB-Audio)"; Flags: postinstall skipifsilent

[Messages]
WelcomeLabel2=This setup installs HomePodCast and includes VB-CABLE by VB-Audio (donationware). Source and license information are included. The virtual audio wizard will ask before installing a driver.
