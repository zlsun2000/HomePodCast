# Experimental single installer

The installer bundles the application and the unmodified standard VB-CABLE Pack45.
The virtual audio wizard reuses a healthy installation; when the device is absent,
it asks before opening the vendor's interactive installer. Reboot after installing
the driver, then run **Configure HomePodCast Virtual Audio** from the Start menu.
Removing HomePodCast keeps the shared driver installed.

This is a development preview. Windows still exposes VB-CABLE's original playback
endpoints. The custom HomePodCast Audio prototype is not bundled. Unsigned application
builds may be blocked by Smart App Control; do not disable Windows protection to run them.

## Build

Use Windows x64, Python 3.12, Inno Setup 6 and the Windows SDK's x64 SignTool.
From the repository root, in an activated Python environment:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
.\build.ps1
Invoke-WebRequest -Uri 'https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack45.zip' -OutFile 'build/VBCABLE_Driver_Pack45.zip'
.\installer\build_installer.ps1 -CableZip 'build/VBCABLE_Driver_Pack45.zip'
```

Outputs: `dist/HomePodCast.exe` and `dist/HomePodCast-Setup.exe`. Optional `-IsccPath`
and `-SignToolPath` select nonstandard tool locations. `-ApplicationPath` selects a
previously built application. The archive is pinned by SHA-256; the build checks
the vendor installer and catalog signatures and catalog membership of INF/SYS files.
It does not modify the vendor package. The full original package and the
[VB-CABLE notice](VB-CABLE-NOTICE.txt) are retained and shown during installation.

Distribution follows [VB-Audio's terms](https://vb-audio.com/Services/licensing.htm),
including vendor attribution and donationware licensing. VB-CABLE is not MIT-licensed;
professional use and custom distribution need their applicable licensing conditions.

## Optional application signing

With an eligible code-signing certificate already available in the current user's
certificate store, sign the app first, then the installer and uninstaller:

```powershell
.\installer\sign_application.ps1 -ApplicationPath dist/HomePodCast.exe -CodeSigningThumbprint '<certificate thumbprint>' -TimestampUrl '<timestamp URL>' -SignToolPath '<path to signtool.exe>'
.\installer\build_installer.ps1 -CableZip 'build/VBCABLE_Driver_Pack45.zip' -CodeSigningThumbprint '<certificate thumbprint>' -TimestampUrl '<timestamp URL>' -SignToolPath '<path to signtool.exe>'
```

This path needs verification with the actual certificate and Windows security policy,
including any extracted dependencies. No production signing key is included. Application
signing is separate from Microsoft kernel-driver signing.

CI uploads `HomePodCast-Setup-experimental` as a build artifact. Tag builds still
attach only the portable application to a **draft** release; the installer is not
automatically published as a production release.
