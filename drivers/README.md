# Driver build baseline

This is the first bring-up milestone for the integrated audio driver. It builds
the **unmodified Microsoft SysVAD sample**, not a working HomePodCast Audio driver.
SysVAD still generates capture test tones; the real PCM bridge is not implemented.
Baseline artifacts are unsigned. Prototype artifacts use a temporary development
test certificate; neither is a production package.

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
not a production-signed release; its initial INF targets Windows 11 build 22621 or later.

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

After installing a test-signed package **inside the VM**, install the probe
dependencies with `python -m pip install -r probe-requirements.txt`, then run:

```powershell
python probe_endpoint.py --list
python probe_endpoint.py --source-id '<exact ID from the list>' --output runtime-report.json
```

This runs six PCM trials (two rates; left, right and distinct stereo tones),
then 100/50/10/0 percent and mute trials. It restores the endpoint volume/mute
and reports failure if capture, channel separation, volume scaling or restoration
fails. It does not change default output or send anything over AirPlay. Keep this
report separate from compiler success; a synthetic analysis unit test is not a
runtime pass. Windows endpoint absence should fail, not fall back to speakers.

## Test package signing and VM installation

The prototype CI job passes `-TestSign`. This path is restricted to ephemeral
GitHub-hosted runners: it creates a non-exportable RSA test key, embeds a SHA256
signature in the SYS, generates a catalog with Inf2Cat for Windows 11 22H2/24H2,
and signs the catalog. It temporarily trusts its public certificate on that
runner to verify signatures and catalog membership, then removes the certificate
and private key. Only the public CER, SYS, INF, CAT and verification metadata
enter `test-package/`. This proves package integrity, not runtime correctness or
Microsoft production kernel-signing eligibility. Every run creates a new test
certificate. No production signing account or reusable private key is involved.

Use only the isolated Windows VM for this package:

1. Install Windows 11 x64 in the VM and take a clean snapshot. Keep the host's
   boot settings and certificate stores unchanged.
2. In the **guest's** elevated terminal, trust the artifact's public certificate
   and enable guest test mode, then restart the guest:

   ```powershell
   certutil -addstore -f Root .\test-package\HomePodCast-Development.cer
   certutil -addstore -f TrustedPublisher .\test-package\HomePodCast-Development.cer
   bcdedit /set testsigning on
   ```

   If guest Secure Boot prevents test mode, adjust only the VM's Secure Boot
   configuration. This build does not disable host Secure Boot or memory integrity.
3. In guest Device Manager, choose Action > Add legacy hardware > select hardware
   manually > Show all devices > Have Disk, and select
   `test-package/HomePodCastAudio.inf`. The root device should create exactly one
   `HomePodCast Audio` playback endpoint and no microphones. Record any error code.
4. Run the probe above in the guest. Then validate ordinary applications, multiple
   clients, stop/restart and sleep separately; passing the probe is only the first
   audio gate. HomePod streaming/discovery is a separate network test.
5. Uninstall the device and its driver package in guest Device Manager; record the
   published `oem*.inf` before deleting a package. Remove this run's certificate
   from guest Root/TrustedPublisher using the thumbprint in `test-signing.json`,
   disable guest test mode and restart, or revert to the clean snapshot.

Reference: [Microsoft test-signing a driver file](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/test-signing-a-driver-file).
