# wizard/project.json 配置格式（v1）

向导页（`wizard/index.html`）「一键生成」输出的配置包。Agent 收到后按本格式解析，走 tiaxmz-tgdwjp 六步流程生成 TIA 项目。

## 字段

```json
{
  "version": 1,
  "generator": "PLC Project Wizard v1",
  "generatedAt": "ISO 时间",
  "project": { "name": "主件供料站", "note": "补充说明" },
  "tiaVersion": "V21",
  "plcs": [
    {
      "no": 1,
      "name": "PLC_1",
      "family": "S7-1200",
      "model": "CPU 1215C DC/DC/DC",
      "mlfb": "6ES7215-1AG40-0XB0",
      "firmware": "V4.7",
      "ifaceType": "PN/IE",
      "iface": "PN/IE_1",
      "ip": "192.168.0.1",
      "subnet": "255.255.255.0"
    }
  ],
  "language": "LAD | SCL",
  "languageNote": "语言偏好说明",
  "signalConvention": { "note": "停止/急停常闭：1=正常 0=动作…" },
  "io": [ { "no": 1, "plc": "PLC_1", "address": "I0.0", "type": "DI|DO|M", "name": "启动按钮", "symbol": "S1", "comment": "S2 启动按钮：1=按下" } ],
  "attachments": [ { "name": "IO表.png", "kind": "image|doc", "dataBase64": "…" } ],
  "modes": [ { "plc": "PLC_1", "name": "复位", "trigger": "复位信号=1 时按启动按钮" } ],
  "flows": [ { "plc": "PLC_1", "text": "复位档按启动→升降抬起→夹爪松开→搬运回右侧位……" } ],
  "blocks": ["报警", "通讯"],
  "notes": "自由备注"
}
```

## 解析要点（Agent）

> **交付方式**：向导页「一键生成」输出/下载 `project.json`；使用者把它放进工作目录并说「按配置生成项目」后，Agent 按本文件解析并走 skill 六步流程。

> **留空语义**：`io` / `steps` / `modes` / `signalConvention.note` 等允许为空数组或空串——表示使用者未填。Agent **不得臆造**：按 skill 的材料清单补问，或先生成可填的空骨架。**必填项只有 PLC 型号（`plcs[].mlfb`）**。

1. **tiaVersion + plcs** → 任务 1 环境接入：按 `tiaVersion` 选 TIA；对 `plcs` 数组**每台**执行 `AddDeviceWithFallback(family, mlfb, firmware, name)`；PN/IE 网络按 `iface/ip/subnet` 配置（MCP 网络工具如 `ConnectDeviceNodesToProfinetSubnet`，IP 可在设备属性设置；多台 PLC 时按同子网规划地址）。项目名用 `project.name`。`firmware` 为 CPU 固件（S7-1200 支持 V4.1–V4.7，S7-1500 支持 V2.8–V3.1）。
2. **io + attachments** → 任务 2 变量表：`io` 为使用者逐行添加的点表（按 `plc` 分组到各 PLC）；`attachments` 为文档/图片附件（base64 内嵌）——先解码写盘，**图片用视觉识别、Office 用 python-docx/openpyxl 解析**出 IO 点，与 `io` 点表合并核对（附件提取与点表冲突时以附件原始内容为准，差异回呈确认）。
3. **modes + flows + signalConvention** → 任务 3 提纯素材：`modes`（按 `plc` 分组，含触发）+ `flows[].text`（使用者对每台 PLC 的自由文字描述）+ 信号约定，整理成模式×序列表回呈确认。
4. **flows** → 任务 3/4：把 `text` 提纯成流程步序列（步号 ×5）与完成判据；延时信息若写在文字里则转 `TON`。
5. **blocks** → 任务 4 可选库块（`报警`超时报警 FB / `通讯`站间 PUT-GET FC / `轴控`轴控 FC / `计时`节拍 FB / `产量`产量统计 / `HMI`画面二期），勾选即在框架外追加对应块；不勾选不生成。
6. **language** → 任务 5：`LAD` 按梯形图模板；`SCL` 用 LAD 块头 + `{ S7_Language := "SCL" }` 网络写 SCL 语句（TIA 导入兼容形式）。
6. 缺字段/不明确处（如电机/通信/HMI 未配）按 skill 的材料清单补问，不要臆造。

## 版本

- v1：型号 / IO / 模式 / 流程 / 语言 / 信号约定（核心链路）。
- 预留：`axis`（步进电机）、`communication`（站间通信）、`hmi`（型号/画面布局/图标功能）——向导二期模块。
