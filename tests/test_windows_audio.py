import threading
import sys
import unittest
from unittest.mock import Mock

sys.coinit_flags = 0
import comtypes
from windows_audio import WindowsAudio


class WindowsAudioTests(unittest.TestCase):
    def setUp(self):
        self.backend = WindowsAudio.__new__(WindowsAudio)
        self.backend.thread = threading.get_ident()
        self.backend.closed = False
        self.backend.com_error = comtypes.COMError
        self.backend.enumerator = Mock()

    def test_no_default_endpoint_is_a_normal_empty_state(self):
        self.backend.enumerator.GetDefaultAudioEndpoint.side_effect = comtypes.COMError(-2147023728, "Not found", None)
        self.assertIsNone(self.backend.default(0))

    def test_removed_device_is_unavailable(self):
        self.backend.enumerator.GetDevice.side_effect = comtypes.COMError(-2147023728, "Not found", None)
        self.assertFalse(self.backend.available("removed"))
