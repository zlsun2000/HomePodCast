"""Measure render-loopback levels while restoring the original endpoint volume."""

import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.coinit_flags = 0  # Match SoundCard's MTA apartment before comtypes imports.
import engine
import numpy as np
import soundcard as sc
from pycaw.pycaw import AudioUtilities


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    speaker = next(s for s in sc.all_speakers() if s.id == args.source_id)
    if "vb-audio" not in speaker.name.lower():
        parser.error("This probe only plays into a VB-Audio endpoint")
    device = AudioUtilities.CreateDevice(AudioUtilities.GetDeviceEnumerator().GetDevice(speaker.id))
    volume = device.EndpointVolume
    original = (volume.GetMasterVolumeLevelScalar(), volume.GetMute())
    results = []
    tone = np.repeat((.02 * np.sin(2 * np.pi * 440 * np.arange(88200) / 44100))[:, None], 2, axis=1)
    try:
        for percent, mute in [(100, False), (50, False), (10, False), (0, False), (100, True)]:
            volume.SetMasterVolumeLevelScalar(percent / 100, None)
            volume.SetMute(mute, None)
            time.sleep(.5)
            capture = engine.Capture(speaker.id, 2)
            capture.start()
            try:
                if not capture.ready.wait(5) or capture.error:
                    raise RuntimeError(f"Capture failed: {capture.error}")
                speaker.play(tone, samplerate=44100)
                time.sleep(.15)
            finally:
                capture.stop()
                capture.join(2)
            if capture.is_alive() or capture.error:
                raise RuntimeError(f"Capture did not close cleanly: {capture.error}")
            samples = capture.ring.read(capture.ring.n)
            if not samples.size:
                raise RuntimeError("No samples captured")
            # Ignore stream startup, endpoint volume ramps, and trailing silence.
            samples = samples[len(samples) // 4:3 * len(samples) // 4]
            results.append(dict(percent=percent, mute=mute, frames=len(samples),
                                peak=float(np.abs(samples).max()),
                                rms=float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))))
    finally:
        volume.SetMasterVolumeLevelScalar(original[0], None)
        volume.SetMute(original[1], None)
    report = dict(source_id=speaker.id, original_volume=original[0], original_mute=bool(original[1]),
                  restored_volume=volume.GetMasterVolumeLevelScalar(), restored_mute=bool(volume.GetMute()),
                  measurements=results)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
