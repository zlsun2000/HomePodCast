import io
import json
import unittest
from unittest.mock import patch

import app


class UpdateTests(unittest.TestCase):
    def test_installer_is_never_selected_as_application_update(self):
        payload = {"tag_name": "v9.0.0", "assets": [
            {"name": "HomePodCast-Setup.exe", "browser_download_url": "setup", "size": 20},
            {"name": "HomePodCast.exe", "browser_download_url": "application", "size": 10},
        ]}
        with patch("app.urllib.request.urlopen", return_value=io.BytesIO(json.dumps(payload).encode())):
            release = app.newer_release()
        self.assertEqual(release["url"], "application")
        self.assertEqual(release["size"], 10)

    def test_setup_only_release_cannot_replace_the_application(self):
        payload = {"tag_name": "v9.0.0", "assets": [
            {"name": "HomePodCast-Setup.exe", "browser_download_url": "setup"},
        ]}
        with patch("app.urllib.request.urlopen", return_value=io.BytesIO(json.dumps(payload).encode())):
            release = app.newer_release()
        self.assertEqual(release["url"], "")


if __name__ == "__main__":
    unittest.main()
