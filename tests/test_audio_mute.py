import unittest
from unittest.mock import Mock

import numpy as np

from drivers.audio_mute import apply_endpoint_mute


class EndpointMuteTests(unittest.TestCase):
    def test_unmuted_samples_are_unchanged_and_muted_samples_are_silent(self):
        samples = np.array([[0.5, -0.2], [-0.4, 0.1]], dtype=np.float32)
        original = samples.copy()
        volume = Mock()
        volume.GetMute.return_value = False
        volume.GetMasterVolumeLevelScalar.return_value = 0.5
        self.assertIs(apply_endpoint_mute(samples, volume), samples)
        volume.GetMute.return_value = True
        np.testing.assert_array_equal(apply_endpoint_mute(samples, volume), np.zeros_like(samples))
        np.testing.assert_array_equal(samples, original)

    def test_zero_volume_silences_without_muting_and_nonzero_keeps_samples(self):
        samples = np.ones((2, 2))
        volume = Mock()
        volume.GetMute.return_value = False
        volume.GetMasterVolumeLevelScalar.return_value = 0.0
        np.testing.assert_array_equal(apply_endpoint_mute(samples, volume), np.zeros_like(samples))
        volume.GetMasterVolumeLevelScalar.return_value = 0.01
        self.assertIs(apply_endpoint_mute(samples, volume), samples)

    def test_volume_query_failure_propagates(self):
        volume = Mock()
        volume.GetMute.return_value = False
        volume.GetMasterVolumeLevelScalar.side_effect = OSError("endpoint disconnected")
        with self.assertRaises(OSError):
            apply_endpoint_mute(np.ones((2, 2)), volume)

    def test_read_failure_propagates(self):
        volume = Mock()
        volume.GetMute.side_effect = OSError("endpoint disconnected")
        with self.assertRaises(OSError):
            apply_endpoint_mute(np.ones((2, 2)), volume)
