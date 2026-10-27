"""Independently verify the prototype artifact's file hashes and PE architecture."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def verify(root, require_test_package=False):
    root = Path(root).resolve()
    manifest = json.loads((root / "build-manifest.json").read_text(encoding="utf-8-sig"))
    if manifest.get("artifactKind") != "homepodcast-audio-prototype" or manifest.get("buildSucceeded") is not True:
        raise ValueError("Not a successfully compiled HomePodCast prototype")
    if manifest.get("infVerified") is not True:
        raise ValueError("INF verification evidence missing")
    if manifest.get("prototype", {}).get("runtimeVerified") is not False:
        raise ValueError("Build artifacts must not claim runtime verification")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Artifact has no hashed files")
    checked = set()
    for entry in files:
        path = (root / entry["path"].replace("\\", "/")).resolve()
        if root not in path.parents or path in checked:
            raise ValueError("Unsafe or duplicate manifest path")
        checked.add(path)
        if hashlib.sha256(path.read_bytes()).hexdigest().lower() != entry["sha256"].lower():
            raise ValueError(f"File hash mismatch: {path.name}")
        if path.suffix.casefold() == ".sys":
            content = path.read_bytes()
            if content[:2] != b"MZ" or len(content) < 64:
                raise ValueError("Invalid driver DOS header")
            pe = struct.unpack_from("<I", content, 60)[0]
            if pe + 94 > len(content) or content[pe:pe + 4] != b"PE\0\0":
                raise ValueError("Invalid driver PE header")
            if (struct.unpack_from("<H", content, pe + 4)[0] != 0x8664 or
                    struct.unpack_from("<H", content, pe + 24)[0] != 0x20B or
                    struct.unpack_from("<H", content, pe + 24 + 68)[0] != 1):
                raise ValueError("Expected an x64 PE32+ native driver")
    drivers = [path for path in checked if path.suffix.casefold() == ".sys"]
    if not drivers or any(path.name != "HomePodCastAudio.sys" for path in drivers):
        raise ValueError("Expected only the HomePodCast driver binary")
    if require_test_package:
        if manifest.get("packageSucceeded") is not True or manifest.get("signing") != "ephemeral-development-test":
            raise ValueError("Test signing did not complete")
        package = root / "test-package"
        for name in ("HomePodCastAudio.sys", "HomePodCastAudio.inf", "HomePodCastAudio.cat", "HomePodCast-Development.cer"):
            if package / name not in checked:
                raise ValueError(f"Test package is missing a hashed file: {name}")
        signing = json.loads((package / "test-signing.json").read_text(encoding="utf-8-sig"))
        if (signing.get("catalogVerified") is not True or signing.get("privateKeyExported") is not False or
                signing.get("runtimeVerified") is not False):
            raise ValueError("Invalid signing evidence")
        if list(root.rglob("*.pfx")) or list(root.rglob("*.p12")):
            raise ValueError("Private key container must not be published")
    return {"passed": True, "checked_files": len(checked), "runtime_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--require-test-package", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.require_test_package), indent=2))
