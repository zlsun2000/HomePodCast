"""Check the two languages and virtual audio setup with real Tk widgets."""

from concurrent.futures import Future
from pathlib import Path
import queue
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def main():
    for language in ("zh", "en"):
        config = dict(language=language, mode="quad", hinted=True, audio_mode="physical",
                      software_volume=language == "zh", future_setting="preserve")
        speakers = ("speakers", "Speakers", 2)
        cable = ("cable", "CABLE Input (VB-Audio Virtual Cable)", 2)
        alternate = ("alternate", "CABLE In 16ch (VB-Audio Virtual Cable)", 16)
        second_cable = ("second", "CABLE Input (2- VB-Audio Virtual Cable)", 2)
        fake_tray = Mock(clicks=queue.Queue())
        fake_engine = Mock()
        fake_engine.status.return_value = dict(state="idle", error=None, routing_error=None)
        with (patch.object(app, "load_config", return_value=config),
              patch.object(app, "save_config") as save_config, patch.object(app, "set_startup"),
              patch.object(app, "startup_command", return_value=None),
              patch.object(app.webbrowser, "open") as open_browser,
              patch.object(app.os, "startfile") as open_windows_settings,
              patch.object(app.eng, "list_sources", return_value=[speakers]) as list_sources,
              patch.object(app.eng, "Engine", return_value=fake_engine),
              patch.object(app.tray, "Tray", return_value=fake_tray),
              patch.object(app.App, "scan"), patch.object(app.App, "check")):
            ui = app.App()
            try:
                ui.root.deiconify()
                ui.root.update_idletasks()
                assert ui.sources[ui.source_index] == speakers
                assert not ui.settings.winfo_manager()
                assert ui.cable_setup_button.winfo_manager() == "pack"
                assert not ui.cable_help_button.winfo_manager()
                open_browser.assert_not_called()

                ui.cable_setup_button.invoke()
                guide = ui.cable_guide
                ui.root.update_idletasks()
                assert guide.download_button.winfo_viewable()
                assert guide.result_heading.cget("text") == ui.tr("cable_step_detect")
                assert guide.winfo_reqheight() < guide.winfo_screenheight() - 60
                assert guide.winfo_reqwidth() < guide.winfo_screenwidth() - 40
                assert guide.sound_settings_button.winfo_viewable()
                open_browser.assert_not_called()
                guide.download_button.invoke()
                open_browser.assert_called_once_with(
                    "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack46.zip"
                )
                guide.website_button.invoke()
                open_browser.assert_called_with("https://vb-audio.com/Cable/")
                guide.sound_settings_button.invoke()
                open_windows_settings.assert_called_once_with("ms-settings:sound")
                save_config.assert_not_called()
                assert ui.audio_mode == "physical"

                list_sources.side_effect = RuntimeError("Device enumeration failed")
                guide.detect_button.invoke()
                assert guide.result_text.cget("text") == ui.tr("cable_detect_failed")
                list_sources.side_effect = None
                list_sources.return_value = [speakers, (cable[0], cable[1], 0), alternate]
                guide.detect_button.invoke()
                assert guide.endpoint_id is None
                assert guide.result_text.cget("text") == ui.tr("cable_not_found")

                list_sources.return_value = [speakers, cable, alternate]
                guide.detect_button.invoke()
                assert guide.endpoint_id == "cable"
                assert guide.confirm.cget("text") == ui.tr("cable_apply")
                assert not guide.install_steps.winfo_manager()
                list_sources.return_value = [speakers]
                guide.confirm.invoke()
                assert guide.endpoint_id is None
                assert ui.audio_mode == "physical"
                save_config.assert_not_called()

                list_sources.return_value = [speakers, cable, second_cable, alternate]
                guide.detect_button.invoke()
                assert guide.endpoint_id is None
                assert guide.result_heading.cget("text") == ui.tr("cable_multiple")
                guide.confirm.invoke()
                assert ui.cable_guide is None
                assert ui.settings.winfo_manager() == "pack"
                assert ui.sources[ui.source_index][0] is None
                assert not ui.auto_switch_output
                save_config.assert_not_called()

                list_sources.return_value = [speakers]
                ui.set_audio_mode(ui.tr("virtual_mode"))
                assert ui.cable_help_button.winfo_manager() == "pack"
                assert ui.audio_mode_hint.cget("text") == ui.tr("cable_setup_hint")
                assert not ui.virtual_settings.winfo_manager()
                ui.set_audio_mode(ui.tr("physical_mode"))
                assert ui.audio_mode == "physical"

                list_sources.return_value = [speakers, cable, alternate]
                ui.cable_setup_button.invoke()
                guide = ui.cable_guide
                assert guide.confirm.cget("text") == ui.tr("cable_apply")
                guide.confirm.invoke()
                assert ui.sources[ui.source_index] == cable
                assert ui.auto_output_box.get()
                config_saved = save_config.call_args.args[0]
                assert config_saved["audio_mode"] == "virtual"
                assert config_saved["source"] == "cable"
                assert config_saved["auto_switch_output"]
                assert config_saved["software_volume"] == config["software_volume"]
                assert guide.result_heading.cget("text") == ui.tr("cable_configured")
                volume_key = "cable_adjust_software" if config["software_volume"] else "cable_adjust"
                assert guide.volume_hint.cget("text") == ui.tr(volume_key)
                guide.confirm.invoke()
                assert ui.cable_guide is None
                assert not ui.cable_setup_button.winfo_manager()
                assert ui.cable_help_button.winfo_manager() == "pack"
                assert ui.virtual_settings.winfo_manager() == "pack"
                fake_engine.start.assert_not_called()
                fake_engine.recover_output.assert_not_called()

                ui.root.update_idletasks()
                requested = ui.root.winfo_reqheight()
                screen = ui.root.winfo_screenheight()
                print(dict(language=language, requested_height=requested, screen_height=screen,
                           settings_height=ui.settings.winfo_height()))
                assert requested < screen - 60, "Settings extend beyond the screen"
                ui.remember()
                assert ui.config["audio_mode"] == "virtual"
                assert ui.config["schema_version"] == 2
                assert ui.config["future_setting"] == "preserve"

                for role, picker in ui.role_vars.items():
                    ui.confs[role] = Mock(identifier=role)
                    picker.set(role)
                fake_engine.start.return_value = Future()
                ui.toggle()
                assert fake_engine.start.call_args.args[2] == "cable"
                assert fake_engine.start.call_args.kwargs["route_options"] is not None
                assert ui.cable_help_button.cget("state") == "disabled"
            finally:
                if ui.cable_guide is not None:
                    ui.close_cable_guide()
                if ui.audio_monitor:
                    ui.audio_monitor.close()
                for timer in ui.root.tk.call("after", "info"):
                    ui.root.after_cancel(timer)
                ui.root.destroy()


if __name__ == "__main__":
    main()
