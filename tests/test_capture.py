import ctypes
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

import numpy as np

from engine import Capture


class CaptureTests(unittest.TestCase):
    def test_failed_com_initialization_reports_error_without_uninitializing(self):
        capture = Capture("virtual", 2, respect_endpoint_mute=True)
        with patch.object(ctypes.windll.ole32, "CoInitializeEx", return_value=-2147417850), \
             patch.object(ctypes.windll.ole32, "CoUninitialize") as cleanup:
            capture.run()
        self.assertTrue(capture.ready.is_set())
        self.assertIsInstance(capture.error, OSError)
        cleanup.assert_not_called()

    def test_virtual_capture_gates_samples_and_reports_volume_failure(self):
        sys.coinit_flags = 0
        from pycaw.utils import AudioUtilities

        samples = np.full((441, 2), .25, np.float32)
        for volume_error in (None, OSError("endpoint removed")):
            with self.subTest(volume_error=volume_error):
                capture = Capture("virtual", 2, respect_endpoint_mute=True)
                microphone = MagicMock(id="virtual")
                recorder = microphone.recorder.return_value.__enter__.return_value = Mock()

                def record(**kwargs):
                    capture.stop()
                    return samples

                recorder.record.side_effect = record
                volume = Mock()
                volume.GetMute.return_value = True
                volume.GetMute.side_effect = volume_error
                with patch("soundcard.get_microphone", return_value=microphone), \
                     patch.object(AudioUtilities, "GetDeviceEnumerator"), \
                     patch.object(AudioUtilities, "CreateDevice", return_value=Mock(EndpointVolume=volume)):
                    capture.run()
                self.assertTrue(capture.ready.is_set())
                if volume_error:
                    self.assertIs(capture.error, volume_error)
                    self.assertEqual(capture.ring.n, 0)
                else:
                    self.assertIsNone(capture.error)
                    self.assertEqual(capture.ring.n, len(samples))
                    self.assertFalse(capture.ring.read(capture.ring.n).any())


if __name__ == "__main__":
    unittest.main()
