"""Create a read-only VirtualBox CD containing one verified CI test package."""
import argparse
import hashlib
import importlib.util
import io
import ipaddress
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".driver-packages/iso-tools"))
import pycdlib

spec = importlib.util.spec_from_file_location("verify_artifact", ROOT / "drivers/verify_artifact.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

FILES = (
    ("test-package/HomePodCastAudio.sys", "HPCSYS.SYS;1", "HomePodCastAudio.sys"),
    ("test-package/HomePodCastAudio.inf", "HPCINF.INF;1", "HomePodCastAudio.inf"),
    ("test-package/homepodcastaudio.cat", "HPCCAT.CAT;1", "HomePodCastAudio.cat"),
    ("test-package/HomePodCast-Development.cer", "HPCCERT.CER;1", "HomePodCast-Development.cer"),
    ("test-package/test-signing.json", "SIGNING.JSN;1", "test-signing.json"),
    ("build-manifest.json", "MANIFEST.JSN;1", "build-manifest.json"),
    ("probe-requirements.txt", "REQUIRES.TXT;1", "probe-requirements.txt"),
    ("UPSTREAM-LICENSE.txt", "MSPL.TXT;1", "UPSTREAM-LICENSE.txt"),
)


def create(artifact, output, receiver_address=""):
    artifact, output = Path(artifact).resolve(), Path(output).resolve()
    if receiver_address:
        receiver_address = str(ipaddress.ip_address(receiver_address))
    if output.exists():
        raise ValueError("Output already exists; choose a new file")
    verifier.verify(artifact, require_test_package=True)
    files = []
    for relative, iso_name, joliet_name in FILES:
        source = (artifact / relative).resolve()
        if artifact not in source.parents or not source.is_file():
            raise ValueError(f"Missing expected artifact: {relative}")
        files.append((source, iso_name, joliet_name))
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, vol_ident="HPC_LAN")
    try:
        iso.add_directory(iso_path='/DRIVERS', joliet_path='/drivers')
        for source, iso_name, joliet_name in files:
            iso.add_file(str(source), iso_path=f"/{iso_name}", joliet_path=f"/{joliet_name}")
        guest_files = ((ROOT / "drivers/probe_endpoint.py", "PROBE.PY;1", "probe_endpoint.py"),
                       (ROOT / "drivers/audio_mute.py", "MUTE.PY;1", "audio_mute.py"),
                       (ROOT / "tools/guest/Prepare-VM.ps1", "PREPARE.PS1;1", "Prepare-VM.ps1"),
                       (ROOT / "tools/guest/Run-Prepare-VM.cmd", "RUNPREP.CMD;1", "Run-Prepare-VM.cmd"),
                       (ROOT / "tools/guest/Test-Audio.ps1", "TEST.PS1;1", "Test-Audio.ps1"),
                       (ROOT / "tools/guest/Run-Audio-Test.cmd", "RUNTEST.CMD;1", "Run-Audio-Test.cmd"),
                       (ROOT / "engine.py", "ENGINE.PY;1", "engine.py"),
                       (ROOT / "drivers/audio_mute.py", "DRIVERS/MUTE.PY;1", "drivers/audio_mute.py"),
                       (ROOT / "tools/guest/vm_homepod_test.py", "HOMETEST.PY;1", "vm_homepod_test.py"),
                       (ROOT / "tools/guest/Run-HomePod-Test.cmd", "RUNHOME.CMD;1", "Run-HomePod-Test.cmd"),
                       (ROOT / "tools/guest/Test-HomePod.ps1", "HOME.PS1;1", "Test-HomePod.ps1"))
        for source, iso_name, joliet_name in guest_files:
            iso.add_file(str(source), iso_path=f"/{iso_name}", joliet_path=f"/{joliet_name}")
        receiver_data = (receiver_address + "\n").encode("ascii")
        iso.add_fp(io.BytesIO(receiver_data), len(receiver_data),
                   iso_path="/RECVADDR.TXT;1", joliet_path="/receiver-address.txt")
        readme = ("HomePodCast Audio experimental test package\r\n"
                  "For use in the isolated Windows test VM only.\r\n"
                  "This is test-signed, not a production driver.\r\n"
                  "Keep the original test-signing.json and development certificate together.\r\n"
                  "See the project drivers/README.md for setup and removal instructions.\r\n").encode("ascii")
        iso.add_fp(io.BytesIO(readme), len(readme), iso_path="/README.TXT;1", joliet_path="/README.txt")
        output.parent.mkdir(parents=True, exist_ok=True)
        iso.write(str(output))
    finally:
        iso.close()
    # Read the CD image back and verify every copied byte before use.
    check = pycdlib.PyCdlib()
    check.open(str(output))
    try:
        for source, _, joliet_name in [*files, *guest_files]:
            content = io.BytesIO()
            check.get_file_from_iso_fp(content, joliet_path=f"/{joliet_name}")
            if hashlib.sha256(content.getvalue()).digest() != hashlib.sha256(source.read_bytes()).digest():
                raise ValueError(f"Media verification failed: {joliet_name}")
        content = io.BytesIO()
        check.get_file_from_iso_fp(content, joliet_path="/receiver-address.txt")
        if content.getvalue() != receiver_data:
            raise ValueError("Media verification failed: receiver-address.txt")
    finally:
        check.close()
    return hashlib.sha256(output.read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receiver-address", default="", help="HomePod IP for the optional audible test")
    args = parser.parse_args()
    print(f"Created and verified {args.output}: SHA256 {create(args.artifact, args.output, args.receiver_address)}")
