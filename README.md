# tiaxmz-tgdwjp — TIA PLC 项目开发 Skill

通用 Agent Skill（SKILL.md 规范），在 MiMo Desktop / MiMoCode 开箱即用，也适用于 Claude Code 等支持同类 skill 规范的 Agent。按固定六步交付西门子 TIA Portal（博图）S7 梯形图程序，从建项目到编译交付全流程。

## 功能（六步工作流）

1. **环境接入** — 通过 `tia-portal` MCP 连接/创建项目，必询 PLC 设备系列、型号、订货号与固件版本后再添加设备。
2. **IO 表** — 按用户 IO 表生成中文命名变量表与注释规范（`符号 说明：状态语义`）。
3. **控制要求提纯 → 用户确认**（必经关卡）— 把工艺描述提炼为模式划分、动作序列、信号约定、延时参数与缺项清单，返回用户确认后才编程。
4. **程序框架** — 标准化封装：`按钮→动作→流程→模式` 调用链、全局/沿 DB、请求/应答动作层、流程步模板（×5 步号 + EQ/Move）、模式互锁与启动许可。
5. **梯形图编写** — S7DCL（`.s7dcl` + `.s7res`，UTF-8 BOM）导入语法全套：TON 延时、`wire#wN` 并联扇出、中文网络标题、LAD+SCL 混编。
6. **交付闭环** — 导入 → 编译 0 错 → `DescribeBlockLogic` 逐段逻辑校验 → 保存 → 释放项目供 TIA 界面查看。

附避坑清单：FC 无 Static、SCL 块头导入失败、BOM/中文标题、扫描顺序与多写规则、项目占用冲突等。

## 安装

把仓库中的 `tiaxmz-tgdwjp/` 目录复制到 skill 根目录：

```text
MiMo Desktop / MiMoCode:
  全局：  ~/.config/mimocode/skills/tiaxmz-tgdwjp/
  项目：  <project>/.mimocode/skills/tiaxmz-tgdwjp/

其他 Agent（如 Claude Code）：
  复制到其各自的 skills 目录即可，SKILL.md 为通用规范
```

MiMo Desktop 可在 **设置 → 插件** 页面看到「TIA PLC 项目开发」。新开会话后即可触发。

## 使用

对 Agent 说：

- 「写 TIA 程序」「做 PLC 项目」「博图编程」
- 「帮我写/改 PLC 控制程序」「用 TIA 做 XX 站」
- 直接发来 IO 表 / 控制要求 / 工艺描述，要求编写西门子 S7 程序

工作流必经"控制要求提纯 → 用户确认"关卡：Agent 会先把理解到的控制逻辑整理给你过目，你确认后才动代码。

## 目录结构

```text
tiaxmz-tgdwjp/
├── SKILL.md                          # 六步工作流、规则、示例、避坑速查
├── references/
│   ├── lad-s7dcl-syntax.md           # 梯形图 S7DCL 导入语法全套
│   └── framework-template.md         # 程序框架模板（按钮/动作/流程/模式）
└── locales/                          # 插件页显示名（zh-CN / en-US）
```

## 依赖

- 支持 Agent Skill 规范的客户端：MiMo Desktop / MiMoCode / Claude Code 等（skill 载体）
- `tia-portal` MCP 服务器（连接 TIA Portal Openness，需 TIA V20/V21 与 Openness 用户组权限）

## License

见 [LICENSE](./LICENSE)。
