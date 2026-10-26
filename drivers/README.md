# Driver build baseline

This is the first bring-up milestone for the integrated audio driver. It builds
the **unmodified Microsoft SysVAD sample**, not a working HomePodCast Audio driver.
SysVAD still generates capture test tones; the real PCM bridge is not implemented.
Artifacts are unsigned development outputs, not ready-to-install production packages.

`upstream.lock.json` pins the source commit, WIL submodule and SDK/WDK package
versions. `packages.x64.config` restores only the x64 kits needed by this build.
Upstream MS-PL licensing remains applicable and is copied alongside artifacts.

## CI

`.github/workflows/driver-baseline.yml` uses `windows-2025-vs2026` and restores
SDK/WDK from NuGet. A system-wide WDK installation is not required. It builds the
solution with x64 MSBuild so WDK selects the native x64 StampInf/API validator
tools supplied by the x64 NuGet kit (the x86 kit has only a subset of tools).
It builds the
full SysVAD solution, saves MSBuild text/binary logs, and uploads binaries plus a
manifest containing versions and file hashes. It does not install a driver,
reboot a runner, change boot security settings, or use release signing keys.

The runner image is serviced by GitHub; the manifest records its version. This
pins source/package inputs but does not claim byte-for-byte reproducibility.
Existing app CI is separate from this baseline job. A successful run of this new
job is required before calling the baseline build verified.

## Equivalent local command (optional)

Requires VS C++ tools, the VS Windows Driver Kit extension/toolsets, the matching
Spectre/ATL libraries, and NuGet CLI on PATH. SDK/WDK restore into the source cache.
The supported GitHub runner supplies the VS components. A local machine without
the driver extension can fail with MSB8020 even after NuGet restore succeeds;
this does not require stopping CI-first development to install a full local WDK.

```powershell
git clone --filter=blob:none --no-checkout https://github.com/microsoft/Windows-driver-samples.git .driver-source
git -C .driver-source checkout bb68ed5e770bce04dc5395ec9258dafab034184d
./drivers/build.ps1
```

Do not recreate an existing cache blindly. The build rejects mismatched or modified
tracked source and checks the exact WIL submodule commit. Generated sources,
packages and outputs are ignored by the HomePodCast repository.

## Following milestones

1. Get a successful baseline build and review warnings and package contents.
2. Build the separate HomePodCast render endpoint prototype described below.
3. Build and statically check it in CI; distinguish it from baseline artifacts.
4. Only then install test-signed packages in the isolated VM for runtime validation.

Passing the baseline build is not evidence that any custom driver works. VM setup
is not a prerequisite for writing and compiling the driver project in CI.

## HomePodCast endpoint prototype

`./drivers/build.ps1 -Prototype` prepares a fresh isolated tree under
`.driver-prototype/`, retaining the locked upstream miniport implementation and
MS-PL license. It overlays HomePodCast-owned endpoint tables and an INF with a
distinct `Root\HomePodCastAudio` hardware ID, service, binary and catalog name.
The baseline checkout is never patched. CI builds baseline and prototype as
separate jobs and uploads distinct artifacts. This is a development prototype,
not a signed release; its initial INF targets Windows 11 build 22621 or later.

There is one render stream pin and an analog bridge pin, with no hardware audio
engine node, hardware loopback pin, offload, microphone, APO or sideband device.
Windows Audio Engine handles shared-mode client mixing. HomePodCast can capture
that real mix using WASAPI software loopback on the render endpoint, rather than
the SysVAD capture sine generator. This follows the documented fallback when a
render endpoint has no hardware loopback pin:
[Microsoft loopback recording](https://learn.microsoft.com/en-us/windows/win32/coreaudio/loopback-recording).
The driver consumes/discards render DMA using the upstream WaveRT clock and never
forwards it to physical speakers. The sample's PCM file recording switch is removed.

The endpoint declares 16-bit stereo PCM at 44.1/48 kHz (48 kHz default). Exclusive
playback cannot be captured by WASAPI loopback. Windows volume/mute behavior,
timing, multi-client mixing, sleep/PnP and actual PCM capture must be validated
in the isolated Windows VM. A green compiler/API validation run does not prove
these runtime behaviors. If software loopback is unsuitable after measurement,
the alternative is a bounded, independently reviewed render/capture bridge.

`prepare_prototype.py` hashes the overlay inputs in the build manifest and
checks that it does not change baseline tracked files. New overlay files are
MIT-licensed; upstream source and notices remain MS-PL. No binary is installed
and no boot-security settings are changed by this build.
