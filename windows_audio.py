"""Windows audio operations. Construct and use only on one MTA thread."""

import ctypes
import queue
import sys
import threading


class WindowsAudio:
    def __init__(self):
        self.thread = threading.get_ident()
        hr = ctypes.windll.ole32.CoInitializeEx(None, 0)
        if hr not in (0, 1):
            raise OSError(f"Cannot initialize audio COM apartment: {hr:#x}")
        self.closed = False
        try:
            sys.coinit_flags = 0
            import comtypes
            from pycaw.utils import AudioUtilities
            from pycaw.callbacks import MMNotificationClient

            self.api = AudioUtilities
            self.com_error = comtypes.COMError
            self.enumerator = AudioUtilities.GetDeviceEnumerator()
            self.events = queue.SimpleQueue()
            self.devices_changed = threading.Event()
            events = self.events
            devices_changed = self.devices_changed

            class Notifications(MMNotificationClient):
                def on_default_device_changed(self, flow, flow_id, role, role_id, device_id):
                    if flow_id == 0:
                        events.put((role_id, device_id))

                def on_device_added(self, device_id):
                    devices_changed.set()

                def on_device_removed(self, device_id):
                    devices_changed.set()

                def on_device_state_changed(self, device_id, state, state_id):
                    devices_changed.set()

                def on_property_value_changed(self, *args):
                    devices_changed.set()

            self.notifications = Notifications()
            self.enumerator.RegisterEndpointNotificationCallback(self.notifications)
        except BaseException:
            ctypes.windll.ole32.CoUninitialize()
            raise

    def _check(self):
        if self.closed or threading.get_ident() != self.thread:
            raise RuntimeError("Audio controller used outside its owning thread")

    def default(self, role):
        self._check()
        try:
            return self.enumerator.GetDefaultAudioEndpoint(0, role).GetId()
        except (OSError, self.com_error):
            return None

    def available(self, endpoint):
        self._check()
        if not endpoint:
            return False
        try:
            return (self.enumerator.GetDevice(endpoint).GetState() == 1 and
                    self.api.GetEndpointDataFlow(endpoint, 1) == 0)
        except (OSError, self.com_error):
            return False

    def set_default(self, endpoint, role):
        self._check()
        from pycaw.constants import ERole

        if not self.available(endpoint):
            raise RuntimeError("Output endpoint unavailable")
        self.api.SetDefaultDevice(endpoint, roles=[ERole(role)])
        if self.default(role) != endpoint:
            raise RuntimeError("Windows did not apply the requested default output")

    def changes(self):
        self._check()
        result = []
        while True:
            try:
                result.append(self.events.get_nowait())
            except queue.Empty:
                return result

    def muted(self, endpoint):
        self._check()
        device = self.api.CreateDevice(self.enumerator.GetDevice(endpoint))
        volume = device.EndpointVolume
        return bool(volume.GetMute()) or volume.GetMasterVolumeLevelScalar() <= 0

    def close(self):
        self._check()
        try:
            self.enumerator.UnregisterEndpointNotificationCallback(self.notifications)
        finally:
            self.enumerator = self.notifications = None
            self.closed = True
            ctypes.windll.ole32.CoUninitialize()
