import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "verify_artifact", Path(__file__).resolve().parents[1] / "verify_artifact.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ArtifactVerificationTests(unittest.TestCase):
    def fixture(self, root):
        # Deliberately minimal PE fixture, sufficient only for header checks.
        binary = bytearray(256)
        binary[:2] = b"MZ"
        struct.pack_into("<I", binary, 60, 64)
        binary[64:68] = b"PE\0\0"
        struct.pack_into("<H", binary, 68, 0x8664)
        struct.pack_into("<H", binary, 88, 0x20B)
        struct.pack_into("<H", binary, 156, 1)
        path = root / "HomePodCastAudio.sys"
        path.write_bytes(binary)
        manifest = {"artifactKind": "homepodcast-audio-prototype", "buildSucceeded": True,
                    "infVerified": True, "prototype": {"runtimeVerified": False},
                    "files": [{"path": path.name, "sha256": hashlib.sha256(binary).hexdigest()}]}
        (root / "build-manifest.json").write_text(json.dumps(manifest))
        return path, manifest

    def test_accepts_headers_then_rejects_tampered_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, manifest = self.fixture(root)
            self.assertTrue(module.verify(root)["passed"])
            path.write_bytes(path.read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                module.verify(root)

    def test_rejects_traversal_and_unverified_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, manifest = self.fixture(root)
            with self.assertRaisesRegex(ValueError, "Test signing did not complete"):
                module.verify(root, True)
            manifest["files"][0]["path"] = "../outside.sys"
            (root / "build-manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                module.verify(root)

    def test_rejects_x86_driver_even_if_hash_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, manifest = self.fixture(root)
            data = bytearray(path.read_bytes())
            struct.pack_into("<H", data, 68, 0x14C)
            path.write_bytes(data)
            manifest["files"][0]["sha256"] = hashlib.sha256(data).hexdigest()
            (root / "build-manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "x64 PE32"):
                module.verify(root)
