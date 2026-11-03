"""Interactive, fail-closed setup for the bundled VB-Audio virtual endpoint.

The vendor installer is never run when a matching device is present, disabled,
broken, or cannot be queried. A leftover service without a device is handled
interactively by the vendor installer. Ordinary startup never installs a driver.
"""

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import messagebox

HARDWARE_ID = "VBAUDIOVACWDM"
HARDWARE_PROPERTY = "{A8B865DD-2E3D-4094-AD97-E593A70C75D6} 8"
INSTANCE_PROPERTY = "{B3F8FA53-0004-438E-9003-51A46E139BFC} 2"
ENDPOINT_NAME_PROPERTY = "{A45C254E-DF1C-4EFD-8020-67D146A850E0} 2"
ENDPOINT_FORM_FACTOR = "{1DA5D803-D492-4EDD-8C23-E0C0FFEE7F0E} 0"
PACKAGE_HASHES = {
    "VBCABLE_Setup_x64.exe": "734c35dfa6d98f48782a451633ceb471166ec70d60482fd89a1123d0ee3c4f41",
    "vbaudio_cable64_win10.cat": "0a921ebadbe39cf3fa7c14ff37d1ca22565a9651244bd3ac177dc810bc99072e",
    "vbMmeCable64_win10.inf": "61c857be74831cc299d9be62f8d49d137f14063454fc54f859d5bc9b4b813daf",
    "vbaudio_cable64_win10.sys": "f01344602472f1b527de5ee98f18987c03db48fea444e457d061e937f1d531d5",
    "vbaudio_cable64arm_win10.sys": "2dc35db3dfad0f25771a3e59af38e8b1268878ebe127476ea75fee109f2927dd",
}

PNP_QUERY = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$cableDevices = @(Get-PnpDevice -Class MEDIA | Where-Object { $_.InstanceId -like 'ROOT\*' } | ForEach-Object {
  $ids = (Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName DEVPKEY_Device_HardwareIds -ErrorAction Stop).Data
  if (@($ids) -contains 'VBAudioVACWDM') {
    $provider = (Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName DEVPKEY_Device_DriverProvider -ErrorAction Stop).Data
    [pscustomobject]@{ instance = $_.InstanceId; status = [string]$_.Status; provider = [string]$provider }
  }
})
if ($cableDevices.Count -eq 0 -and (Get-Service -Name 'VBAudioVACMME' -ErrorAction SilentlyContinue)) {
  $cableDevices = @([pscustomobject]@{ instance = ''; status = 'Unknown'; provider = '' })
}
ConvertTo-Json -InputObject $cableDevices -Compress
'''


def classify_devices(devices):
    """Identify a matching device separately from a leftover driver service."""
    if not devices:
        return "missing"
    if len(devices) == 1 and devices[0].get("instance") == "" and devices[0].get("status") == "Unknown":
        return "residual_service"
    if (len(devices) == 1 and devices[0].get("status") == "OK"
            and devices[0].get("provider", "").casefold() == "vb-audio software"):
        return "ready"
    return "needs_attention"


def query_devices():
    result = subprocess.run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", PNP_QUERY],
        capture_output=True, encoding="utf-8", errors="replace", timeout=30,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False,
    )
    if result.returncode:
        raise RuntimeError("无法查询 Windows 音频驱动：" + result.stderr.strip())
    devices = json.loads(result.stdout)
    if not isinstance(devices, list):
        raise RuntimeError("Windows 返回的设备信息格式不正确")
    return devices


def matching_endpoints(devices, instance):
    """Bind endpoint to a verified PnP instance, not just its display name."""
    result = []
    marker = "." + instance.casefold()
    for device in devices:
        props = device.properties or {}
        if (str(props.get(HARDWARE_PROPERTY, "")).casefold() == HARDWARE_ID.casefold()
                and str(props.get(INSTANCE_PROPERTY, "")).casefold().endswith(marker)):
            result.append(device)
    return result


def standard_render_id(devices, instance):
    matches = [device.id for device in matching_endpoints(devices, instance)
               if ((device.properties or {}).get(ENDPOINT_FORM_FACTOR) == 1 or
                   ((device.properties or {}).get(ENDPOINT_FORM_FACTOR) is None and
                    str((device.properties or {}).get(ENDPOINT_NAME_PROPERTY, "")).casefold() == "cable input"))
               and device.id.startswith("{0.0.0.") and getattr(device.state, "value", device.state) == 1]
    return matches[0] if len(matches) == 1 else None


def snapshot_defaults(backend):
    result = {}
    for flow in (0, 1):
        for role in (0, 1, 2):
            try:
                result[f"{flow}:{role}"] = backend.enumerator.GetDefaultAudioEndpoint(flow, role).GetId()
            except (OSError, backend.com_error):
                result[f"{flow}:{role}"] = None
    return result


def restore_changed_defaults(backend, before, cable_ids):
    """Undo only changes to the newly installed cable; preserve user changes."""
    from pycaw.constants import ERole

    failures = []
    for key, original in before.items():
        flow, role = (int(part) for part in key.split(":"))
        try:
            current = backend.enumerator.GetDefaultAudioEndpoint(flow, role).GetId()
            if current == original or current not in cable_ids or not original:
                continue
            device = backend.enumerator.GetDevice(original)
            if device.GetState() != 1 or backend.api.GetEndpointDataFlow(original, 1) != flow:
                failures.append(key)
                continue
            backend.api.SetDefaultDevice(original, roles=[ERole(role)])
            if backend.enumerator.GetDefaultAudioEndpoint(flow, role).GetId() != original:
                failures.append(key)
        except Exception:
            failures.append(key)
    return failures


def run_vendor_setup(path):
    """Run the signed, unmodified vendor installer with its visible UI."""
    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("fMask", wintypes.ULONG),
                    ("hwnd", wintypes.HWND), ("lpVerb", wintypes.LPCWSTR),
                    ("lpFile", wintypes.LPCWSTR), ("lpParameters", wintypes.LPCWSTR),
                    ("lpDirectory", wintypes.LPCWSTR), ("nShow", ctypes.c_int),
                    ("hInstApp", wintypes.HINSTANCE), ("lpIDList", ctypes.c_void_p),
                    ("lpClass", wintypes.LPCWSTR), ("hkeyClass", wintypes.HKEY),
                    ("dwHotKey", wintypes.DWORD), ("hIcon", wintypes.HANDLE),
                    ("hProcess", wintypes.HANDLE)]

    shell = ctypes.windll.shell32
    kernel = ctypes.windll.kernel32
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(SHELLEXECUTEINFO)]
    shell.ShellExecuteExW.restype = wintypes.BOOL
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    info = SHELLEXECUTEINFO()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
    info.lpVerb = "runas"
    info.lpFile = str(path)
    info.lpDirectory = str(path.parent)
    info.nShow = 1
    if not shell.ShellExecuteExW(ctypes.byref(info)):
        raise ctypes.WinError()
    try:
        kernel.WaitForSingleObject(info.hProcess, 0xFFFFFFFF)
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(info.hProcess, ctypes.byref(code)):
            raise ctypes.WinError()
        return code.value
    finally:
        kernel.CloseHandle(info.hProcess)


def verify_vendor_files(directory):
    for name, expected in PACKAGE_HASHES.items():
        path = Path(directory) / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"VB-CABLE 文件校验失败：{name}")


def save_virtual_config(path, source_id):
    path = Path(path)
    if path.exists():
        with path.open(encoding="utf-8") as stream:
            config = json.load(stream)
        if not isinstance(config, dict):
            raise RuntimeError("HomePodCast 设置文件格式不正确")
    else:
        config = {}
    config.update(schema_version=2, audio_mode="virtual", source=source_id,
                  auto_switch_output=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         delete=False, prefix="config-", suffix=".tmp") as stream:
            temp_name = stream.name
            json.dump(config, stream, ensure_ascii=False, indent=1)
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def load_audio_api():
    # SoundCard initializes COM as MTA during app import. comtypes otherwise
    # defaults to STA and raises RPC_E_CHANGED_MODE before the wizard opens.
    sys.coinit_flags = 0
    from windows_audio import WindowsAudio
    from pycaw.utils import AudioUtilities

    return WindowsAudio, AudioUtilities


def run():
    import tray

    root = tk.Tk()
    root.withdraw()
    backend = None
    try:
        WindowsAudio, AudioUtilities = load_audio_api()
        if ctypes.windll.user32.FindWindowW(tray.WINDOW, None):
            messagebox.showwarning("HomePodCast", "请先退出正在运行的 HomePodCast，再配置虚拟音频。")
            return 2
        devices = query_devices()
        state = classify_devices(devices)
        if state == "needs_attention":
            messagebox.showwarning("HomePodCast", "检测到已有 VB-CABLE 设备，但状态异常或身份不明确。为避免误卸载，本程序不会重新运行驱动安装器。请检查设备管理器。")
            return 2
        if state in ("missing", "residual_service"):
            detail = ("未发现 VB-CABLE 音频设备，但检测到卸载后的驱动残留。"
                      if state == "residual_service" else "未检测到 VB-CABLE。")
            if not messagebox.askyesno("HomePodCast", detail + "是否启动随附的 VB-Audio 安装程序？\n\n驱动需要管理员确认。请在原版程序中选择 Install Driver；如果显示 Remove Driver，请不要点击并返回 HomePodCast。完成安装后按提示重启。\n\nVB-CABLE 是 VB-Audio 的 donationware：www.vb-cable.com"):
                return 1
            if not getattr(sys, "frozen", False):
                raise RuntimeError("请使用已安装的 HomePodCast 来安装随附驱动")
            installer = Path(sys.executable).parent / "VBCABLE" / "VBCABLE_Setup_x64.exe"
            if not installer.is_file():
                raise RuntimeError("未找到随附的 VB-CABLE 安装程序")
            verify_vendor_files(installer.parent)
            backend = WindowsAudio()
            before = snapshot_defaults(backend)
            # Recheck immediately before invoking the vendor's install/uninstall toggle.
            if classify_devices(query_devices()) not in ("missing", "residual_service"):
                raise RuntimeError("设备状态已变化；为避免误卸载，请重新运行配置向导")
            exit_code = run_vendor_setup(installer)
            devices = query_devices()
            if classify_devices(devices) == "ready":
                cable_ids = {d.id for d in matching_endpoints(AudioUtilities.GetAllDevices(), devices[0]["instance"])}
                failures = restore_changed_defaults(backend, before, cable_ids)
                if failures or not cable_ids:
                    messagebox.showwarning("HomePodCast", "无法恢复部分默认扬声器或麦克风，请在 Windows 声音设置中检查。")
            else:
                messagebox.showwarning("HomePodCast", "尚不能确认驱动和音频端点。请重启后检查 Windows 的默认扬声器和麦克风，再重新运行配置向导。")
            messagebox.showinfo("HomePodCast", "驱动安装程序已退出。请重启电脑，再从开始菜单运行“配置 HomePodCast 虚拟音频”。\n\n安装程序退出码：%s" % exit_code)
            return 0 if exit_code == 0 else 1
        source = standard_render_id(AudioUtilities.GetAllDevices(), devices[0]["instance"])
        if not source:
            messagebox.showwarning("HomePodCast", "VB-CABLE 已安装，但标准 CABLE Input 不可用或存在多个匹配项。请检查 Windows 声音设备后重试。")
            return 2
        if messagebox.askyesno("HomePodCast", "检测到 VB-CABLE。是否将 HomePodCast 设置为仅通过 HomePod 播放，并在停止时恢复电脑输出？\n\n这只修改 HomePodCast 的音源设置，不会立即切换 Windows 输出。"):
            config_path = Path(os.environ["APPDATA"]) / "HomePodCast" / "config.json"
            save_virtual_config(config_path, source)
            messagebox.showinfo("HomePodCast", "配置完成。打开 HomePodCast，选择 HomePod 并开始串流。\n\n若使用软件音量，请在管理员版 VB-CABLE 控制面板关闭 Enable Windows Volume Control，并在应用设置中启用软件音量。也可启用驱动音量、关闭应用软件音量；不要同时启用。请关闭录音设备的“侦听此设备”。")
        return 0
    except Exception as exc:
        messagebox.showerror("HomePodCast", f"虚拟音频配置未完成：{exc}")
        return 2
    finally:
        if backend:
            backend.close()
        root.destroy()
