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
2. Add a separate HomePodCast endpoint project and bounded render/capture bridge.
3. Build and statically check it in CI; distinguish it from baseline artifacts.
4. Only then install test-signed packages in the isolated VM for runtime validation.

Passing the baseline build is not evidence that any custom driver works. VM setup
is not a prerequisite for writing and compiling the driver project in CI.
