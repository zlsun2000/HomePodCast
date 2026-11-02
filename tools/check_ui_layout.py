"""Construct real Tk widgets with network/startup/tray side effects mocked."""

from pathlib import Path
import queue
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def main():
    for language in ("zh", "en"):
        config = dict(language=language, mode="quad", hinted=True, audio_mode="virtual",
                      future_setting="preserve")
        fake_tray = Mock(clicks=queue.Queue())
        fake_engine = Mock()
        fake_engine.status.return_value = dict(state="idle", error=None, routing_error=None)
        with (patch.object(app, "load_config", return_value=config),
              patch.object(app, "save_config"), patch.object(app, "set_startup"),
              patch.object(app, "startup_command", return_value=None),
              patch.object(app.eng, "Engine", return_value=fake_engine),
              patch.object(app.tray, "Tray", return_value=fake_tray),
              patch.object(app.App, "scan"), patch.object(app.App, "check")):
            ui = app.App()
            try:
                ui.show_settings = True
                ui.place_settings()
                ui.root.update_idletasks()
                requested = ui.root.winfo_reqheight()
                screen = ui.root.winfo_screenheight()
                print(dict(language=language, requested_height=requested, screen_height=screen,
                           settings_height=ui.settings.winfo_height()))
                assert requested < screen - 60, "Settings extend beyond the screen"
                ui.refresh_sources()
                ui.remember()
                assert ui.config["audio_mode"] == "virtual"
                assert ui.config["schema_version"] == 2
                assert ui.config["future_setting"] == "preserve"
            finally:
                if ui.audio_monitor:
                    ui.audio_monitor.close()
                for timer in ui.root.tk.call("after", "info"):
                    ui.root.after_cancel(timer)
                ui.root.destroy()


if __name__ == "__main__":
    main()
