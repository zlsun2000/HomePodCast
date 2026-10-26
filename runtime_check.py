"""Read-only packaged-runtime smoke check, without application startup settings."""

import json
from pathlib import Path


def run(output_path):
    import customtkinter as ctk
    import soundcard as sc
    import pyatv
    from windows_audio import WindowsAudio

    report = {"ok": False}
    backend = None
    root = None
    try:
        root = ctk.CTk()
        root.withdraw()
        root.update_idletasks()
        backend = WindowsAudio()
        report.update(defaults={str(r): backend.default(r) for r in (0, 1, 2)},
                      sources=[dict(id=s.id, name=s.name, channels=s.channels) for s in sc.all_speakers()],
                      pyatv_imported=pyatv is not None, tk_initialized=True, ok=True)
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if backend:
            backend.close()
        if root:
            root.destroy()
    Path(output_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1
