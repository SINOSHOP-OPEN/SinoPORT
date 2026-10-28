# 支持策略 / Support Policy

SINOSHOP 是一个软硬结合的超级工程。本策略基于 **LTS（长期支持）** 模型，明确各版本的生命周期承诺。

## 当前状态

🧪 **SINOSHOP 目前处于早期开发阶段（0.3）。**  
所有 0.3.x 版本均为 Active 状态，享受全面的安全修复、功能更新与 API 更新。

正式版发布后，将正式启用以下三层梯队模型。

## 版本梯队与生命周期（正式版启用后）

| 梯队 | 版本示例 | 支持类型 | 硬件兼容性保证 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **Active (当前主线)** | 1.x | 安全修复、功能更新、API 更新 | 最新固件签名 | 主要开发分支，享受所有更新。 |
| **Maintenance (长期支持)** | 旧稳定版 | **仅安全修复** | 已验证的硬件签名矩阵 | 为长期部署在生产环境中的节点提供关键安全保障。不增加新功能。 |
| **End-of-Life (EOL)** | 更早版本 | 无官方支持 | 无 | 存在已知风险。仓库 CI 将拒绝非安全补丁的合并。 |

## 针对硬件信任根的特殊治理

SINOSHOP 的软件版本与硬件信任根固件签名绑定。所有软件升级，无论新旧，必须遵守：

1. **固件签名矩阵：** 任何发布必须附带 `VERSION_MATRIX.md`，明确软件版本与兼容的固件签名的映射关系。
2. **影子模式验证：** **这是强制要求。** 即使源码开放，任何版本的二进制签名在通过“影子模式”灰度验证前，**绝对禁止**进入生产部署白名单。

## 结束生命周期的流程

1. 在 GitHub Releases 页面将对应版本标记为 `[DEPRECATED]`。
2. 在 `VERSIONS.json` 中将其状态迁移为 `eol`。
3. CI/CD 系统自动拒绝任何针对 EOL 分支的非安全补丁合并。

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
