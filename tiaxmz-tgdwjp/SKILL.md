---
name: tiaxmz-tgdwjp
description: TIA Portal（博图）PLC 项目开发全流程——通过 tia-portal MCP 连接建项目、询问并添加 PLC 设备与型号、生成中文命名 IO 变量表、提纯控制要求交用户确认、按标准程序框架封装按钮/动作/流程/模式、以 S7DCL 梯形图编写并导入编译交付。Use when 用户说"写 TIA 程序"、"做 PLC 项目"、"博图编程"、"帮我写/改 PLC 控制程序"、"用 TIA 做 XX 站"、"PLC 梯形图"，或发来 IO 表、控制要求、工艺描述要求编写西门子 S7 程序时。Not for 非西门子/非 TIA 的 PLC，或只讲概念不写程序的提问。
---

# TIA PLC 项目开发（tiaxmz-tgdwjp）

按固定六步交付西门子 S7 梯形图程序。**第 3 步的"控制要求提纯→用户确认"是必经关卡，未确认不得进入编程。**

## 重要规则（先读）

1. 所有程序变量、块名、网络标题一律**中文命名/中文注释**。
2. 动手写代码前，必须先把控制要求**提纯**成结构化清单**返回给使用者确认**（见步骤 3），使用者判断"行"才继续。
3. 编译必须 **0 错误**，并用 DescribeBlockLogic 逐段核对逻辑后才算交付。
4. MCP 占用项目期间 TIA 界面打不开该项目；查看前必须释放（步骤 6）。
5. 梯形图细节语法与程序框架模板分别在 `references/lad-s7dcl-syntax.md`、`references/framework-template.md`，写代码前先读对应文件。

## 六步工作流

### 1. 环境接入（tia-portal MCP）

顺序固定：`Bootstrap` → `Connect` → `CreateProject` → 添加设备 → `GetDevices` 验证。

- 建项目：`CreateProject(directoryPath, projectName)`，目录默认用当前工作目录，项目名用中文或按用户要求。
- **询问需要添加什么设备、型号**：不要假设 CPU！用 question 工具问清：PLC 系列（S7-1200/1500）、具体型号（如 CPU 1215C DC/DC/DC）、订货号/MLFB（如 6ES7215-1AG40-0XB0）、固件版本（如 V4.5）。拿到后 `AddDeviceWithFallback(family, preferredMlfb, preferredVersion, deviceName)` 一次命中为准，命中不了再让用户确认替代型号。
- 验证：`GetDevices` 看设备、`GetBlocks` 看程序块。`GetProjectTree` 可能因缺 WinCCUnified DLL 报错，用前两者替代。
- 项目占用约定：MCP 打开项目时 TIA UI 打开同项目会报 0100:000295（"已打开为参考项目"）。让用户在界面查看前，先 `SaveProject` → `CloseProject` → `Disconnect` 释放；继续开发时 `Connect` → `OpenProject`。用户界面里已开着项目时用 `AttachToOpenProject` 接管。

### 2. IO 表（中文命名变量表）

从用户的 IO 表生成变量表（`PlcBuildAndImport kind=tagtable`，JSON：`{name, comment, tags:[{name, dataType, address, comment}]}`）：

- 变量名用中文（不用空格，如 `启动按钮`、`升降落下到位`），地址与用户 IO 表逐点对应。
- 注释规范：`符号 说明：状态语义`（例：`S3 停止按钮（常闭）：1=正常 0=按下`）。信号的常开/常闭与有效电平以提纯确认的结论为准写进注释。
- 需要重建表时：`DeletePlcTagTable(dryRun=true 预览 → false)`，同名表里旧符号会一并消失，确认无 HMI 绑定再删。

### 3. 控制要求提纯 → 用户确认（必经关卡）

把用户的工艺描述/控制要求**提纯**为结构化清单，返回给使用者判断行不行：

1. **模式划分**：有哪些档位/模式（如 复位、手动单次、自动循环），各自的触发操作（什么信号+什么按钮）。
2. **动作序列**：每个模式下按顺序列出执行步骤（执行器动作 + 完成判据传感器）。
3. **信号约定**：每个按钮/传感器是常开还是常闭、1=正常还是 0=动作；停止/急停按下后的处理（暂停续跑 / 中止重来）。
4. **时间参数**：哪里要延时（延时量、TON/TOF）。
5. **边界问题**：缺失的信号（如站间握手）、循环次数、异常处理——列成问题一并让用户答。

输出格式：一张模式×序列表 + 待确认问题清单。**用户确认"行"之后才进入第 4 步。**

### 4. 程序框架（标准模板封装）

模板细节见 `references/framework-template.md`。骨架固定为：

- **OB1 调用链**：`按钮() → 动作() → 流程() → 模式()`（一条梯形图支路串联调用）。
- **全局 DB**（嵌套 STRUCT）：`动作.请求位…`、`模式.初始化/手动/自动{开始,标志位}` + `模式.停止标志位/启动标志位/流程步:Int`。
- **沿 DB**：编号 Bool 位，专供 P_TRIG 边沿记忆。
- **动作层（请求/应答）**：流程/模式只置 `全局.动作.Xxx` 请求位；`动作` FC 把请求翻译成线圈（两线圈执行器要互锁），到位传感器清除请求——流程与输出解耦。
- **流程步模板**：步号 ×5 递增（1,5,10,…）。每步一个网络：〔`模式.启动标志位` · `EQ(流程步=当前步)`〕扇出本步动作请求/线圈；另一分支〔到位传感器（· TON 延时）〕`MOVE` 下一步。
- **模式互锁**：任一模式"开始"→ 置本模式标志、复位其他模式标志与停止标志、P_TRIG 一次性 `MOVE(流程步:=起点)`（暂停后恢复不允许重置步号）。**启动许可** =（运行模式标志）· 非停止 · 非复位 · 急停正常。
- **初始化顺序链**：初始化模式下按"前一步到位才发下一步命令"串行（升降抬起 → 夹爪松开 → 搬运回位…），全部到位置"初始化完成"。

### 5. 梯形图编写（S7DCL 导入语法）

语法全套（import 验证形式）见 `references/lad-s7dcl-syntax.md`。要点：

- 每块两个文件：`<块名>.s7dcl` + `<块名>.s7res`，**UTF-8 WITH BOM**。
- 块头必须 `S7_PreferredLanguage := "LAD"`（纯 SCL 块头导入会失败；SCL 写法放 `{ S7_Language := "SCL" }` 网络里混编）。
- 中文块标题/网络标题走 `.s7res` 的 `MLC_*` 映射（`S7_BlockTitle/S7_NetworkTitle := "MLC_x"`），**只写 zh-CN**（加 en-US 且 Override 会报错）。
- FC 不允许 Static 段——所有状态（步号、标志、定时器实例）放进全局 DB。TON 实例直接声明为全局 DB 成员（`延时X : TON_TIME`），调用 `"全局".延时X.TON{ time_type := Time }( PT := T#500MS, ET => )`。
- 多线圈扇出用 `wire#wN` 并联 + `RUNG wire#wN` 起始支路；普通 Coil 全块只写一处，其余用 S/R 线圈（S/R 允许多处写，扫描顺序后者优先——安全/急停网络放块尾）。

### 6. 交付闭环

1. `ImportFromDocuments(importOption="Override")` 逐块导入（DB 无 .s7res 也能导）。
2. `CompileAndDiagnosePlc` → **错误数必须为 0**；有错按报错逐条修，重新导入同名块覆盖。
3. `DescribeBlockLogic` 逐段读回逻辑，与提纯清单逐条核对（并联是否成形、边沿是否只用一次、取反是否正确）。
4. `SaveProject` 保存。
5. `CloseProject` + `Disconnect` **释放项目**，告诉用户在 TIA 界面打开查看（以普通项目方式打开）。

## 示例

用户发来"主件供料站 IO 表 + 工艺描述"说"帮我写 TIA 程序"：

1. 连接并建项目，问："PLC 用什么系列/型号/订货号/固件？"（如 1215C DC/DC/DC V4.5）
2. 按 IO 表生成 `主件供料站IO` 中文变量表。
3. 提纯并确认："三档位——复位=1+启动→初始化（升降抬起→夹爪松开→搬运回右侧位）；手/自动=0+启动→单次搬运循环；手/自动=1+启动→连续循环；停止=当前步暂停、再启动继续；急停常闭 1=正常 0=动作、动作后锁定需复位；下降/抓取/抬升处加 0.5s TON。对吗？"
4. 确认后按框架模板建 全局/沿 DB + 按钮/动作/流程/模式 FC。
5. 写 S7DCL 梯形图并导入、编译 0 错、逐段核对、保存、释放。

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
