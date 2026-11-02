# HomePodCast 单安装包方案

> 2026-11-02 收尾范围：用户决定保留当前 VB-CABLE 版本，暂缓单端点与品牌名称要求。此次不改名、不禁用 Windows 端点；下文保留实现过程和后续研究方向。当前状态以 [开发状态](DEVELOPMENT_STATUS.zh-CN.md) 为准。

## 单端点实现方向（2026-10-28）

- 标准 VB-CABLE Windows 10/11 驱动创建两个播放端点；官方支持用户更改端点名称，但手册指出驱动名称不能更改。尚未找到原版提供只创建一个播放端点的官方选项。[官方手册](https://vb-audio.com/Cable/VBCABLE_ReferenceManual.pdf)
- 评估路线：A. 向 VB-Audio 核实是否提供单端点、HomePodCast 品牌且微软签名的定制驱动，以及授权和成本；B. 评估已有开源虚拟音频驱动的签名、单端点、重分发、WASAPI loopback 和音量行为；C. 延续本项目单渲染端点驱动原型，解决原生静音和正式签名。A 尚未联系厂商，B 仅为候选探索，不假设第三方应用签名等同于微软认可的内核驱动签名。
- Scream 项目虽提供签名构建，但其 Windows 11 说明要求测试模式或更改启动保护，不符合当前保持安全设置的约束，暂不作为推荐方案。[项目说明](https://github.com/duncanthrax/scream)
- 自有原型 INF 定义一个渲染设备；已在隔离虚拟机实测采集，但正式签名和原生静音未解决。先在 VM 完成音量、静音、重连、重新安装与端到端验证，再评估 WHCP/HLK 及实际发布条件；不把测试签名当作生产方案。
- 验收包括：新装系统中只有一个相关的播放端点、期望名称、系统音量/静音、退出恢复、保持 Secure Boot 和 Smart App Control；不能通过禁用额外端点冒充单端点驱动。录音端点与播放端点分开检查。

更新：2026-10-28。已有实验性一体安装包和配置向导；新装系统测试、应用签名和正式发布验收尚未完成。

## 本次实现状态

### 2026-10-28 用户反馈

- 同日实体 Realtek 扬声器 loopback 实测：100%、50%、10%、0% 和静音的 RMS 分别约为 0.00990、0.00293、0.000176、0.000000083 和 0；测试后音量恢复 26%，未静音。该测试不包含 HomePod，也不证明所有实体声卡同样遵循端点音量。
- 用户报告物理/虚拟两种模式容易混淆。应用现把已识别的虚拟源从电脑输出列表中排除，保留已保存但不可用的占位，避免静默改源；标准 VB-CABLE 存在时不显示未选中的 16 声道端点。两种模式增加说明，HomePod 音量滑块明确标注为音箱音量；Windows 默认输出未必等于所选音源。
- 主机音频端点未重命名或禁用；用户不接受以禁用端点满足单端点目标。配置向导已兼容根据 VB-Audio 设备实例及扬声器类型识别重命名后的端点，尚需实际重命名实测。不能修改第三方驱动 INF/SYS/CAT，否则现有签名不能保留。

- 用户为了测试一体安装主动卸载 VB-CABLE。主机只读检查发现设备不存在，但 `VBAudioVACMME` 服务和官方驱动包仍存在；厂商原版安装界面显示 `Install Driver`。配置向导现允许在用户同意后打开厂商安装界面，但会再次检查设备没有出现；实际安装仍需用户在厂商窗口确认并在干净环境验证。未主动重装或清理用户的驱动。
- 用户报告虚拟机自有 `HomePodCast Audio` 经 HomePod 播放时，1–100 音量有效，但静音或 0 音量仍有声。应用侧 PCM 补偿现同时检查静音标志和端点音量为 0，不额外缩放非零音量；只通过单元测试，尚未对用户此次运行的版本、设置、发送链路和 HomePod 实际播放完成复测。驱动原生静音仍未修复。
- 应用保留 HomePod 接收端自身音量控件，并将其标注为“音箱音量”，与 Windows 端点音量区分。

- 新增 Inno Setup 构建脚本：固定官方 Pack45 的 SHA-256，验证安装器和微软目录签名，并用 Windows SDK SignTool 验证 INF 和 x64/ARM64 SYS 与目录的关联；第三方原包不入 Git。安装包本身和应用当前没有签名。
- 配置向导根据硬件 ID、设备提供者、状态和端点所属实例识别 VB-CABLE；已安装、状态异常或查询失败时不启动厂商安装器。确认后保存虚拟模式和自动输出设置；缺失时调用原版驱动安装向导，先尝试备份并保护播放和录音的默认设备。重启后设备状态及默认设备仍需在实际新装环境验证。
- 测试证据：源码运行时自检通过；本机只读 PnP/端点关联成功；31 项单元测试通过；应用和实验安装包编译成功。尚未在新装系统运行安装器、安装驱动或重启验证，也未完成本版 HomePod 端到端测试。
- 本机的 Smart App Control 在 2026-10-28 拦截了新构建的未签名 `HomePodCast.exe`；CodeIntegrity 事件 3077 记录策略 `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`。VB-CABLE 的微软签名不使应用和安装器自动受信任；当前安装包不能当作已可运行交付。
- 可选签名入口：先通过 `installer/sign_application.ps1` 使用受信任的代码签名证书和时间戳签署应用，然后向 `installer/build_installer.ps1` 传入 `-CodeSigningThumbprint` 和 `-TimestampUrl`，由 Inno Setup 签署安装器和卸载器。当前没有可用证书，此路径尚未在本机实测；打包的 DLL 等也需逐项检查及在 SAC 下验证，签名本身不构成运行保证。参见 [Microsoft 应用签名指引](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/code-signing-for-smart-app-control)。
- CI 构建的安装包标记为 experimental；流水线尚未在本次更改上运行，不纳入现有草稿发布。

### 可探索的应用签名路线

- 可使用符合 Microsoft Trusted Root Program 要求的应用代码签名证书；这与自有内核驱动的 Microsoft 驱动签名是两件事。证书申请可能涉及身份验证和费用，是否通过 SAC 仍需实际测试。
- [SignPath Foundation](https://signpath.org/) 为符合要求的开源项目提供免费签名，但其[开源项目条件](https://github.com/SignPath/fdn-website/blob/main/docs/terms.md)限制专有组件。当前安装包内含非开源 VB-CABLE，不能假设符合条件；可研究仅签署开源部分并在安装时从厂商获取驱动的方案，具体是否获准由该服务审核。
- Microsoft Artifact Signing 的公开信任证书对申请主体所在地有限制；当前官方文档说明个人开发者须位于美国或加拿大，不能仅凭可创建 Azure 资源而假设适用。[官方资格说明](https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart#prerequisites)

## 目标与选择

用户希望只下载、安装一次 HomePodCast，可以接受安装包内部包含第三方驱动。核心验收是 HomePod 播放时，本机扬声器不播放同一路音频。

选择：HomePodCast 安装包携带未经修改的标准版 VB-CABLE 官方包，安装后由 HomePodCast 管理采集和输出切换。自有测试签名驱动不再是这一目标的前置条件；保留已有原型用于后续研究。

音频路径：应用 → CABLE Input → WASAPI loopback → HomePodCast → HomePod。日常无需打开 VB-CABLE 控制面板或额外运行混音软件。首次驱动安装需要管理员确认，按官方要求安排重启，不强制立即重启。

## 已有证据

- 本机此前已完成 VB-CABLE 到 HomePod 的实际测试，用户确认 HomePod 有声且电脑没有同时出声。
- 本机启用 Enable Windows Volume Control 后，已测音量与静音；详见 `P0_AUDIO_VALIDATION.zh-CN.md`。这不代表新装机器已经自动完成此配置。
- 2026-10-28 只读枚举再次找到标准 CABLE Input、CABLE In 16ch 和 Realtek Speaker。此次没有播放声音或改变路由。
- 本地官方 Pack45 的 `VBCABLE_Setup_x64.exe` Authenticode 状态为 Valid；`vbaudio_cable64_win10.cat` 状态为 Valid，签发者为 Microsoft Windows Hardware Compatibility Publisher。此检查不替代驱动包内文件关联校验或其他 Windows 版本的加载测试。
- 现有 `app.py`、`audio_session.py`、`windows_audio.py` 已有虚拟模式、串流就绪后切换、停止后条件恢复等能力；一体安装器尚不存在。

## 分发依据与边界

[VB-Audio 官方许可页](https://vb-audio.com/Services/licensing.htm) 的 “VB-CABLE Distribution with other product” 允许在适用其 donationware 条件时随应用嵌入标准 VB-CABLE。用户必须能识别其厂商、看到来源和捐赠说明。专业机构场景另有许可要求；A+B、C+D 不适用此捆绑许可。

Pack45 自带 readme 要求集成须获作者同意；当前官网给出了上述有条件许可。打包时保留原 readme、完整原包、来源链接和所依据条款的核对日期，发布前复核具体分发场景是否落在许可范围内。不得将 VB-CABLE 重新标为项目 MIT 代码。需要特殊品牌或不满足公开条件的分发，应另行取得授权。

## 实现顺序

1. **固定依赖和构建安装包**：固定官方包版本、下载来源和 SHA256；校验安装器、CAT 和包内关联文件；原样内嵌，不修改 INF/SYS/CAT。交付一个 `HomePodCast-Setup.exe`，同时保留便携应用构建。
2. **识别与复用**：按设备身份、驱动提供者、状态及播放端点确认 VB-CABLE，名称仅用于展示。已有可用版本直接复用，不能无条件运行安装器，因为官方安装器检测到已安装时可能进入卸载流程。禁用、部分安装或不兼容状态需给出具体处理信息。
3. **缺失时集成安装**：显示组件来源和许可；仅驱动步骤请求管理员权限，应用仍以普通用户运行。使用已核实的官方安装方式；未验证静默参数前，允许在同一安装流程中调用原版安装向导，不承诺完全无提示。检查安装结果和重启状态，重启后再确认设备就绪。
4. **保护原有设备设置**：安装前记录播放和录音的默认设备。驱动安装可能改变默认播放或录音设备，须识别并处理这类变化，不能把用户麦克风留在 CABLE Output。已经安装的驱动及其设置保持原状。
5. **减少首次配置**：确认标准 CABLE Input 的身份后在 HomePodCast 推荐选择；明确提供“只通过 HomePod 播放”的入口。检查 Windows 音量配置和设备监听；只有验证了受支持的配置接口，才自动设置驱动选项，否则在应用内给出一次性引导，不猜测注册表。
6. **复用路由与恢复**：HomePod 连接和采集就绪后切换普通输出；通信输出单独选择。停止或按用户选项断连后恢复仍由当前会话控制的设备，尊重用户中途手动切换。异常退出保留恢复入口。
7. **升级与卸载**：升级应用不重复安装驱动；卸载 HomePodCast 默认保留共享的 VB-CABLE，避免影响其他应用。只有用户明确选择且检查后才卸载驱动。

## 验收与发布

- CI：依赖哈希和签名校验、路由单元测试、应用及安装包构建、自检产物；不能将 CI 编译成功等同于驱动运行或 HomePod 发声成功。
- 新装 Windows：测试首次安装、管理员拒绝、需要重启、安装失败、默认麦克风保留、重复安装和卸载。安装器自身的签名与 Smart App Control 兼容性单独验证；驱动的微软签名不会自动赋予外层安装器信任。
- 已装 VB-CABLE 的本机：验证直接复用、音量和静音、开始/停止的切换恢复，以及用户实际确认 HomePod 有声且扬声器无同路声音。保留 Secure Boot 和 Smart App Control。
- 路由边界：明确绑定物理扬声器的应用或开启监听转发的软件，仍可能发声。需检查这类应用的输出设置，不能声称切换默认设备能强制迁移所有音频。
- 两小时稳定性测试仍按用户此前要求暂缓；本方案不将其记为通过。

## 官方参考

- [VB-CABLE 下载与安装说明](https://vb-audio.com/Cable/)
- [VB-CABLE 手册](https://vb-audio.com/Cable/VBCABLE_ReferenceManual.pdf)：安装及重启、默认设备变化、loopback、Windows 音量选项。
- [VB-Audio 分发许可](https://vb-audio.com/Services/licensing.htm)
- [Microsoft 驱动签名选项](https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/driver-signing-offerings)：自有驱动将来另行处理签名；不继续用测试签名作为日常使用前提。
