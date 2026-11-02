import json
from pathlib import Path
import tempfile
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import virtual_audio_setup as setup

from virtual_audio_setup import (HARDWARE_PROPERTY, INSTANCE_PROPERTY, ENDPOINT_NAME_PROPERTY, ENDPOINT_FORM_FACTOR,
                                 classify_devices, matching_endpoints, standard_render_id,
                                 restore_changed_defaults, save_virtual_config)


def endpoint(endpoint_id, name, instance, hardware="VBAudioVACWDM", state=1):
    return SimpleNamespace(id=endpoint_id, state=state, properties={
        HARDWARE_PROPERTY: hardware,
        INSTANCE_PROPERTY: "{1}." + instance,
        ENDPOINT_NAME_PROPERTY: name,
    })


class VirtualAudioSetupTests(unittest.TestCase):
    def test_audio_import_after_soundcard_does_not_change_com_thread_mode(self):
        result = subprocess.run([sys.executable, "-c", "import soundcard; from virtual_audio_setup import load_audio_api; load_audio_api()"],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_existing_and_abnormal_devices_never_use_vendor_installer(self):
        self.assertEqual(classify_devices([]), "missing")
        self.assertEqual(classify_devices([{"instance": "", "status": "Unknown", "provider": ""}]),
                         "residual_service")
        ready = {"status": "OK", "provider": "VB-Audio Software"}
        self.assertEqual(classify_devices([ready]), "ready")
        self.assertEqual(classify_devices([{**ready, "status": "Error"}]), "needs_attention")
        self.assertEqual(classify_devices([{**ready, "provider": "other"}]), "needs_attention")
        self.assertEqual(classify_devices([ready, ready]), "needs_attention")

    def test_residual_service_opens_vendor_ui_after_user_confirmation(self):
        residual = [{"instance": "", "status": "Unknown", "provider": ""}]
        api = Mock()
        backend = Mock()
        with patch.object(setup, "load_audio_api", return_value=(Mock(return_value=backend), api)), \
             patch.object(setup.tk, "Tk"), patch.object(setup.ctypes.windll.user32, "FindWindowW", return_value=0), \
             patch.object(setup, "query_devices", side_effect=[residual, residual, residual]), \
             patch.object(setup.messagebox, "askyesno", return_value=True), \
             patch.object(setup.messagebox, "showwarning"), patch.object(setup.messagebox, "showinfo"), \
             patch.object(setup.sys, "frozen", True, create=True), \
             patch.object(Path, "is_file", return_value=True), patch.object(setup, "verify_vendor_files"), \
             patch.object(setup, "snapshot_defaults", return_value={}), \
             patch.object(setup, "run_vendor_setup", return_value=0) as launch:
            self.assertEqual(setup.run(), 0)
            launch.assert_called_once()

    def test_device_appearing_before_vendor_ui_prevents_uninstall(self):
        residual = [{"instance": "", "status": "Unknown", "provider": ""}]
        ready = [{"instance": "id", "status": "OK", "provider": "VB-Audio Software"}]
        with patch.object(setup, "load_audio_api", return_value=(Mock(return_value=Mock()), Mock())), \
             patch.object(setup.tk, "Tk"), patch.object(setup.ctypes.windll.user32, "FindWindowW", return_value=0), \
             patch.object(setup, "query_devices", side_effect=[residual, ready]), \
             patch.object(setup.messagebox, "askyesno", return_value=True), \
             patch.object(setup.messagebox, "showerror"), patch.object(setup.sys, "frozen", True, create=True), \
             patch.object(Path, "is_file", return_value=True), patch.object(setup, "verify_vendor_files"), \
             patch.object(setup, "snapshot_defaults", return_value={}), \
             patch.object(setup, "run_vendor_setup") as launch:
            self.assertEqual(setup.run(), 2)
            launch.assert_not_called()

    def test_only_exact_instance_and_standard_render_are_selected(self):
        instance = r"ROOT\MEDIA\0001"
        standard = endpoint("{0.0.0.a}", "CABLE Input", instance)
        devices = [standard, endpoint("{0.0.0.b}", "CABLE In 16ch", instance),
                   endpoint("{0.0.0.c}", "CABLE Input", r"ROOT\MEDIA\0002"),
                   endpoint("{0.0.1.d}", "CABLE Output", instance)]
        self.assertEqual(standard_render_id(devices, instance), standard.id)
        standard.properties[ENDPOINT_NAME_PROPERTY] = "HomePodCast"
        standard.properties[ENDPOINT_FORM_FACTOR] = 1
        self.assertEqual(standard_render_id(devices, instance), standard.id)
        self.assertEqual(len(matching_endpoints(devices, instance)), 3)
        self.assertIsNone(standard_render_id(devices + [endpoint("{0.0.0.e}", "CABLE Input", instance)], instance))
        standard.state = 2
        self.assertIsNone(standard_render_id(devices, instance))

    def test_restore_does_not_override_manual_switch_or_missing_device(self):
        backend = Mock()
        backend.com_error = OSError
        current = {0: "cable", 1: "manual", 2: "cable"}
        backend.enumerator.GetDefaultAudioEndpoint.side_effect = lambda flow, role: SimpleNamespace(GetId=lambda: current[role])
        backend.enumerator.GetDevice.return_value.GetState.return_value = 1
        backend.api.GetEndpointDataFlow.return_value = 0
        backend.api.SetDefaultDevice.side_effect = lambda device, roles: current.update({roles[0].value: device})
        failures = restore_changed_defaults(backend, {"0:0": "speakers", "0:1": "speakers", "0:2": None}, {"cable"})
        self.assertEqual(failures, [])
        self.assertEqual(current, {0: "speakers", 1: "manual", 2: "cable"})
        self.assertEqual(backend.api.SetDefaultDevice.call_count, 1)

    def test_config_preserves_other_settings_and_invalid_config(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"language":"en","custom":42}', encoding="utf-8")
            save_virtual_config(path, "virtual-id")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual((data["language"], data["custom"]), ("en", 42))
            self.assertEqual((data["audio_mode"], data["source"], data["auto_switch_output"]),
                             ("virtual", "virtual-id", True))
            path.write_text("broken", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                save_virtual_config(path, "another")
            self.assertEqual(path.read_text(encoding="utf-8"), "broken")


if __name__ == "__main__":
    unittest.main()
