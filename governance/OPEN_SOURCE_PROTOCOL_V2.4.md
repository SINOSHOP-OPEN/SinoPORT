# SINOSHOP 开源文件协议 V2.4

## 1. 引言

本协议适用于所有发布在 [SINOSHOP](https://github.com/SINOSHOP-OPEN/SinoPORT) 仓库中的源代码、构建产物、文档及治理文件（以下简称“本作品”）。  
本协议定义了版本生命周期、安全策略、兼容性承诺及贡献规范，是 SINOSHOP 开源治理的最高准则。

> 🧪 **当前阶段：** SINOSHOP 处于早期开发阶段（0.3）。正式版发布后，本协议中的分层治理模型将全面生效。

---

## 2. 版本定义与生命周期

本作品采用语义化版本控制 **MAJOR.MINOR.PATCH**，并遵循以下 **LTS 模型**：

| 梯队 | 状态 | 支持类型 | 硬件兼容性 |
|------|------|----------|-------------|
| **Active** | 当前主线 | 安全修复、功能更新、API 更新 | 最新固件签名 |
| **Maintenance** | 长期支持 | **仅安全修复** | 已验证的硬件签名矩阵 |
| **End-of-Life** | 已终止 | 无官方支持 | 无 |

版本生命周期由 `governance/SUPPORT_POLICY.md` 详细规定，机器可读的状态定义在 `governance/VERSIONS.json`。

---

## 3. 安全策略

安全问题请私下报告至 **support@sinoshop.org**（PGP 密钥见 `governance/SECURITY.md`）。  
我们承诺在 **48 小时**内确认，**5 个工作日内**完成初步评估。  
漏洞分级如下：

| 等级 | 定义 | 响应时间 |
|------|------|----------|
| **P0 (Critical)** | 影响物理安全（如 FLC 异常、结构完整性） | 24 小时内灰度部署 |
| **P1 (High)** | 影响数据安全（如加密原语泄露） | 7 天内修复 |
| **P2 (Low/Info)** | 文档、非关键功能 | 常规迭代 |

详情见 `governance/SECURITY.md`。

---

## 4. 兼容性承诺

### 4.1 API / ABI 兼容性
- **MAJOR** 版本允许不兼容的 API 变更。
- **MINOR** 及 **PATCH** 版本必须保持 **向后兼容**。  
- 闭源核心 `libsinoshop_core.so` 的 ABI 兼容性由 CI 自动检测，变更破坏兼容性将导致构建失败。

### 4.2 协议版本交换（R16 强制）
在 R16 的 TLS/mTLS 握手阶段，客户端与服务端必须交换 `protocol_version`。  
- 若客户端版本 < 服务端最小支持版本，服务端 **必须** 返回 `ERR_VERSION_EOL` 并断开连接。  
- 返回的错误信息中应包含升级指南链接（由 `VERSIONS.json` 提供）。

### 4.3 兼容性矩阵
具体客户端-服务端版本兼容关系由 `COMPATIBILITY.md` 维护。

---

## 5. 硬件信任根与固件签名

SINOSHOP 的软件版本与硬件信任根（TPM/SE）固件签名深度绑定。  
- 任何发布必须附带 `VERSION_MATRIX.md`，明确软件版本与兼容的固件签名映射。  
- **影子模式验证：** 即使源码开放，任何版本的构建产物签名在通过“影子模式”灰度验证前，**严禁**进入生产部署白名单。

---

## 6. 治理自动化

`governance/VERSIONS.json` 是本协议的唯一事实来源，驱动 CI/CD 流水线：
- 向 **EOL 分支** 提交的 PR 将自动构建失败（紧急安全补丁除外）。
- 向 **Maintenance 分支** 提交的 PR 将触发警告，禁止引入新功能。  
自动化检查由 `scripts/ci/validate_version.py` 及 `.github/workflows/version-policy.yml` 实现。

---

## 7. 弃用策略

- **编译期**：废弃 API 标注 `__attribute__((deprecated))`，CI 中设为 Error。  
- **运行时**：R16-Telemetry 记录 `protocol_version`，Dashboard 生成版本分布热力图，主动提示升级。  
- **EOL 前**：在代码中植入运行时告警：“[WARNING] Version X.x is reaching EOL. Please upgrade.”。

---

## 8. 贡献者须知

贡献前请阅读 `CONTRIBUTING.md`。  
提交代码即表示你同意将作品按本项目指定的开源许可证（见 `LICENSE`）进行许可。

---

## 9. 参考资料

本协议的相关细则文件均位于 `governance/` 目录下：
- `SECURITY.md` – 安全漏洞报告与处理流程
- `SUPPORT_POLICY.md` – 版本生命周期详细承诺
- `VERSIONS.json` – 机器可读的版本状态与升级指南
- `VERSION_MATRIX.md`（规划中）– 软硬件版本对应关系
## 致谢 / Hall of Fame

我们会向遵守本策略的漏洞报告者公开致谢（需征得本人同意）。  
感谢你对 SINOSHOP 安全做出的贡献。

---

**SINOSHOP：观天之道，执天之行，造福人民。**
**海生电、电养桥、桥造城、城惠民。**
**貞忠昭日月，惠民播春秋。**

*Observe Nature's Order, Align with Ocean's Rhythm, Advance the People's Welfare.*
*Ocean breeds energy, energy sustains the corridors, corridors build cities, and cities benefit the people.*
*Steadfast Loyalty glowing like the sun and moon; Benevolence nourishing the tide of time.*

*Root: Liang Zhenxiong*
*SINOSHOP*
*liangzhenxiong@gmail.com*

---

*本协议版本 V2.4，最后更新于 2026-04-26。*

---
