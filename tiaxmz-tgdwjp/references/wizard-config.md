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
  "io": [ { "no": 1, "address": "I0.0", "type": "DI|DO|M", "name": "启动按钮", "symbol": "S1", "comment": "S2 启动按钮：1=按下" } ],
  "ioImages": ["io表.png"],
  "modes": [ { "name": "复位", "trigger": "复位信号=1 时按启动按钮" } ],
  "steps": [ { "no": 1, "action": "输送启动+搬运左行回初始位", "done": "搬运初始位 且 上料点有料", "delayMs": 0 } ],
  "notes": "自由备注"
}
```

## 解析要点（Agent）

1. **tiaVersion + plcs** → 任务 1 环境接入：按 `tiaVersion` 选 TIA；对 `plcs` 数组**每台**执行 `AddDeviceWithFallback(family, mlfb, firmware, name)`；PN/IE 网络按 `iface/ip/subnet` 配置（MCP 网络工具如 `ConnectDeviceNodesToProfinetSubnet`，IP 可在设备属性设置；多台 PLC 时按同子网规划地址）。项目名用 `project.name`。`firmware` 为 CPU 固件（S7-1200 支持 V4.1–V4.7，S7-1500 支持 V2.8–V3.1）。
2. **io** → 任务 2 变量表：`PlcBuildAndImport kind=tagtable`，变量名用 `name`（中文），注释用 `comment`，地址 `address`；`ioImages` 里的图片用视觉识别补齐/校核。
3. **modes + steps + signalConvention** → 任务 3 提纯素材：整理成模式×序列表 + 信号约定，**回呈使用者确认**后才进任务 4。
4. **steps** → 流程步模板：步号 ×5（1,5,10,…）按 `no` 顺序展开；`delayMs>0` 的步在到位后串 `TON(PT:=T#<delay>MS)`；`done` 为完成判据传感器条件。
5. **language** → 任务 5：`LAD` 按梯形图模板；`SCL` 用 LAD 块头 + `{ S7_Language := "SCL" }` 网络写 SCL 语句（TIA 导入兼容形式）。
6. 缺字段/不明确处（如电机/通信/HMI 未配）按 skill 的材料清单补问，不要臆造。

## 版本

- v1：型号 / IO / 模式 / 流程 / 语言 / 信号约定（核心链路）。
- 预留：`axis`（步进电机）、`communication`（站间通信）、`hmi`（型号/画面布局/图标功能）——向导二期模块。
