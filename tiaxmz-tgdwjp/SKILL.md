---
name: tiaxmz-tgdwjp
description: TIA Portal（博图）PLC 项目开发全流程——通过 tia-portal MCP 连接建项目、询问并添加 PLC 设备与型号、生成中文命名 IO 变量表、提纯控制要求交用户确认、按标准程序框架封装按钮/动作/流程/模式、以 S7DCL 梯形图编写并导入编译交付。Use when 用户说"写 TIA 程序"、"做 PLC 项目"、"博图编程"、"帮我写/改 PLC 控制程序"、"用 TIA 做 XX 站"、"PLC 梯形图"，或发来 IO 表、控制要求、工艺描述要求编写西门子 S7 程序时。Not for 非西门子/非 TIA 的 PLC，或只讲概念不写程序的提问。
---

# TIA PLC 项目开发（tiaxmz-tgdwjp）

按固定六步交付西门子 S7 梯形图程序。**开工即把六步建成任务清单（右侧任务栏逐项打勾），并先请使用者把材料一次交全；控制要求经使用者确认后才动代码。**

## 重要规则（先读）

1. **六步 = 六个任务**：开工时用 task 工具创建 6 个任务（用结果导向措辞、使用者的语言），执行到哪步就 `start` 哪个、做完立刻 `done`，让右侧任务栏实时显示进度；计划变化时用 `rename/abandon` 保持清单与实际一致。
2. **材料一次交全**：先输出下面的「开工材料清单」请使用者一次性提交；交不全的项才逐个补问，避免挤牙膏式来回。
3. **控制要求提纯 → 用户确认**是必经关卡（步骤 3），确认"行"之前不得编写程序。
4. 所有变量、块名、网络标题一律**中文命名/中文注释**。
5. 编译必须 **0 错误**，并用 DescribeBlockLogic 逐段核对逻辑后才算交付。
6. MCP 占用项目期间 TIA 界面打不开该项目；交付前必须释放（步骤 6）。
7. 梯形图细节语法与框架模板在 `references/lad-s7dcl-syntax.md`、`references/framework-template.md`，写代码前先读对应文件。
8. **配置向导对接**：用户可通过 `wizard/index.html`（CubeMX 式前端）配置并生成 `project.json`；收到该文件时按 `references/wizard-config.md` 解析——plc→任务1、io→任务2、modes/steps/信号约定→任务3 提纯素材、language→任务5，仍走六步任务跟踪与提纯确认关卡。

## 开工材料清单（请使用者一次交全）

> 也可用配置向导 `wizard/index.html` 生成 `project.json` 代替手交材料（格式见 `references/wizard-config.md`）；收到配置包按文件解析，缺项再补问。

| # | 材料 | 内容要求 | 缺了怎么办 |
|---|------|----------|------------|
| 1 | 设备信息 | 可**多台 PLC**；每台给系列/型号/订货号/固件（例：CPU 1215C DC/DC/DC，6ES7215-1AG40-0XB0，V4.5）及 PN/IE 接口名与 IPv4/掩码；另注明目标 TIA 版本（V18/V20/V21） | 我来问，不猜 |
| 2 | IO 表 | 每点的地址、符号、说明、0/1 状态语义 | 必备，缺则先要 |
| 3 | 控制要求/工艺描述 | 模式档位与触发方式、动作先后顺序、每步完成判据 | 必备，缺则先要 |
| 4 | 信号约定 | 按钮/传感器常开还是常闭、1=正常还是 0=动作、停止/急停行为（暂停续跑或中止） | 提纯环节确认 |
| 5 | 时间参数 | 哪些动作后要延时、TON/TOF、时长 | 默认不加 |
| 6 | 其他（可选） | 站间握手信号、HMI/WinCC 需求、产量/循环次数、手动点动需求 | 可无 |

一次性交全的好处：材料齐了六步可以连贯跑完，任务栏一气呵成。

## 六步工作流（任务清单）

每步三行：**【需要】**（输入材料）→ **【做什么】**（动作）→ **【交出】**（产出与完成判据）。

### 任务 1：环境接入
- 【需要】材料 1 设备信息（多台 PLC 与各自 PN/IE、IPv4，目标 TIA 版本）；项目名/存放目录（可默认：工作目录+中文项目名）
- 【做什么】`Bootstrap` → `Connect` → `CreateProject` → 对**每台** PLC 按用户给的型号 `AddDeviceWithFallback(family, preferredMlfb, preferredVersion, deviceName)` → 按各台 `iface/ip/subnet` 配 PN/IE 网络（`ConnectDeviceNodesToProfinetSubnet` 等；IP 可在设备属性设置，多台注意同子网）→ `GetDevices` 验证。设备型号**必须用用户给的**，没有就问，不假设。
- 【交出】建好的工程与 PLC 设备。占用约定：MCP 打开项目时 TIA 界面打开同项目报 0100:000295；要让用户查看前先 `SaveProject` → `CloseProject` → `Disconnect`；继续开发用 `AttachToOpenProject`/`OpenProject`。`GetProjectTree` 缺 DLL 时报错属已知，用 `GetDevices/GetBlocks` 替代。

### 任务 2：IO 变量表
- 【需要】材料 2 IO 表（+材料 4 信号约定）
- 【做什么】`PlcBuildAndImport kind=tagtable` 生成中文命名变量表：变量名中文无空格（`启动按钮`、`升降落下到位`），注释格式 `符号 说明：状态语义`（`S3 停止按钮（常闭）：1=正常 0=按下`），地址与 IO 表逐点对应。
- 【交出】变量表导入且与 IO 表逐点核对无误。重建表用 `DeletePlcTagTable`（先 dryRun 预览）。

### 任务 3：控制要求提纯 → 使用者确认（关卡）
- 【需要】材料 3/4/5/6
- 【做什么】把控制要求提炼成结构化清单交使用者确认：①模式划分（档位+触发操作）②各模式动作序列（动作+完成判据）③信号约定（常开常闭/有效电平/停止急停行为）④延时参数 ⑤缺项问题（站间信号、循环方式等）。用 question 工具或清单形式**请使用者判断行不行**。
- 【交出】经使用者确认的控制逻辑。**未确认不得进入任务 4。**

### 任务 4：程序框架搭建
- 【需要】已确认的控制逻辑
- 【做什么】按 `references/framework-template.md` 搭骨架：OB1 调用链 `按钮()→动作()→流程()→模式()`；全局 DB（动作请求位/模式标志/流程步）+ 沿 DB（P_TRIG 记忆）；动作层请求/应答；流程步 ×5 编号模板；模式互锁+启动许可；初始化顺序链。
- 【交出】DB 与 FC 空框架导入成功（块名中文）。**流程材料为空时兜底**：只生成一个空 Main（OB1 空网络），IO 变量表照常，不建框架块。

### 任务 5：梯形图编写
- 【需要】任务 4 框架 + 确认后的动作序列
- 【做什么】按 `references/lad-s7dcl-syntax.md` 写 `.s7dcl`+.s7res（UTF-8 BOM，`S7_PreferredLanguage := "LAD"`，中文标题走 MLC）：每步网络〔启动许可·EQ(流程步)〕扇出动作，〔到位·TON 延时〕MOVE 下一步；安全网络放块尾。
- 【交出】全部块导入成功。

### 任务 6：交付闭环
- 【需要】全部块
- 【做什么】`CompileAndDiagnosePlc`（**0 错**）→ `DescribeBlockLogic` 逐段读回逻辑与提纯清单逐条核对 → `SaveProject` → `CloseProject`+`Disconnect` 释放。
- 【交出】编译 0 错、逐段核对通过、已保存并释放的工程；给使用者指路（打开 `xxx.ap21` 查看哪些块）。任务 6 `done` 后六项全绿。

## 示例

使用者发来"主件供料站 IO 表 + 工艺描述"说"帮我写 TIA 程序"：

1. 建 6 个任务（右侧任务栏出现六步清单），输出材料清单："设备用什么型号？IO 表和控制要求请一并给我；信号常开常闭、停止急停行为、延时点也请说明，一次交齐即可连贯开工。"
2. 材料到手后：任务 1 start——建项目、加 1215C V4.5；done。任务 2 start——建 `主件供料站IO` 中文变量表；done。
3. 任务 3 start——提纯回呈："三档位——复位=1+启动→初始化；手/自动=0+启动→单次流程；手/自动=1+启动→连续循环；停止=当前步暂停再启动续跑；急停常闭 1=正常 0=动作、动作锁定需复位；下降/抓取/抬升各加 0.5s TON。对吗？"得到确认后 done。
4. 任务 4/5 start——搭框架、写梯形图导入。任务 6 start——编译 0 错、逐段核对、保存、释放；六项全部打勾，提示使用者打开项目查看。

## 避坑清单（排障速查）

| 现象 | 原因 | 处理 |
|---|---|---|
| 导入报 `Failed importing` / `importedBlocks:0` | 块头写了 `S7_PreferredLanguage := "SCL"` | 改回 `"LAD"`，SCL 网络混编 |
| Override 导入报 Multilingual text 错误 | .s7res 带 en-US 文化项 | 只保留 zh-CN |
| 中文注释乱码 | 文件缺 BOM | 全部 s7dcl/s7res 转 UTF-8 WITH BOM |
| 网络标题导入后丢失 | 标题写了字面中文 | 用 `MLC_*` 引用 + .s7res 映射 |
| FC 编译报静态变量问题 | FC 带了 VAR/Static | 状态移入全局 DB，FC 只留 VAR_TEMP |
| 同一输出多处赋值报警 | 多个普通 Coil 写同一变量 | 普通 Coil 只留一处，其余 S/R 线圈 |
| 输出"多写后者覆盖"不符合预期 | 网络顺序 | 安全/急停/暂停网络放块尾 |
| TON 复用串台 | 多步共用一个实例 | 每个延时点独立 TON_TIME 成员 |
| 重新生成块后旧逻辑还在 | GenerateBlocksFromExternalSource 不覆盖 | 删块再导，或直接 ImportFromDocuments(Override) |
| TIA 界面打不开项目（0100:000295） | 项目被 MCP 占用 | Save+Close+Disconnect 释放 |
| GetProjectTree 报 WinCCUnified DLL 错 | 本机 TIA 组件不全 | 改用 GetDevices/GetBlocks/GetSoftwareTree |
| 到料/到位信号一闪而过导致定时器重跑 | 传感器短暂触发后复归 | 加记忆位锁存再定时，完成位锁存到本循环结束 |
| 设设备 IP 没有工具入口 | 网络节点 IP（`Address`）不在 DeviceItem 属性上 | TIA 界面手动：设备与网络 → 接口 → 以太网地址；交付时附"待手动设 IP 清单" |
| GetDeviceItem 子路径 not found | 子项路径要带设备同名层级（`设备/设备/子项`） | 用 `ExportDeviceAml` 导出 AML 读真实层级再写路径 |
