# CALOS 接口契约 / CALOS SPECIFICATION

> **状态：** 公开接口定义 | **版本：** V1.0  
> 本文件定义 SINOSHOP 数字层与 CALOS 物理系统之间的数据交换格式。  
> CALOS 物理系统的具体实现存放于 `SinoSir/CALOS_OpenSources`。

---

## 1. 概述

CALOS（恒定高度控制系统）负责管理 SINOSHOP 跨海通道的物理层——防波堤、浮力控制、结构监测。  
SINOSHOP 数字层通过 R16 协议总线从 CALOS 获取物理状态数据，进行数字孪生与资产确权。

**核心原则：**
- CALOS 是物理数据的**提供者**，SINOSHOP 是数据的**消费者与治理者**。
- 数据交换通过标准化 API 完成，双方独立部署。
- CALOS 的核心控制算法属于 L3 资产，本文件仅定义接口。

---

## 2. 数据交换模型
[CALOS 物理系统] → [CALOS API Connector] → [R16 消息总线] → [SINOSHOP 数字孪生]
↓
[RWA 资产确权]

text

---

## 3. API 接口定义

### 3.1 获取物理构件状态

**端点：** `GET /api/v1/calos/component/{component_id}`
> 注：此 API 由 CALOS 系统提供，SINOSHOP 通过此接口拉取数据。

**响应体：**
```json
{
  "component_id": "SINOR-OCN-SFT-05-AFMB-A001-N000-A3",
  "timestamp": 1714204800000,
  "status": {
    "buoyancy_n": 9800000.0,
    "displacement_mm": 12.3,
    "stress_kpa": 45.7,
    "tilt_deg": 0.03,
    "vibration_hz": 0.5,
    "temperature_c": 22.1
  },
  "alerts": []
}
3.2 获取 U-Shield 防波堤状态
端点： GET /api/v1/calos/ushield/{zone}

响应体：

json
{
  "zone": "SFT-05",
  "timestamp": 1714204800000,
  "wave_height_m": 2.1,
  "wave_period_s": 8.3,
  "energy_absorption_percent": 87.5,
  "structural_integrity": "NORMAL"
}
3.3 推送数字孪生指令（SINOSHOP → CALOS）
端点： POST /api/v1/calos/command

请求体：

json
{
  "component_id": "SINOR-OCN-SFT-05-AFMB-A001-N000-A3",
  "command": "ADJUST_BUOYANCY",
  "params": {
    "target_newtons": 9805000.0,
    "rate": 100.0
  },
  "digital_signature": "..."
}
响应体：

json
{
  "command_id": "CMD-2026-0001",
  "status": "ACCEPTED",
  "estimated_completion_s": 30
}
4. 数据格式映射
CALOS 物理数据字段与 R16 遥测包（TelemetryPacket）的映射关系：

CALOS 字段	R16 Metric name	单位
buoyancy_n	buoyancy_force	N
displacement_mm	displacement	mm
stress_kpa	stress	kPa
tilt_deg	tilt_angle	deg
vibration_hz	vibration_freq	Hz
temperature_c	temperature	°C
wave_height_m	wave_height	m
energy_absorption_percent	energy_absorption	%
5. 跨仓库协作流程
CALOS 团队在 SinoSir/CALOS_OpenSources 维护物理控制逻辑与硬件驱动。

SINOSHOP 团队在 SinoSir/SINOSHOP 定义数据接口与协议标准。

双方通过本文件定义的 API 进行集成测试。

接口变更必须通过双方仓库的 PR 审核。

6. 变更记录
日期	变更	作者
2026-04-27	初始接口定义	梁振雄
*本文件由 SINOSHOP-Core 治理委员会维护，最后更新于 2026-04-27。*

text

**提交信息：** `Add CALOS interface specification`

---


