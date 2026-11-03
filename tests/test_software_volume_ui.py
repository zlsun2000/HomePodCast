import unittest
from unittest.mock import Mock, patch

import app


class SoftwareVolumeUiTests(unittest.TestCase):
    def test_requires_confirmation_and_keeps_disabled_if_rejected(self):
        ui = app.App.__new__(app.App)
        ui.software_volume = False
        ui.software_volume_box = Mock()
        ui.root = Mock()
        ui.tr = lambda key: key
        with patch.object(app.messagebox, "askyesno", return_value=False):
            ui.set_software_volume(True)
        self.assertFalse(ui.software_volume)
        ui.software_volume_box.deselect.assert_called_once()
        with patch.object(app.messagebox, "askyesno", return_value=True):
            ui.set_software_volume(True)
        self.assertTrue(ui.software_volume)
        ui.set_software_volume(False)
        self.assertFalse(ui.software_volume)


if __name__ == "__main__":
    unittest.main()
