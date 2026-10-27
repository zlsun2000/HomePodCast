"""Generate an isolated HomePodCast build tree from the verified SysVAD cache.

Never modify the baseline checkout. Upstream source retains its MS-PL license;
HomePodCast-owned endpoint descriptors and packaging are separate overlay files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from xml.sax.saxutils import escape


def prepare(source: Path, destination: Path) -> None:
    source = source.resolve()
    destination = destination.resolve()
    if destination.exists():
        raise ValueError("Destination already exists; use a fresh prototype directory")
    if source == destination or source in destination.parents:
        raise ValueError("Prototype must be outside the baseline source tree")
    overlay = Path(__file__).parent / "prototype"
    sysvad = destination / "audio/sysvad"
    shutil.copytree(source / "audio/sysvad", sysvad,
                    ignore=shutil.ignore_patterns("x64", "ARM64", "Debug", "Release",
                                                 "*.user", "*.log", "*.binlog"))
    # Restore stays in the baseline cache. Absolute imports avoid a second copy
    # of the large SDK/WDK packages, and never import an unpinned system kit.
    props = (source / "Directory.Build.props").read_text(encoding="utf-8-sig")
    props = props.replace('Project="packages\\',
                          'Project="' + escape(str(source / "packages"), {'"': '&quot;'}) + '\\')
    props = props.replace("Exists('packages\\", "Exists('" +
                          escape(str(source / "packages"), {"'": "&apos;"}) + "\\")
    (destination / "Directory.Build.props").write_text(props, encoding="utf-8")
    shutil.copy2(source / "LICENSE", destination / "UPSTREAM-LICENSE.txt")
    tablet = sysvad / "TabletAudioSample"
    for path in overlay.iterdir():
        shutil.copy2(path, tablet / path.name)
    for project in sysvad.rglob("*.vcxproj"):
        content = project.read_text(encoding="utf-8-sig")
        # No Bluetooth/USB endpoint registration in this virtual-only driver.
        content = content.replace("SYSVAD_BTH_BYPASS;", "").replace(";SYSVAD_BTH_BYPASS", "")
        content = content.replace("SYSVAD_USB_SIDEBAND;", "").replace(";SYSVAD_USB_SIDEBAND", "")
        if project.parent == tablet:
            content = content.replace("<TargetName>TabletAudioSample</TargetName>",
                                      "<TargetName>HomePodCastAudio</TargetName>")
            content = content.replace('Include="*.inx"', 'Include="HomePodCastAudio.inx"')
            for unused in ("micintopo.cpp", "hdmitopo.cpp", "spdiftopo.cpp"):
                content = content.replace(f'    <ClCompile Include="{unused}" />\n', "")
        project.write_text(content, encoding="utf-8")
    # Force the null sink: never allow the sample registry switch to enable
    # recording render PCM into files on disk.
    adapter = sysvad / "adapter.cpp"
    lines = adapter.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    matches = [line for line in lines if 'L"DoNotCreateDataFiles"' in line]
    if len(matches) != 1:
        raise ValueError("Upstream data-file registry entry changed")
    adapter.write_text("".join(line for line in lines if line not in matches), encoding="utf-8")
    # Upstream has eight sideband branches missing the conditional compilation
    # guards used elsewhere. Guard them when building without Bluetooth/USB.
    engine_node = sysvad / "EndpointsCommon/MiniportAudioEngineNode.cpp"
    text = engine_node.read_text(encoding="utf-8-sig")
    marker = "    if (IsSidebandDevice() && "
    if text.count(marker) != 8:
        raise ValueError("Upstream audio-engine sideband branches changed")
    cursor = len(text)
    for _ in range(8):
        start = text.rfind(marker, 0, cursor)
        end = text.index("\n    }", start) + len("\n    }")
        if text[end:].startswith("\n    else"):
            end += len("\n    else")
        text = (text[:start] + "#if defined(SYSVAD_BTH_BYPASS) || defined(SYSVAD_USB_SIDEBAND)\n" +
                text[start:end] + "\n#endif" + text[end:])
        cursor = start
    engine_node.write_text(text, encoding="utf-8")
    # Match the miniport's own QI policy: a software endpoint has no hardware
    # engine controls. Do not expose the sample's simulated stream gain/mute.
    stream = sysvad / "EndpointsCommon/minwavertstream.cpp"
    text = stream.read_text(encoding="utf-8-sig")
    for interface in ("IID_IMiniportStreamAudioEngineNode", "IID_IMiniportStreamAudioEngineNode2"):
        original = f"IsEqualGUIDAligned(Interface, {interface}))"
        if text.count(original) != 1:
            raise ValueError("Upstream stream-engine QI changed")
        text = text.replace(original, f"IsEqualGUIDAligned(Interface, {interface}) && m_pMiniport->IsOffloadSupported())")
    stream.write_text(text, encoding="utf-8")
    resource = tablet / "TabletAudioSample.rc"
    text = resource.read_text(encoding="utf-8-sig")
    text = text.replace("Microsoft Virtual Audio Tablet Sample Driver", "HomePodCast Audio Prototype")
    resource.write_text(text.replace("TabletAudioSample.sys", "HomePodCastAudio.sys"), encoding="utf-8")
    manifest = {
        "artifactKind": "homepodcast-audio-prototype",
        "transport": "wasapi-software-loopback",
        "hardwareId": r"Root\HomePodCastAudio",
        "runtimeVerified": False,
        "generatorSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "overlaySha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(overlay.iterdir())},
    }
    (destination / "prototype-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.source, args.destination)
