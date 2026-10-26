"""Check isolation and packaging invariants before compiling kernel code."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

MODULE = Path(__file__).resolve().parents[1] / "prepare_prototype.py"
spec = importlib.util.spec_from_file_location("prepare_prototype", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PrototypePreparationTests(unittest.TestCase):
    def test_prepares_real_pinned_source_without_modifying_it(self):
        source = MODULE.parents[1] / ".driver-source"
        if not source.exists():
            self.skipTest("Fetch locked upstream first")
        tracked_inputs = [source / "audio/sysvad/adapter.cpp",
                          source / "audio/sysvad/TabletAudioSample/minipairs.h",
                          source / "audio/sysvad/TabletAudioSample/TabletAudioSample.vcxproj"]
        before = {path: path.read_bytes() for path in tracked_inputs}
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "prototype"
            module.prepare(source, destination)
            tablet = destination / "audio/sysvad/TabletAudioSample"
            props = ET.parse(destination / "Directory.Build.props")
            self.assertTrue(all(str(source / "packages") in child.attrib["Project"]
                                for child in props.getroot()))
            ns = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
            project = ET.parse(tablet / "TabletAudioSample.vcxproj")
            infs = project.findall(".//m:Inf", ns)
            self.assertEqual([item.attrib["Include"] for item in infs], ["HomePodCastAudio.inx"])
            self.assertEqual({e.text for e in project.findall(".//m:TargetName", ns)},
                             {"HomePodCastAudio"})
            self.assertNotIn("SYSVAD_BTH_BYPASS", (tablet / "TabletAudioSample.vcxproj").read_text())
            self.assertNotIn('L"DoNotCreateDataFiles"',
                             (destination / "audio/sysvad/adapter.cpp").read_text())
            self.assertIn("Root\\HomePodCastAudio", (tablet / "HomePodCastAudio.inx").read_text())
            self.assertTrue((destination / "UPSTREAM-LICENSE.txt").exists())
            with self.assertRaises(ValueError):
                module.prepare(source, destination)
        self.assertEqual(before, {path: path.read_bytes() for path in tracked_inputs})

    def test_rejects_destination_inside_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            with self.assertRaises(ValueError):
                module.prepare(source, source / "nested")


if __name__ == "__main__":
    unittest.main()
