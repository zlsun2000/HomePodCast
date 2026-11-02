"""Play short single-channel tones into an explicit VB-CABLE render endpoint."""

import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import Capture, RATE
import numpy as np
import soundcard as sc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    speaker = next(s for s in sc.all_speakers() if s.id == args.source_id)
    if "vb-audio" not in speaker.name.lower() or speaker.channels != 2:
        parser.error("Requires an explicitly selected stereo VB-Audio endpoint")
    results = []
    for rate in (44100, 48000):
        for channel in (0, 1):
            signal = np.zeros((rate, 2), dtype=np.float32)
            signal[:, channel] = .01 * np.sin(2 * np.pi * 1000 * np.arange(rate) / rate)
            capture = Capture(speaker.id, 2)
            capture.start()
            try:
                if not capture.ready.wait(5) or capture.error:
                    raise RuntimeError(f"Capture failed: {capture.error}")
                speaker.play(signal, samplerate=rate)
                time.sleep(.1)
            finally:
                capture.stop()
                capture.join(2)
            if capture.is_alive() or capture.error:
                raise RuntimeError(f"Capture failed to close: {capture.error}")
            samples = capture.ring.read(capture.ring.n)
            samples = samples[len(samples) // 4:3 * len(samples) // 4]
            if len(samples) < RATE // 4:
                raise RuntimeError("Too few captured frames")
            rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2, axis=0))
            spectrum = np.abs(np.fft.rfft(samples[:, channel] * np.hanning(len(samples))))
            frequency = float(np.argmax(spectrum) * RATE / len(samples))
            passed = abs(frequency - 1000) < 5 and rms[channel] > .0001 and rms[1-channel] < rms[channel] * .01
            results.append(dict(render_rate=rate, capture_rate=RATE, channel=channel,
                                frequency_hz=frequency, rms=rms.tolist(), passed=bool(passed)))
    report = dict(source_id=speaker.id, results=results, passed=all(r["passed"] for r in results))
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
