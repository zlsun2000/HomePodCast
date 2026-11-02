# Development probes

Run from the repository root in the Python environment from `requirements.txt`.
These are opt-in development tools; the app and installer do not run them.
Store generated reports under `build/`. Reports can contain device IDs and local
network addresses; review before sharing and do not commit private reports.

- `python tools/check_ui_layout.py`: constructs the Chinese and English UI with
  network, startup writes and tray side effects mocked. No playback or configuration changes.
- `python tools/audio_diagnostics.py --output build/audio.json`: read-only device
  enumeration. Adding `--capture --source-id '<endpoint ID>'` captures short-lived
  PCM and reports statistics only, without writing an audio recording.
- `python tools/discover_homepods.py`: bounded local-network RAOP discovery.
- `python tools/probe_cable_volume.py --source-id '<endpoint ID>' --output build/volume.json`:
  plays short tones into the explicit cable endpoint, changes its volume/mute,
  and restores them in `finally`.
- `python tools/probe_audio_formats.py --source-id '<endpoint ID>' --output build/formats.json`:
  plays left/right tones at 44.1/48 kHz into the explicit cable endpoint.
- `probe_output_recovery.py`: requires `--source-id`, `--journal` and `--output`.
  Switches default output, simulates a child-process crash and checks journal recovery.
- `probe_reconnect.py` and `probe_disconnect_restore.py`: additionally require
  `--receiver-address '<HomePod IP>'`. They connect to that receiver, temporarily
  switch defaults, inject a connection fault, then check restoration. The latter
  simulates receiver offline flags; it does not test actual Wi-Fi failure.

Do not run routing, playback or volume probes during a user's active audio session.
Choose a new journal filename for each probe. A failed restoration retains its
journal for recovery; never delete a live routing journal just to make a test pass.

## Prototype VM helpers

The application installer does **not** install the custom driver. For isolated
driver research, see [drivers/README.md](../drivers/README.md).

`setup_test_vm.ps1` creates a new VirtualBox guest with a 100 GB dynamic disk;
it refuses to replace an existing VM. `check_driver_toolchain.ps1` is read-only.

Install `pycdlib` in the development Python environment before creating test media:

```powershell
python -m pip install pycdlib
python tools/create_vm_test_media.py --artifact '<verified CI artifact directory>' --output build/driver-test.iso
```

Add `--receiver-address '<HomePod IP>'` only for the optional audible HomePod test.
Without it, audio-endpoint probes still work, but the HomePod test reports that no
receiver is configured. No personal receiver address is embedded by default.
The ISO is verified after creation. It is not automatically mounted or executed.

Guest scripts download their pinned Python/audio test dependencies and produce
JSON reports. `Prepare-VM.ps1` requires an isolated VirtualBox guest and changes
**guest** test signing and certificate trust; take a clean VM snapshot first.
A successful protocol report does not prove audible output: the HomePod test
still needs a person to confirm two tones with silence between them.
