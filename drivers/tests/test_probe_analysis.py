"""The VM probe must distinguish transmitted stereo PCM from a sample tone."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

spec = importlib.util.spec_from_file_location(
    "probe_endpoint", Path(__file__).resolve().parents[1] / "probe_endpoint.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.rate = 48000
        ticks = np.arange(self.rate) / self.rate
        self.stereo = np.stack((.03 * np.sin(2 * np.pi * 697 * ticks),
                                .03 * np.sin(2 * np.pi * 1337 * ticks)), axis=1)

    def test_accepts_input_pcm_surrounded_by_silence(self):
        silence = np.zeros_like(self.stereo)
        samples = np.concatenate((silence, self.stereo, silence))
        self.assertTrue(probe.analyze(samples, self.rate, (697, 1337))["passed"])

    def test_rejects_generated_tone_and_swapped_channels(self):
        swapped = self.stereo[:, ::-1]
        self.assertFalse(probe.analyze(swapped, self.rate, (697, 1337))["passed"])
        same_tone = np.repeat(self.stereo[:, :1], 2, axis=1)
        self.assertFalse(probe.analyze(same_tone, self.rate, (697, 1337))["passed"])

    def test_rejects_crosstalk_and_silence(self):
        self.assertFalse(probe.analyze(self.stereo, self.rate, (697, 0))["passed"])
        self.assertFalse(probe.analyze(np.zeros_like(self.stereo), self.rate, (697, 1337))["passed"])
        self.assertFalse(probe.analyze(self.stereo[:40], self.rate, (697, 1337))["passed"])


if __name__ == "__main__":
    unittest.main()
