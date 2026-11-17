<div align="center">

![晚霞中的海上花园 · 碧海蓝天](media/seascape/shop_coast_dusk.jpg)

# SINOSHOP —— 共建共享，海洋家园，众志成城。

### 可移动、抗台风、人海和谐的生态花园社区

> **观天之道，执天之行。以术载道，造福众生。**

<br>

<div align="center">

*愿海如镜，人如舟。*

</div>

<br>

[![可复现验证](https://img.shields.io/badge/可复现验证-21%20%2F%2021%20PASS-2ea88c?style=flat-square&logo=python&logoColor=white)](https://gitee.com/sinoshop/sinoshop-os)

[![Apache-2.0 License](https://img.shields.io/badge/License-Apache--2.0-2ea88c?style=flat-square)](LICENSE)

</div>

---

## 三大版图矩阵

> SinoPORT（悬浮港）解决重载稳态，SinoSFT（跨海隧道）探索空间跨越，
> SINOSHOP（海洋城市）构建生态人居。**三者合一，拼凑出属于未来的海洋文明。**

| 版图 | 定位 | 主张 | 仓库 |
|:--|:--|:--|:--|
| **SinoPORT** | 悬浮港 | 无桩基超级刚体，重载交通下保持毫米级平顺作业面 | [gitee](https://gitee.com/sinoshop/SinoPORT) ｜ [GitHub](https://github.com/SINOSHOP-OPEN/SinoPORT) |
| **SinoSFT** | 跨海隧道 | 以数学为宪法，探索深海跨越的全新结构形态 | [gitee](https://gitee.com/sinoshop/sinosft) ｜ [GitHub](https://github.com/SINOSHOP-OPEN/sinosft) |
| **SINOSHOP** | 海洋城市 | 可移动、抗台风、人海和谐的生态花园社区 | **本仓库** ｜ [GitHub](https://github.com/SINOSHOP-OPEN/SINOSHOP) |

---

## 卷首 · 海之底色

**构建可移动、抗台风、人海和谐的生态花园社区。贞忠昭日月，惠民播春秋。**

SINOSHOP 是自浮式智能海洋城市运营平台。它不是一座漂浮的建筑，
而是一套**可以生长的城市基础设施** —— 平台越大，静水回复刚度越高；
模块可拆可换，城市可以像拼装积木一样逐步成形。

我们不与海洋争夺空间。我们让结构**浮在海面**，把波浪与载荷在体系内部化解，
把深水航道、岸线生态与渔业通道完整留给海洋本身。

### 设计哲学主线

**海生电 → 电养船 → 船搭桥 → 桥造城 → 城惠民**

从海洋能源自给，到船舶自持，到跨海通道成形，最终到海洋城市成形 ——
四层范式由此贯通：材料 → 结构 → 场景 → 哲学。

### 六大主张

| 主张 | 事实 | 佐证 |
|:--|:--|:--|
| **⚓ 无桩基超级刚体** | 张力索按八卦方位布置，拉结成超级刚体；各方位分工按实测水动力确定 | 力学剖面图 |
| **🌪️ 极限消浪** | 四梯队串联（消浪金字塔 + 红树林 + 生态花园 + 内堤），外海来波经四梯队逐级削减至内港显著平稳 | 实测 |
| **🌿 东方象数 × 流体力学** | 八卦方位对应消浪/发电/抗风/导流功能分区；**象数负责「形」，力水负责「真」** | CFD 校核 |
| **🔬 可复现的工程闭环** | 几何/工况/装配约束同源一处，实体校验 **21 / 21 PASS** | 校验脚本 |
| **🌱 生态优先** | 消浪与生态同步设计，防波堤模块表面设种植基床，培育红树林及耐盐滨海植物 | 设计文档 |
| **🔗 标准化与可追溯** | 构件编码 **100% 可追溯**；模块尺寸整除无余数 | 编码规范 |

### 六宗旨实证（每条均有实测支撑）

| 宗旨 | 实证 |
|:--|:--|
| 轻量化 | 复合材料显著轻于纯钢，**减重约四分之三**（密度比属受控口径，不在公开层提供具体值） |
| 浮空性 | 等效密度低于海水，结构本体即浮 |
| 标准化 | 构件编码 **100% 可追溯**；模数阵列整除无余数（容积属受控口径，不在公开层提供具体值） |
| 安全 | 储备红线 **60%~80%**；压载配平带心对称 |
| 节约 | 轻 77.1% → 材料、运力、坞站**三处同省** |
| 高效 | 装配流程 7~8 步；调载窗口覆盖全部储备带 |

每个对外数字都由**独立断言脚本判定** ——
**人可以写文案，但不能写 PASS。**

---

## 中卷 · 四季流转

<div align="center">

![夏日波光](media/seascape/summer_sparkle.jpg)

</div>

### 开放沙盒 · 封闭核心

本仓库是**公开发布面**：呈现系统的宏观形态、公开图面与可复现的核验数据。

功能定义接口，核心实现细节（材料配方、阀门设计、控制算法、密封结构）
均被封装为宏观参数 —— **开放沙盒，封闭核心。**

- **可公开** —— 架构原则、编码规范、界面定义、仿真接口、验证脚本
- **按角色分发** —— 施工图纸、工艺细节、认证材料

### 仓库结构

```
sinoshop-os/
├── 00_Legal/                     ← 贡献者荣誉与安全声明
├── Documentation/                ← 海洋城市白皮书（中/英）
├── CLA.md                        ← 贡献者许可协议
├── CONTRIBUTING.md               ← 参与方式 · 数字存证与共建共享
├── SECURITY.md                   ← 安全策略 · 受控范围披露通道
├── ENGINEERING.md                ← 工程总纲
├── INDEX.md                      ← 索引
├── Standard_Floating_Module_Spec_V5.6.md  ← 标准浮箱模块规范
├── SINOSFT-PATH/                 ← 跨海通道路径
├── SINOSFT_Bridge_Segment/       ← 跨海通道桥梁段
├── open-collab/                  ← 开源共创区（T1 大众层 / T2 开发者层素材与治理文件）
├── scripts/ci/                   ← CI 校验脚本（含公开层尺寸脱敏扫描器）
└── .githooks/                    ← 随代码分发的本地脱敏钩子（提交/推送闸门）
```

> **参与前请先启用本地脱敏钩子**（一次性）：
> ```bash
> sh scripts/enable_hooks.sh
> ```
> 启用后，每次提交与推送会自动扫描并在检出受控范围参数时拦截。
> 规则形态公开可查（见 [`CONTRIBUTING.md`](CONTRIBUTING.md)），
> 具体工程真值保存在受控层，不进本仓库。

### 生态项目

基于本仓库定义的核心规范，以下项目正在构建开放海洋工程生态：

- **[SINOSHIP/sinoshop-openice](https://gitee.com/SINOSHIP/sinoshop-openice) — 极地氢能全链条仿真平台**
- **[SINOSHIP/sinoship](https://gitee.com/SINOSHIP/sinoship) — 船舶设计与航运开源基础设施**
- **[sinoshop/sinosft](https://gitee.com/sinoshop/sinosft) — 跨海悬浮隧道浮桥**
- **[sinoshop/SinoPORT](https://gitee.com/sinoshop/SinoPORT) — 悬浮港旗舰工程**

---

## 谁在推动

- **SINOSHOP** —— 设计与工程团队
- 开放协作：任何人都可以提交 issue、复现验证、提出改进
- 贡献即确权 —— 详见 [`CONTRIBUTING.md` 第七章](CONTRIBUTING.md) 与
  [`00_Legal/CONTRIBUTOR_HONOR_ATTESTATION.md`](00_Legal/CONTRIBUTOR_HONOR_ATTESTATION.md)

---

## 许可与引用

代码与图面遵循本仓库 `LICENSE`（Apache-2.0）。
引用本项目时请注明出处；图面可用于非商业介绍，商业使用请先联系团队。

---

## 尾卷 · 月夜归航

<div align="center">

![月光洒在海面上](media/seascape/moonlight_sea.jpg)

**共建共享，海洋家园，众志成城**

---

### 人可以写文案，但不能写 PASS。

*愿海如镜，人如舟。*

</div>



---

愿海如镜，人如舟，道心即我心，心地无非，心地无痴，见境不乱。
