# LAD S7DCL 导入语法全套（import 验证形式）

配套文件：`<块名>.s7dcl`（块声明+网络）与 `<块名>.s7res`（中文标题映射），**两者均为 UTF-8 WITH BOM**。
导入：`ImportFromDocuments(softwarePath, groupPath, importPath, fileNameWithoutExtension, importOption="Override")`。

## 块头模板

```
{
    S7_BlockTitle := "MLC_T1";          // 中文标题走 .s7res，可省略
    S7_Optimized := "TRUE";
    S7_PreferredLanguage := "LAD";       // 必须 LAD！纯 SCL 头导入失败
    S7_Version := "0.1"
}
FUNCTION "按钮" : Void                   // FC：FUNCTION "名" : Void
    ...
END_FUNCTION
```

FB：`FUNCTION_BLOCK "报警" ... END_FUNCTION_BLOCK`；OB1：`ORGANIZATION_BLOCK "Main" ... END_ORGANIZATION_BLOCK`；
全局 DB：`DATA_BLOCK 全局 VAR ... END_VAR END_DATA_BLOCK`；实例 DB：`DATA_BLOCK 报警_DB : 报警 END_DATA_BLOCK`。
FC 无 Static 段（仅 VAR_TEMP/VAR_INPUT/VAR_OUTPUT）；FB 可有 `VAR ... END_VAR` 静态段。

## .s7res 模板（仅 zh-CN，勿加 en-US）

```
MultiLingualTexts:
  - id: MLC_T1
    zh-CN: 按钮
  - id: MLC_N1
    zh-CN: N1 停止（常闭：1=正常 0=按下）→ 置停止标志位
```

块标题/网络标题引用：`S7_BlockTitle := "MLC_T1"`；网络属性块内 `S7_NetworkTitle := "MLC_N1"`。
DB 可以不带 .s7res。

## 网络与支路模型

```
    {
        S7_Language := "LAD";            // 每网络标注语言（SCL 网络用 "SCL"）
        S7_NetworkTitle := "MLC_N1"
    }
    NETWORK
        RUNG wire#powerrail
            Contact( "启动按钮" ) wire#w1
            S_Coil( "全局".模式.启动标志位 )
        END_RUNG
        RUNG wire#w1                     // 从 w1 起的扇出支路：同一条件驱动多个线圈
            R_Coil( "全局".模式.停止标志位 )
        END_RUNG
        RUNG wire#powerrail              // 并联第二支路，末端并入 w1 = OR
            Contact( "HMI启动" )
        END_RUNG wire#w1
    END_NETWORK
```

- `wire#wN` 是节点：支路中段 `wire#w1` 引出（tap），`END_RUNG wire#w1` 并入（join）。
- **多线圈扇出**：主支路 `… wire#w1 Coil(A)`，其余 `RUNG wire#w1 Coil(B)`。
- **并联 OR**：两支路都从 `wire#powerrail` 起，一支路中段 `wire#w1` 接线圈，另一支 `END_RUNG wire#w1` 并入。
- SCL 网络混编（LAD 头的块内）：`{ S7_Language := "SCL" } NETWORK <SCL语句;> END_NETWORK`。

## 指令表（左列=import 形式，照抄；右列=export 形式，勿用）

| 用途 | import 形式 |
|---|---|
| 常开 / 常闭触点 | `Contact( "启动按钮" )` / `I_Contact( "停止按钮" )` |
| 线圈 / 置位 / 复位 | `Coil( "启动指示灯" )` / `S_Coil( "全局".动作.夹爪夹取 )` / `R_Coil( ... )` |
| 比较（Int 等） | 先写 `{ S7_Templates := "SrcType := Int" }` 独占一行，再 `EQ_Contact( in1 := 5, in2 := "全局".模式.流程步 )`；GT/LT/NE 同型 |
| 传送 | `Move( in := 20, out1 => "全局".模式.流程步 )`（可多输出 out2） |
| 上升沿 | `P_Trig( "沿"."1" )` 串入支路（"沿" DB 位=边沿记忆；同一记忆每扫描周期只许用一次） |
| 定时器 TON | `"全局".延时_下降1.TON{ time_type := Time }( PT := T#500MS, ET => )`（TON_TIME 成员放全局 DB，每延时点独立实例） |
| 计数器 CTU | `"IEC_Counter_0_DB".CTU( r := "复位", pv := 9999, cv => "计数" )` |
| FC/FB 调用 | `"按钮"()` ；多个调用可串在一条支路：`"按钮"() "动作"() "流程"()` |
| 加减乘除 | `Add( in1 := a, in2 := 1, out => b )` / `Sub/Mul/Div` 同型 |
| 转换 | `Convert( in := x, out => y )`，属性 `{ S7_Templates := "[SrcType := Int, DestType := Real]" }` |
| 取最大 | `MAX( in1 := a, in2 := b, out => c )`，属性 `{ S7_Templates := "value_type := Real" }` |

时间字面量：`T#500MS`、`T#2s`。全局 DB 成员用 `"全局".模式.流程步` 形式引用；IO 变量直接 `"启动按钮"`。

## 扫描顺序与写法纪律

- 网络/支路按文件顺序执行，**后执行者同扫描周期最终生效**：急停/暂停/安全网络放**块尾**。
- 普通 `Coil` 全块对同一变量只写一处；需要多处驱动时用 `S_Coil/R_Coil`（S/R 允许多处）。
- 每个 P_TRIG 记忆位只在一个网络使用（两次用同一记忆，第二次永远读不到边沿）。
- 动作请求位由流程/模式置位（S），由动作块应答清除（R）；清除若不经到位传感器路径，必须同时 R 对应线圈（S 线圈是保持型）。
