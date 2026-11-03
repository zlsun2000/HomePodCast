# HomePod Cast — Guide · 使用须知

## Virtual cable preview · 虚拟声卡预览

Windows 音量可使用以下互斥方式：

1. **软件音量（预览）：**以管理员身份运行 `VBCABLE_ControlPanel.exe`，在 Options 取消勾选 **Enable Windows Volume Control**，确认显示 `Volume Control: Disabled`，再在 HomePodCast 设置中启用“软件控制虚拟输出音量”（默认关闭）。
2. **驱动音量：**以管理员身份运行控制面板并勾选 **Enable Windows Volume Control**，确认显示 `Volume Control: Enabled`；同时关闭应用的“软件控制虚拟输出音量”。此前仅以普通权限临时启用时，可在管理员模式关闭后再启用，以保存设置。

不要同时开启，否则可能重复衰减。实测本机驱动音量开启时 Windows 1–5 的采集信号为零，关闭后有非零信号；软件音量的低音量 HomePod 实际听感仍待验证。

Choose one method: **Software volume for virtual output** (off by default) requires disabling **Enable Windows Volume Control** in the VB-CABLE control panel run as administrator; alternatively enable the driver option and leave software volume off. Do not enable both: gain may be applied twice. On the tested PC, levels 1–5 yielded silent captured PCM with driver volume enabled but nonzero PCM with it disabled. The low-volume HomePod listening result using software volume remains unverified.

实验安装包附带标准 VB-CABLE，安装后可从开始菜单运行 **Configure HomePodCast Virtual Audio** 配置向导。已有可用驱动会直接复用；缺少驱动时，经确认打开原厂安装界面，重启后再次运行配置向导。安装包仍为预览版，构建和签名说明见 [installer/README.md](../installer/README.md)。

在设置的“音源模式”选择“虚拟输出（HomePod）”，刷新音源并明确选择标准 `CABLE Input`。开启自动切换后，程序在串流就绪时切换普通默认输出，停止时按记录恢复；通信输出保持原设置。也可关闭自动切换，在 Windows 中手动选择同一个 CABLE Input。不要启用录音端“侦听此设备”。全部掉线后停止与恢复为另一个默认关闭的选项；10 秒从程序确认全部掉线后计时。异常退出后可使用设置中的恢复按钮，恢复仍受原设备可用性与用户后续选择限制。应用的“音箱音量”控制 HomePod，Windows 音量控制当前默认输出；虚拟端点静音或音量为 0 时，应用将采集 PCM 置零。标准驱动的名称及两个 Windows 播放端点保持原样。

The experimental installer includes standard VB-CABLE. Run **Configure HomePodCast Virtual Audio** from the Start menu; it reuses a healthy driver or asks before opening the vendor installer. Reboot after driver installation and run the wizard again. Select **Virtual output (HomePod)** and standard **CABLE Input**. Optional automatic routing switches normal default outputs after streaming is ready and conditionally restores them on stop; communication defaults remain unchanged. With manual routing, choose the same endpoint in Windows. Keep recording-device monitoring disabled. Optional all-receivers-offline recovery waits 10 seconds after loss is detected. Use the recovery button after an abnormal exit. Restoration respects device availability and subsequent user choices. The app slider controls HomePod volume; Windows volume controls the default output. Muted or zero-volume virtual PCM is silenced in the app. Windows still shows the vendor's original endpoint names and both playback endpoints.

`HomePodCast Audio` 自有驱动仍是开发原型，虚拟机中已探测 PCM 路径，但原生静音、正式签名和完整运行验收尚未完成，不随应用安装。The own driver remains experimental: VM PCM probes have been performed, but native mute, production signing and full runtime acceptance remain incomplete. It is not bundled; existing device selections are preserved by exact ID. See [driver development notes](../drivers/README.md).

[← Back to README](../README.md) · [English](#english) · [中文](#中文) · [Privacy · 隐私](#privacy--隐私) · [Build from source](#build-from-source)

---

## English

![How to use HomePod Cast](usage-en.png)

- **First run** — current builds are not code-signed. SmartScreen may warn, and Smart App Control may block execution. Do not disable Windows protection to run the preview.
- **HomePod access** — Home app → Home Settings → Speakers & TV → *Anyone on the Same Network*, no password.
- **Firewall** — allow the app on private networks when Windows asks. A red dot means a HomePod cannot reach your PC.
- **Which speaker is which** — **♪** next to a channel plays a short test sound on that HomePod, before or while streaming.
- **Latency** — AirPlay needs a buffer. *Auto* keeps it as small as your Wi‑Fi allows, about 150 ms in total: fine for music and video, too slow for games.
- **Quad** — separate rear channels need a 5.1 or 7.1 Windows output device. With a stereo source the rear speakers repeat the front ones.
- **PC speakers** keep playing in **Computer output (both)** mode. Choose **Virtual output (HomePod)** and route playback to CABLE Input for HomePod-only playback. Apps explicitly bound to a physical speaker may still play there.
- **Dropouts** — a HomePod that loses the connection is reconnected on its own while the others keep playing. One that another device has started playing to is left alone until it is free. With *Dropout* switched off in Settings, the stream stops instead when a HomePod is lost.
- **Closing the window** hides it; the app keeps running, and streaming, as an icon in the notification area. Click the icon to get the window back, right-click it to quit. Starting the app a second time brings up the one that is running.
- **Settings** — source device, buffer (Auto or fixed), language (中文 / English) and *Startup*, which starts streaming with the last setup when you sign in to Windows, with only the icon showing; it is on unless you switch it off. The window follows the Windows light or dark mode.
- **Updates** — at launch, and when you click the version in Settings, the app asks GitHub for the latest release. A newer one shows next to the version as an orange arrow: click it and the app downloads that release from GitHub, puts it in its own place and restarts, picking the stream up again. Nothing else is sent.
- Tested with HomePod mini on Windows 11.

---

## 中文

![HomePod Cast 使用方法](usage-zh.png)

- **首次运行** — 当前构建没有代码签名，SmartScreen 可能提示，智能应用控制可能阻止运行。不要为预览版关闭 Windows 保护。
- **HomePod 权限** — “家庭”App → 家庭设置 → 扬声器与电视 → *同一网络上的任何人*，不设密码。
- **防火墙** — Windows 询问时允许本程序使用专用网络。圆点变红表示 HomePod 连不回电脑。
- **分清每台音箱** — 声道旁的 **♪** 会让那台 HomePod 响一声测试音，串流前、串流中都能用。
- **延迟** — AirPlay 必须有缓冲。*自动*档会按 Wi‑Fi 状况把它压到最小，总延迟约 150 ms：听音乐、看视频没问题，不适合游戏。
- **四声道** — 独立的后置声道需要把 Windows 输出设备配置成 5.1 或 7.1。音源是立体声时，后置会重复前置。
- **电脑音箱**在“电脑输出（同时播放）”模式下会同时出声。只让 HomePod 播放时选择“虚拟输出（HomePod）”，并将 Windows 输出切到 CABLE Input；明确绑定物理声卡的应用仍可能在电脑播放。
- **断线** — 掉线的 HomePod 会自动重连，其余音箱照常播放。被其他设备占用的音箱不会被抢回来，空闲后才重连。在设置里关掉*断线*后，有音箱掉线时改为直接停止串流。
- **关闭窗口**只是把它收起来：程序留在任务栏通知区域（托盘）继续运行、继续串流。点图标恢复窗口，右键点图标退出。再次启动程序会直接调出正在运行的那一个。
- **设置** — 音源设备、缓冲（自动或固定）、语言（中文 / English）和*自启*：登录 Windows 后按上次的配置自动开始串流，只显示托盘图标；默认开启，可以关掉。窗口跟随 Windows 的浅色或深色模式。
- **更新** — 启动时、以及点设置里的版本号时，向 GitHub 查询最新版本。有新版时，版本号旁边出现橙色箭头：点一下，程序会从 GitHub 下载新版、替换自己并重新启动，串流也会接着继续。不发送其他任何信息。
- 已在 Windows 11 上用 HomePod mini 测试。

---

## Privacy · 隐私

HomePod Cast collects nothing and has no account, analytics or telemetry. Your audio goes only to the speakers you pick, on your own network. The only connections it makes beyond that are to GitHub: a request to `api.github.com` at launch, or when you click the version, to look up the latest release, and the download of that release when you choose to update. Like any web request they show GitHub your IP address.

HomePod Cast 不收集任何数据，没有账号、统计或遥测。音频只发送到你在局域网里选中的音箱。除此之外，它只连接 GitHub：启动时或点版本号时向 `api.github.com` 查询最新版本，以及在你选择更新时下载新版。和任何网络请求一样，GitHub 会看到你的 IP 地址。

---

## Build from source

Windows 10/11, Python 3.12.

```powershell
pip install -r requirements.txt
python app.py     # run
.\build.ps1       # build dist\HomePodCast.exe
```

`engine.py` captures, routes and streams; `app.py` is the window and `tray.py` its icon in the notification area. `--autostart` starts streaming with the last setup, `--minimized` starts with only that icon showing.

Releases are built by [GitHub Actions](../.github/workflows/build.yml), not on a developer's machine: set `VERSION` in `app.py`, push, then push the tag `v` + that version. The workflow builds the exe, stamps the version into it and attaches it to a draft release.

## Credits

Built on [pyatv](https://github.com/postlund/pyatv), [SoundCard](https://github.com/bastibe/SoundCard) and [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter). Not affiliated with Apple; HomePod and AirPlay are trademarks of Apple Inc.

