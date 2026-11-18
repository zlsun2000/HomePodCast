# HomePod Cast — Guide · 使用须知

## Portable app · 便携版

双击 `HomePodCast.exe` 即可运行。下载的是 ZIP 时，请先解压。“电脑输出（同时播放）”使用现有的 Windows 播放设备。只想通过 HomePod 播放时，点击主界面的 **设置仅用 HomePod 播放**。

Double-click `HomePodCast.exe` to run it. If you downloaded a ZIP, extract it first. **Computer output (both)** uses an existing Windows playback device. For HomePod-only playback, select **Set up HomePod-only playback** in the main window.

## VB-CABLE setup · VB-CABLE 安装

### 安装步骤

1. 打开 **设置仅用 HomePod 播放**。如果指引已找到 **CABLE Input**，可以直接进入第 4 步。
2. 点击 **下载 Windows ZIP**，浏览器会打开标准版 VB-CABLE 的官方 ZIP。也可以从指引打开 [VB-Audio 官网](https://vb-audio.com/Cable/)。
3. 解压整个 ZIP。64 位 Windows 右键 `VBCABLE_Setup_x64.exe`，选择“以管理员身份运行”，点击 **Install Driver**，重启 Windows。再次打开 HomePodCast，回到指引并点击 **检测 CABLE Input**。
4. 点击 **使用 CABLE Input 并自动切换**。返回主界面，选择 HomePod 并开始串流。连接就绪后，HomePodCast 会切换 Windows 的默认输出，停止时恢复。

如果重启后仍检测不到，在指引中点 **打开 Windows 声音设置**，确认播放设备 **CABLE Input** 已启用，再检测一次。配置完成后，可从 **设置 → VB-CABLE 安装与使用** 再次打开指引。若要手动路由，关闭 HomePodCast 的自动切换，然后在 Windows 中选择 **CABLE Input** 作为输出。保持录音设备的“侦听此设备”关闭，以免声音送回电脑扬声器。

### Installation steps

1. Open **Set up HomePod-only playback**. If the guide finds **CABLE Input**, go to step 4.
2. Select **Download Windows ZIP** to open the official package for standard VB-CABLE in your browser. The guide also links to the [VB-Audio website](https://vb-audio.com/Cable/).
3. Extract the whole ZIP. On 64-bit Windows, right-click `VBCABLE_Setup_x64.exe`, choose **Run as administrator**, and select **Install Driver**. Restart Windows, return to the guide, and select **Detect CABLE Input**.
4. Select **Use CABLE Input and auto-switch**. Choose a HomePod in the main window and start streaming. HomePodCast switches the Windows default output when the stream is ready and restores it on stop.

If detection still fails after restarting, select **Open Windows Sound settings**, enable the **CABLE Input** playback device, and detect again. After setup, find the guide in **Settings → VB-CABLE setup and use**. To route manually, turn off automatic switching in HomePodCast and select **CABLE Input** as the Windows output. Keep **Listen to this device** off for the recording device to avoid sending audio back to your computer speakers.

### Windows volume · 系统音量

Windows 音量控制当前默认输出，应用的“音箱音量”控制 HomePod。虚拟输出静音或音量为 0 时，应用将采集信号置零。下列两种音量方式选一种。

1. **软件音量（预览）：**以管理员身份运行 `VBCABLE_ControlPanel.exe`，在 Options 取消勾选 **Enable Windows Volume Control**，确认显示 `Volume Control: Disabled`，再在 HomePodCast 设置中启用“软件控制虚拟输出音量”（默认关闭）。
2. **驱动音量：**以管理员身份运行控制面板并勾选 **Enable Windows Volume Control**，确认显示 `Volume Control: Enabled`；同时关闭应用的“软件控制虚拟输出音量”。此前仅以普通权限临时启用时，可在管理员模式关闭后再启用，以保存设置。

不要同时开启，否则可能重复衰减。实测本机驱动音量开启时 Windows 1–5 的采集信号为零，关闭后有非零信号；软件音量的低音量 HomePod 实际听感仍待验证。

Choose one method: **Software volume for virtual output** (off by default) requires disabling **Enable Windows Volume Control** in the VB-CABLE control panel run as administrator; alternatively enable the driver option and leave software volume off. Do not enable both: gain may be applied twice. On the tested PC, levels 1–5 yielded silent captured PCM with driver volume enabled but nonzero PCM with it disabled. The low-volume HomePod listening result using software volume remains unverified.

The Windows slider controls the current default output. The app slider controls the HomePod. The app silences captured virtual audio at zero volume or when muted.

### Output recovery · 输出恢复

“同时切换通信应用输出”可将通话输出也切到虚拟设备。“全部音箱掉线 10 秒后停止并恢复输出”从应用确认全部掉线后开始计时。异常退出后可在设置中恢复上次输出，恢复取决于原设备是否可用以及之后是否手动更改过输出。

You can opt in to switching the communications output and to restoring outputs 10 seconds after the app detects that all receivers are offline. After an abnormal exit, use the recovery button in Settings. Recovery respects subsequent manual switches and device availability.

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

