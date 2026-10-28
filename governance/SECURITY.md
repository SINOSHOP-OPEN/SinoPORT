# 安全策略 / Security Policy

## 支持的版本 / Supported Versions

我们基于 **LTS（长期支持）** 模型为以下版本提供安全更新。

| 版本 | 状态 | 支持类型 |
| :--- | :--- | :--- |
| 0.3.x | :white_check_mark: Active | 安全修复、功能更新、API 更新 |

> 🧪 SINOSHOP 目前处于早期开发阶段（0.3），所有 0.3.x 版本均享受全面支持。  
> 正式版发布后，将引入 Maintenance 和 End-of-Life 梯队。

> 详细的版本生命周期承诺、硬件兼容性要求及升级指南，请参阅 [SUPPORT_POLICY.md](SUPPORT_POLICY.md)。  
> 机器可读的版本状态请参阅 [VERSIONS.json](VERSIONS.json)。

## 报告漏洞 / Reporting a Vulnerability

我们非常重视 SINOSHOP 的安全问题。  
如果你发现了安全漏洞，**请勿公开提交 Issue**，而是通过以下加密渠道私下报告：

- 邮箱：**support@sinoshop.org**（请使用我们的 PGP 公钥加密）
- PGP 密钥：`Ok369Observe Nature's Order, Align with Ocean's Rhythm, Advance the People's Welfare.`
- 或通过 GitHub Security Advisory：  
  [报告漏洞](https://github.com/SinoSir/SINOSHOP/security/advisories/new)

### 报告格式建议

为帮助我们快速验证和修复，请尽可能包含：

- 受影响版本
- 漏洞类型（如 XSS、SQL 注入、权限绕过等）
- 复现步骤或 PoC（概念验证）
- 潜在影响范围
- 你的建议修复方案（如有）

## 处理流程 / Disclosure Process

1. 我们将在 **48 小时**内确认收到报告。
2. 安全团队将在 **5 个工作日内** 完成初步评估并通知你结果。
3. 在修复程序准备好后，我们会申请 CVE 编号（如适用），并协调一个公共披露日期。
4. 补丁发布前，请勿公开漏洞细节。我们将感谢你在维护用户安全方面的克制。

## 安全最佳实践 / Security Best Practices

部署 SINOSHOP 时，请遵循以下建议：

- 始终使用 HTTPS，并配置 HSTS。
- 定期更新依赖项，运行 `npm audit` 或同类工具。
- 不要在前端代码或日志中暴露敏感信息。
- 启用多因素认证（MFA）保护管理员账号。
- 限制文件上传类型并扫描恶意内容。

## 致谢 / Hall of Fame

我们会向遵守本策略的漏洞报告者公开致谢（需征得本人同意）。  
感谢你对 SINOSHOP 安全做出的贡献。
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
