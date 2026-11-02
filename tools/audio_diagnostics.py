"""Read-only P0 diagnostics. Capture requires an explicit endpoint ID.

Run from the repository root: python tools/audio_diagnostics.py --help
No default device, volume, driver, or saved application setting is changed.
"""

import argparse
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import platform
import sys
import threading
import time


def package_versions():
    result = {}
    for name in ("SoundCard", "numpy", "pyatv", "customtkinter"):
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = None
    return result


def capture_probe(sc, source, seconds):
    """Bound the probe even when a silent endpoint blocks a recorder read."""
    result = {"state": "opening", "frames": 0, "peak": 0.0,
              "rms": None, "active_samples": 0}

    def work():
        import ctypes
        import numpy as np

        initialized = False
        try:
            hr = ctypes.windll.ole32.CoInitializeEx(None, 0)
            if hr not in (0, 1):
                raise RuntimeError(f"COM initialization failed: {hr:#x}")
            initialized = True
            mic = sc.get_microphone(source.id, include_loopback=True)
            energy, samples = 0.0, 0
            with mic.recorder(samplerate=44100, channels=source.channels,
                              blocksize=441) as recorder:
                result["state"] = "opened"
                deadline = time.monotonic() + seconds
                while time.monotonic() < deadline:
                    block = recorder.record(numframes=None)
                    if block.size:
                        result["frames"] += len(block)
                        result["peak"] = max(result["peak"], float(np.abs(block).max()))
                        energy += float(np.square(block.astype(np.float64)).sum())
                        samples += block.size
                        result["active_samples"] += int(np.count_nonzero(np.abs(block) > 1e-5))
                        result["rms"] = (energy / samples) ** 0.5
            result["state"] = "completed"
        except Exception as exc:
            result.update(state="failed", error=f"{type(exc).__name__}: {exc}")
        finally:
            if initialized:
                ctypes.windll.ole32.CoUninitialize()

    worker = threading.Thread(target=work, daemon=True)
    worker.start()
    worker.join(seconds + 5)
    snapshot = dict(result)
    if worker.is_alive():
        snapshot.update(state="timed_out", note="A silent endpoint may block reads; this does not prove device failure.")
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", help="Exact render endpoint ID; never matched by name")
    parser.add_argument("--capture", action="store_true", help="Measure PCM levels from the selected endpoint")
    parser.add_argument("--seconds", type=float, default=5)
    parser.add_argument("--output", type=Path, help="Write JSON report to this file")
    args = parser.parse_args()
    if args.capture and not args.source_id:
        parser.error("--capture requires --source-id")
    if not 0 < args.seconds <= 60:
        parser.error("--seconds must be greater than 0 and at most 60")

    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "python": sys.version,
              "packages": package_versions(), "state": "blocked", "render_endpoints": []}
    code = 2
    try:
        if sys.platform != "win32":
            raise RuntimeError("This probe requires Windows WASAPI")
        import soundcard as sc

        speakers = sc.all_speakers()
        report["render_endpoints"] = [dict(id=s.id, name=s.name, channels=s.channels) for s in speakers]
        # Names are hints for a human, never used to bind capture automatically.
        report["virtual_name_hints"] = [s.id for s in speakers if "vb-audio" in s.name.lower() or "cable input" in s.name.lower()]
        report.update(state="enumerated", note="Enumeration does not establish driver identity, volume semantics, or successful playback.")
        code = 0
        if args.source_id:
            source = next((s for s in speakers if s.id == args.source_id), None)
            if source is None:
                raise RuntimeError("Selected endpoint ID is unavailable")
            report["selected_id"] = source.id
            if args.capture:
                report["capture"] = capture_probe(sc, source, args.seconds)
                if report["capture"]["state"] != "completed":
                    code = 2
    except Exception as exc:
        report.update(state="blocked", error=f"{type(exc).__name__}: {exc}")
        code = 2
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
