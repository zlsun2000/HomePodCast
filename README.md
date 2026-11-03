<div align="center">

<img src="docs/icon.png" width="96" alt="HomePod Cast icon">

# HomePod Cast

**Windows audio → 1, 2 or 4 HomePods, in sync.**<br>
**把 Windows 声音同步送到 1、2 或 4 台 HomePod。**

[![Latest release](https://img.shields.io/github/v/release/GeoAtom/HomePodCast?label=release)](https://github.com/GeoAtom/HomePodCast/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/GeoAtom/HomePodCast/total)](https://github.com/GeoAtom/HomePodCast/releases)
![Windows 10/11](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D4)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

<a href="https://github.com/GeoAtom/HomePodCast/releases/latest/download/HomePodCast.exe"><img src="https://img.shields.io/badge/Download%20for%20Windows-2ea44f?style=for-the-badge&logo=windows&logoColor=white" alt="Download for Windows" width="309"></a>
&nbsp;
<a href="https://www.buymeacoffee.com/geo2026"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="150"></a>
&nbsp;
<a href="https://afdian.com/a/geo2026"><img src="docs/afdian-button.png" alt="去爱发电赞助" width="150"></a>

**[📖 Guide · 使用须知](docs/GUIDE.md)**

</div>

## 虚拟音频预览版

本分支增加虚拟输出、自动切换和恢复默认播放设备。实验性安装包包含标准 VB-CABLE，配置向导会在需要时请求确认，再打开原厂驱动安装程序；驱动安装后需要重启并再次运行向导。应用内选择“虚拟输出（HomePod）”和标准 **CABLE Input**，即可将默认输出送往 HomePod。明确绑定物理扬声器的应用仍可能从电脑出声。

**Windows 音量设置：**以下两种方式选一种使用。Windows 当前默认播放设备须为所选的 CABLE Input；应用中的“音箱音量”另行控制 HomePod 自身音量。

1. **软件音量（预览）：**以管理员身份运行安装目录 `VBCABLE` 文件夹中的 `VBCABLE_ControlPanel.exe`，在 **Options → Enable Windows Volume Control** 取消勾选，确认控制面板显示 `Volume Control: Disabled`；然后在 HomePodCast 设置中启用“软件控制虚拟输出音量”（默认关闭）。管理员权限用于保存驱动设置。
2. **驱动音量：**在上述管理员控制面板中勾选 **Enable Windows Volume Control**，确认显示 `Volume Control: Enabled`；在 HomePodCast 中关闭“软件控制虚拟输出音量”。如果先前仅在非管理员模式临时启用，需在管理员模式中关闭后重新启用以保存状态。

不要同时启用驱动音量和软件音量，否则可能重复衰减。本机测试发现驱动音量开启时，Windows 1–5 的采集信号为零；关闭后有非零信号。软件音量方案的低音量 HomePod 实际听感仍待验证。

标准 VB-CABLE 会创建 `CABLE Input` 和 `CABLE In 16ch` 两个播放端点；安装程序不会自动禁用或重命名它们。可在 Windows 声音设置中按需禁用 `CABLE In 16ch`；这只影响当前电脑，不会改变安装包或其他用户的设备。

该安装包及应用目前未正式签名，Smart App Control 可能阻止运行；驱动签名不会自动使外层应用受信任。详情见[使用指南](docs/GUIDE.md)、[安装包构建说明](installer/README.md)和[当前状态](docs/DEVELOPMENT_STATUS.zh-CN.md)。

## Virtual audio preview

This fork adds virtual-output routing and an experimental installer bundling standard VB-CABLE. Install the driver through the setup wizard, reboot, and run the wizard again. Select **Virtual output (HomePod)** and **CABLE Input** in the app. The preview builds are available as artifacts in [this fork's Build workflow](https://github.com/zlsun2000/HomePodCast/actions/workflows/build.yml); the download buttons above refer to the original upstream release and do not include these changes.

Choose one Windows-volume method: for the preview **Software volume for virtual output** setting (off by default), run `VBCABLE_ControlPanel.exe` from the installation's `VBCABLE` folder as administrator and disable **Options → Enable Windows Volume Control**, then enable software volume in the app. Alternatively, enable the driver option and leave software volume off. Using both can apply volume twice. On the tested PC, levels 1–5 produced silent captured PCM with driver volume enabled and nonzero PCM when disabled; low-volume listening through HomePod with software volume still needs verification. Windows volume controls the default output; the app's speaker slider controls the HomePod itself. The vendor driver exposes two playback endpoints; disabling `CABLE In 16ch` in Windows is an optional, per-PC setting, not an installer action. Current application and installer builds are unsigned and may be blocked by Smart App Control. See the [guide](docs/GUIDE.md) and [installer instructions](installer/README.md).

![How to use HomePod Cast](docs/usage-en.png)

<details>
<summary><b>中文使用方法</b></summary>

![HomePod Cast 使用方法](docs/usage-zh.png)

</details>
