# 内置 HomePodCast Audio 驱动：源码核对与原型方案

> 历史研究记录。实际原型现使用单渲染端点和 WASAPI 软件 loopback，未实现下文初期设想的私有数据桥。当前交付采用 VB-CABLE，原型说明以 [drivers/README.md](../drivers/README.md) 为准。

日期：2026-10-22。此文记录第二阶段研究，不代表驱动已经实现、编译或通过签名。

## 源码证据

已通过 GitHub 连接器读取 Microsoft Windows-driver-samples 的以下资源：

| 资源 | 内容 SHA | 核对结果 |
| --- | --- | --- |
| [EndpointsCommon/minwavertstream.cpp](https://github.com/microsoft/Windows-driver-samples/blob/main/audio/sysvad/EndpointsCommon/minwavertstream.cpp) | `adea0c824c0830fd213fd2f7061160e7f111c556` | `WriteBytes` 使用 `m_ToneGenerator.GenerateSine` 填充 capture DMA；`ReadBytes` 把 render DMA 交给 `m_SaveData.WriteData` |
| [EndpointsCommon/minwavert.cpp](https://github.com/microsoft/Windows-driver-samples/blob/main/audio/sysvad/EndpointsCommon/minwavert.cpp) | `c6b8e8c3cad83eb22d034f0f341318639f3f9445` | 单独维护 system、offload 和 loopback 流，不能把“存在 loopback pin”当成真实回传 PCM 已实现 |
| [仓库 LICENSE](https://github.com/microsoft/Windows-driver-samples/blob/main/LICENSE) | `6ef3ee38d1ce61958787dda3b8c669627b248080` | 当前上游使用 MS-PL；不能把继承代码全部重标成 HomePodCast 的 MIT 许可 |

SHA 是读取文件的 blob SHA，不是整个驱动工程的构建基线。正式原型还须固定上游 commit、依赖子模块和 WDK 版本。上游可能更新，应在引入代码时重新核对许可及文件声明。

## 首个原型的边界

推荐只暴露一个立体声播放端点，初期不暴露 offload、空间音频或多声道功能。应用共享模式的多客户端混音由 Windows Audio Engine 完成；驱动不直接承接任意格式、任意多引脚的混音任务。

render PCM 必须进入驱动内真实的数据桥，再由对应的标准 loopback/capture 路径读取，替换样例的测试音路径。优先保留当前用户态 WASAPI/SoundCard 接口，减少应用与驱动之间的新私有协议。

具体待实现接口：

- 在适配器或端点范围维护有界、不可分页的 PCM 缓冲，并绑定格式与流代号。
- 从正常 render 数据消费路径写入 PCM，从 loopback capture 路径读取；先实现单一共享 render 流，不把样例的多个 offload/system 流直接拼接。
- 缓冲不足输出零、溢出丢弃最旧的完整帧，保持音频线程有界执行；以计数器记录异常。
- 针对 RUN/PAUSE/STOP、格式重开、设备移除与电源状态，清空旧数据和重置流代号，避免旧会话音频泄漏到新会话。
- 对多个 capture 消费者选择独立读游标；不能让一个读取者从全局队列移走其他读取者需要的数据。
- 保持 WaveRT 位置、通知和真实数据进度一致；不能只接一个 FIFO 而忽略系统要求的时钟行为。
- 明确定义端点音量与静音作用位置，确保用户态只衰减一次；普通应用不运行时端点仍可消费/丢弃音频。

以上是设计候选，必须经过 WDK 原型和 Driver Verifier/音频测试验证，不能据此声称内核实现已正确。

## 建议的原型里程碑

1. 在可编译的 VS/SDK/WDK 环境固定上游版本并构建未改样例，保留构建日志。
2. 在独立测试系统验证样例安装和卸载；测试签名仅用于开发环境，产品交付另走正式签名路线。
3. 裁剪为单立体声输出，先固定一种 PCM 格式完成真实 render→loopback 数据桥。
4. 用不同左右声道测试音证明传输的是输入 PCM，而非生成的测试音；检查静音、音量、无读取者和无播放者。
5. 加入 44.1/48 kHz 格式协商、长时间时钟漂移、多个共享播放客户端及 capture 客户端。
6. 完成 PnP、电源、睡眠、异常停止、安装升级回滚与安全测试，再讨论签名发布。

AirPlay、网络和 HomePod 发现继续位于现有用户态引擎；驱动不承担网络连接。

## 本机环境缺口

`tools/check_driver_toolchain.ps1` 检查注册和标准安装位置、PATH，报告见 `P4_DRIVER_TOOLCHAIN.json`。当前没有在这些位置发现 Visual Studio、Windows Kits 根目录、WDK `portcls.h` 或可用的驱动编译/验证命令。

这使本机无法对驱动代码完成编译验证。自定义、未注册的安装位置仍可能需要另行指定；报告不声称已经扫描全盘。下一步需提供可用 VS/SDK/WDK 工具链及独立驱动测试系统，才能继续原型实现。还没有建立正式签名条件或完成 Windows 10、多 HomePod、Secure Boot/内存完整性的测试矩阵。

当前 VB-CABLE 用户态版本不依赖这套工具链，可以继续使用和验收。用户已明确暂缓两小时稳定性测试，该测试仍未通过。

## 2026-10-27：可编译原型与数据路径修订

已实现并推送隔离构建的 HomePodCast 自有端点原型，见 `drivers/README.md`、`drivers/prototype/`。实际源码以当前工作树及 `drivers/upstream.lock.json` 为准。

[微软 WASAPI 文档](https://learn.microsoft.com/en-us/windows/win32/coreaudio/loopback-recording)说明：当 render endpoint 未声明硬件 loopback pin 时，WASAPI 从 Windows Audio Engine 的输出复制真实混音 PCM。因此此前“必须先在驱动内实现独立 PCM 缓冲桥”的设计约束过强；它是保留硬件 loopback pin 时的候选方案，不是实现本项目目标的唯一方式。

当前原型选择：单一立体声 null render endpoint，无硬件 loopback、offload、麦克风或音频引擎节点，由 Windows Audio Engine 负责共享播放客户端的混音和软件 loopback；延续应用现有 SoundCard/WASAPI 采集接口。驱动不向物理音箱转发数据、不启用样例音频落盘。声明 44.1/48 kHz 16-bit PCM，INF 初始面向 Windows 11 x64 build 22621 及以后。

[原型 CI](https://github.com/zlsun2000/HomePodCast/actions/runs/40353782218)已实际通过，生成独立 HomePodCastAudio.sys/INF，并通过 API validator；下载产物后 InfVerif /w /v 报告 INF is VALID。应用新增功能[构建](https://github.com/zlsun2000/HomePodCast/actions/runs/40354121817)亦通过，包含 23 项回归测试、EXE 打包及运行自检。原型探针新增 5 项隔离/分析测试；这些测试不等同于内核运行验证。

尚未在 Windows 测试 VM 安装自有端点，真实输入 PCM、音量/静音、PnP/睡眠、混音、独占模式限制及 HomePod 串流验收仍待执行。测试 VM 关闭且光驱为空，未发现已下载 Windows ISO。用户此前明确暂缓两小时长测，该项不自动视为通过。正式内核签名、Secure Boot/内存完整性、安装升级卸载与发布矩阵仍未完成。
