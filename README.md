<div align="center">

<img src="docs/icon.png" width="96" alt="HomePod Cast icon">

# HomePod Cast

**Windows audio → 1, 2 or 4 HomePods, in sync.**<br>
**把 Windows 声音同步送到 1、2 或 4 台 HomePod。**

![Windows 10/11](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D4)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

<a href="https://github.com/zlsun2000/HomePodCast/releases/latest/download/HomePodCast.exe"><img src="https://img.shields.io/badge/Download%20Windows%20EXE-2ea44f?style=for-the-badge&logo=windows&logoColor=white" alt="Download HomePodCast.exe for Windows" width="309"></a>
&nbsp;
<a href="https://www.buymeacoffee.com/geo2026"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="150"></a>
&nbsp;
<a href="https://afdian.com/a/geo2026"><img src="docs/afdian-button.png" alt="去爱发电赞助" width="150"></a>

**[发布页 · Releases](https://github.com/zlsun2000/HomePodCast/releases)** · **[使用指南 · Guide](docs/GUIDE.md)** · [原项目 · Upstream](https://github.com/GeoAtom/HomePodCast)

</div>

## 与原版的区别

本分支沿用双击 EXE 即可运行的流程，以及 1、2 或 4 台 HomePod 的同步串流。下表以 [GeoAtom/HomePodCast v1.2.1](https://github.com/GeoAtom/HomePodCast/releases/tag/v1.2.1) 为对照。

| 功能 | 原版 v1.2.1 | 本分支 |
| --- | --- | --- |
| 播放路径 | 从现有 Windows 播放设备采集。选物理扬声器时，电脑与 HomePod 同播。 | 保留电脑同播模式，新增虚拟输出。跟随 Windows 默认输出的应用可只通过 HomePod 播放。 |
| 虚拟声卡设置 | 从通用音源列表手动选择设备。 | 主界面提供 VB-CABLE 官方 ZIP 直链、解压安装步骤和 **CABLE Input** 检测。已有驱动可直接使用。 |
| 切换与恢复 | 在 Windows 声音设置中手动切换默认输出。 | 串流就绪后自动切换，停止时恢复。可选全部音箱掉线后的恢复。 |
| 音量 | 应用滑块调整 HomePod 音量。 | 虚拟模式支持 Windows 音量、静音和 0 档处理，并提供可选软件音量。应用滑块继续调整 HomePod 音量。 |

## 在 Windows 上使用

1. 下载 `HomePodCast.exe` 后双击运行。便携版适用于 Windows 10/11 x64。[下载 EXE](https://github.com/zlsun2000/HomePodCast/releases/latest/download/HomePodCast.exe)
2. 只想用 HomePod 播放时，在主界面点击 **设置仅用 HomePod 播放**。缺少驱动时，按指引下载并安装标准版 VB-CABLE，重启后回到应用检测 **CABLE Input**。
3. 点击 **使用 CABLE Input 并自动切换**，选择 HomePod，再点 **开始串流**。

便携 EXE 未进行代码签名，Windows 智能应用控制可能拦截。手动路由、软件音量和异常退出后的恢复步骤见[使用指南](docs/GUIDE.md)。

## What this fork adds

This fork builds on [GeoAtom/HomePodCast v1.2.1](https://github.com/GeoAtom/HomePodCast/releases/tag/v1.2.1) and keeps the portable EXE and synced streaming to one, two, or four HomePods.

- **HomePod-only playback.** The upstream app captures an existing Windows output. This fork adds a virtual-output mode for audio that follows the Windows default device, alongside the existing computer output mode.
- **Guided VB-CABLE setup.** The main window links directly to the standard Windows ZIP, shows installation and restart steps, and detects an available **CABLE Input**.
- **Automatic switching and recovery.** Windows can switch its default output when streaming is ready and restore the previous output on stop. Recovery when all HomePods disconnect is optional.
- **Windows volume and mute.** Virtual mode handles system volume, mute, and zero volume, with optional software volume. The app slider controls the HomePod speaker volume.

Download and double-click `HomePodCast.exe` on Windows 10 or 11 x64. Select **Set up HomePod-only playback** if you want to use VB-CABLE. The EXE is unsigned. [Download EXE](https://github.com/zlsun2000/HomePodCast/releases/latest/download/HomePodCast.exe) · [Setup guide](docs/GUIDE.md)

<details>
<summary><b>原版操作截图 · Upstream screenshots</b></summary>

![Upstream HomePod Cast usage in English](docs/usage-en.png)

![原版 HomePod Cast 中文使用方法](docs/usage-zh.png)

</details>
