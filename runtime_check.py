"""Read-only packaged-runtime smoke check, without application startup settings."""

import json
from pathlib import Path


def check_authentication():
    """Exercise the pyatv/SRP API used by AirPlay, entirely offline."""
    import binascii
    import hashlib
    from pyatv.auth.hap_srp import SRPAuthHandler
    from srptools import SRPContext, SRPServerSession, constants

    options = dict(prime=constants.PRIME_3072, generator=constants.PRIME_3072_GEN,
                   hash_func=hashlib.sha512)
    context = SRPContext("Pair-Setup", "1234", **options)
    username, verifier, salt = context.get_user_data_triplet()
    server = SRPServerSession(SRPContext(username, **options), verifier)
    client = SRPAuthHandler()
    client.initialize()
    client.step1(1234)
    public, proof = client.step2(bytes.fromhex(server.public), bytes.fromhex(salt))
    server.process(public.hex(), salt)
    if not server.verify_proof(binascii.hexlify(proof)) or client.shared_key != server.key:
        raise RuntimeError("AirPlay SRP authentication dependency check failed")
    if not client.step3():
        raise RuntimeError("AirPlay encryption dependency check failed")


def run(output_path):
    report = {"ok": False}
    backend = None
    root = None
    try:
        import customtkinter as ctk
        import soundcard as sc
        import pyatv
        from windows_audio import WindowsAudio
        from virtual_audio_setup import load_audio_api
        from drivers.audio_mute import apply_endpoint_mute

        check_authentication()
        load_audio_api()
        root = ctk.CTk()
        root.withdraw()
        root.update_idletasks()
        backend = WindowsAudio()
        report.update(defaults={str(r): backend.default(r) for r in (0, 1, 2)},
                      sources=[dict(id=s.id, name=s.name, channels=s.channels) for s in sc.all_speakers()],
                      pyatv_imported=pyatv is not None, tk_initialized=True,
                      authentication_checked=True, mute_helper_loaded=callable(apply_endpoint_mute), ok=True)
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if backend:
            backend.close()
        if root:
            root.destroy()
    Path(output_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1
