"""Verify real PCM and volume on an explicitly selected HomePodCast Audio endpoint.

Run inside the driver-test VM with numpy, SoundCard, pycaw and comtypes installed.
No default output changes are made. Only the named endpoint's volume/mute is
temporarily changed, then restored. Does not stream to a HomePod.
"""
import argparse
import ctypes
import json
from pathlib import Path
import threading
import time
import sys


def analyze(samples, rate, frequencies):
    import numpy as np
    # Find a quarter-second of active audio, avoiding startup/tail silence.
    width = rate // 4
    if len(samples) < width or samples.ndim != 2 or samples.shape[1] != 2:
        return {"passed": False, "reason": "Insufficient stereo frames"}
    starts = range(0, len(samples) - width + 1, width // 2)
    start = max(starts, key=lambda pos: float(np.mean(samples[pos:pos + width] ** 2)))
    window = samples[start:start + width].astype(np.float64)
    rms = np.sqrt(np.mean(window ** 2, axis=0))
    spectrum = abs(np.fft.rfft(window * np.hanning(width)[:, None], axis=0))
    peaks = np.argmax(spectrum, axis=0) * rate / width
    passed = True
    for channel, frequency in enumerate(frequencies):
        if frequency:
            passed &= bool(rms[channel] > .001 and abs(peaks[channel] - frequency) < 8)
        else:
            passed &= bool(rms[channel] < max(.00005, rms[1 - channel] * .01))
    return {"passed": bool(passed), "rms": rms.tolist(), "peaks_hz": peaks.tolist()}


def capture_trial(speaker, render_rate, frequencies):
    import numpy as np
    import soundcard as sc
    rate = 48000
    ready, stop = threading.Event(), threading.Event()
    frames, errors = [], []

    def record():
        initialized = ctypes.windll.ole32.CoInitializeEx(None, 0) >= 0
        try:
            if not initialized:
                raise RuntimeError("Capture MTA initialization failed")
            microphone = sc.get_microphone(speaker.id, include_loopback=True)
            if microphone.id != speaker.id:
                raise RuntimeError("WASAPI selected a different endpoint")
            with microphone.recorder(rate, channels=2, blocksize=480) as recorder:
                ready.set()
                count = 0
                while not stop.is_set():
                    chunk = recorder.record(numframes=None)
                    count += len(chunk)
                    if count > rate * 5:
                        raise RuntimeError("Capture exceeded bounded trial buffer")
                    frames.append(chunk)
        except Exception as error:
            errors.append(str(error))
        finally:
            ready.set()
            if initialized:
                ctypes.windll.ole32.CoUninitialize()

    worker = threading.Thread(target=record, daemon=True)
    worker.start()
    try:
        if not ready.wait(5) or errors:
            raise RuntimeError(f"Capture did not become ready: {errors}")
        ticks = np.arange(render_rate) / render_rate
        signal = np.zeros((render_rate, 2), dtype=np.float32)
        for channel, frequency in enumerate(frequencies):
            if frequency:
                signal[:, channel] = .03 * np.sin(2 * np.pi * frequency * ticks)
        speaker.play(signal, samplerate=render_rate)
        time.sleep(.2)
    finally:
        stop.set()
        worker.join(3)
    if worker.is_alive() or errors:
        raise RuntimeError(f"Capture did not close cleanly: {errors}")
    return np.concatenate(frames) if frames else np.zeros((0, 2), np.float32)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List candidate endpoint IDs only")
    parser.add_argument("--source-id", help="Exact Windows render endpoint ID")
    parser.add_argument("--output", type=Path, help="JSON report path (required for testing)")
    args = parser.parse_args()
    # Import SoundCard first: its Windows COM initialization must occur before
    # pycaw/comtypes initialize the main thread's apartment.
    import soundcard as sc
    import numpy as np
    candidates = [speaker for speaker in sc.all_speakers()
                  if "homepodcast audio" in speaker.name.casefold()]
    if args.list:
        print(json.dumps([{"id": s.id, "name": s.name, "channels": s.channels}
                          for s in candidates], indent=2))
        return 0
    if not args.source_id or not args.output:
        parser.error("Specify --source-id and --output, or use --list")
    speaker = next((s for s in candidates if s.id == args.source_id), None)
    if speaker is None or speaker.channels != 2:
        parser.error("The exact ID must identify a stereo HomePodCast Audio render endpoint")
    sys.coinit_flags = 0
    from pycaw.utils import AudioUtilities
    enumerator = AudioUtilities.GetDeviceEnumerator()
    volume = AudioUtilities.CreateDevice(enumerator.GetDevice(speaker.id)).EndpointVolume
    previous_volume = volume.GetMasterVolumeLevelScalar()
    previous_mute = volume.GetMute()
    report = {"endpoint_id": speaker.id, "name": speaker.name, "pcm_trials": [],
              "volume_trials": [], "passed": False}
    try:
        volume.SetMute(0, None)
        volume.SetMasterVolumeLevelScalar(1, None)
        for rate in (44100, 48000):
            for frequencies in ((997, 0), (0, 1531), (697, 1337)):
                result = analyze(capture_trial(speaker, rate, frequencies), 48000, frequencies)
                result.update(render_rate=rate, expected_hz=frequencies)
                report["pcm_trials"].append(result)
        for scalar, muted in ((1, False), (.5, False), (.1, False), (0, False), (1, True)):
            volume.SetMasterVolumeLevelScalar(scalar, None)
            volume.SetMute(int(muted), None)
            time.sleep(.15)
            samples = capture_trial(speaker, 48000, (697, 1337))
            result = analyze(samples, 48000, (697, 1337))
            rms = float(np.mean(result.get("rms", [0])))
            # No packets while muted is legitimate; zero is not success for
            # unmuted positive-volume trials.
            report["volume_trials"].append({"scalar": scalar, "muted": muted, "rms": rms})
        rms = [trial["rms"] for trial in report["volume_trials"]]
        report["volume_passed"] = (rms[0] > rms[1] > rms[2] > .00005 and
                                    max(rms[3:]) < max(.00005, rms[0] * .005))
        report["passed"] = all(t["passed"] for t in report["pcm_trials"]) and report["volume_passed"]
    except Exception as error:
        report["error"] = str(error)
    finally:
        try:
            volume.SetMasterVolumeLevelScalar(previous_volume, None)
            volume.SetMute(previous_mute, None)
            report["volume_restored"] = (abs(volume.GetMasterVolumeLevelScalar() - previous_volume) < .0001
                                         and volume.GetMute() == previous_mute)
            if not report["volume_restored"]:
                report["passed"] = False
        except Exception as error:
            report["volume_restored"] = False
            report["restore_error"] = str(error)
            report["passed"] = False
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
