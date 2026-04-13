# 硅基军团 MCP 安全最佳实践

> 适用版本：v1.0.0+  
> 依据：2025年4月 MCP 安全事件（GitHub MCP Server 凭证泄露）  
> 更新日期：2025-04-13

---

## 📌 摘要

2025年4月，多个主流MCP Server因配置缺陷导致凭证泄露（如GitHub MCP Server `GITHUB_PERSONAL_ACCESS_TOKEN` 通过URL参数传递被记录至日志）。本文件汇总硅基军团生产环境的MCP安全加固方案，覆盖 **传输安全**、**认证授权**、**审计日志**、**漏洞防御** 四大维度。

---

## 1. 传输层安全

### 1.1 仅使用安全传输协议

```json
{
  "mcp": {
    "transport": "streamablehttp",
    "tls": {
      "enabled": true,
      "minVersion": "TLS1.2",
      "certPath": "/etc/ssl/certs/army.crt",
      "keyPath": "/etc/ssl/private/army.key"
    }
  }
}
```

**规则：**
- ❌ 禁止使用 `stdio` 跨网络传输（仅限本地进程通信）
- ✅ 跨网络必须使用 `streamablehttp` + TLS 1.2+
- ✅ 使用内网Unix Socket替代TCP（风险最低）

### 1.2 IP 白名单

```json
{
  "mcp": {
    "auth": {
      "allowed_ips": [
        "10.0.0.0/8",
        "172.16.0.0/12"
      ],
      "block_on_first_failure": true,
      "failure_limit": 5,
      "failure_window_seconds": 300
    }
  }
}
```

**规则：**
- 所有MCP Server必须配置IP白名单
- 启用首次失败封禁（`block_on_first_failure: true`）

---

## 2. 认证与授权

### 2.1 凭证管理规范

| 场景 | 推荐方案 | 禁止方案 |
|------|----------|----------|
| 长期凭证 | 环境变量或密钥管理服务（AWS Secrets Manager / HashiCorp Vault） | ❌ URL参数、❌ 日志文件、❌ 代码硬编码 |
| 临时凭证 | OAuth 2.0 Token（短期） + 自动刷新 | ❌ 长期PAT |
| Agent间认证 | JWT + 签名验证 | ❌ 无验证直连 |

**GitHub MCP Server 修复方案（2025-04事件）：**
```bash
# 错误 ❌
claude mcp add github github.com -- GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx

# 正确 ✅ — 使用环境变量而非明文参数
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx
claude mcp add github github.com
```

### 2.2 RBAC 权限矩阵（MCP扩展）

已在 `access_control.json` 中新增以下MCP权限：

| 权限 | 适用角色 | 说明 |
|------|----------|------|
| `mcp:*` | admin | 完全控制 |
| `mcp:read` | chief_of_staff, department_head, operator | 读取MCP工具列表 |
| `mcp:execute` | chief_of_staff, department_head | 执行MCP工具 |
| `mcp:audit` | chief_of_staff, security_auditor | 读取MCP审计日志 |
| `security:read` | security_auditor | 读取安全配置（无执行权） |

**新增角色：`security_auditor`**
- 仅读取审计日志和安全配置
- 无Agent执行权限
- 适用于合规审计人员

### 2.3 凭证保险库（CredentialVault）

```python
from security.gui_guardian import CredentialVault

vault = CredentialVault()
storage_id = vault.store("github_token", "ghp_xxxx")  # HMAC-SHA256加密存储
```

**原则：**
- 核心凭证存入内存保险库，不落磁盘
- Session结束后自动清空（`vault.clear_all()`）
- 日志中凭证显示为 `[REDACTED]`

---

## 3. 审计日志（MCP专项）

### 3.1 审计事件类型

已在 `audit_log_config.json` 新增8类MCP专项事件：

| 事件类型 | 级别 | 说明 |
|----------|------|------|
| `mcp_tool_call` | INFO | 每次MCP工具调用 |
| `mcp_vulnerability_scan` | WARNING | 漏洞扫描结果 |
| `mcp_permission_denied` | HIGH | 权限边界检查拒绝 |
| `mcp_command_injection` | CRITICAL | 命令注入攻击检测 |
| `mcp_ssrf_attempt` | CRITICAL | SSRF攻击检测 |
| `mcp_credential_exposure` | CRITICAL | 凭证泄露检测 |
| `mcp_rate_limit_exceeded` | MEDIUM | 速率限制触发 |
| `mcp_soc2_report` | INFO | 月度SOC 2合规报告 |

### 3.2 日志保留与合规

```json
{
  "audit": {
    "retention": {
      "days": 90,
      "archiveBeforeDelete": true,
      "archivePath": "./security/audit_logs/archive"
    }
  }
}
```

**SOC 2 合规新增字段：**
- `CC6.7_mcp_security_controls` — MCP安全控制有效性
- `CC7.3_mcp_audit_trail` — MCP操作可追溯性
- `CC9.1_mcp_vulnerability_management` — 漏洞管理流程

---

## 4. 漏洞防御

### 4.1 命令注入防御

**检测正则（已内置于 `MCPAuditor`）：**
```python
# Shell特殊字符
r"[;&|`$]\s*\w+"
# 命令替换
r"\$\([^)]+\)"
# 反引号执行
r"`[^`]+`"
```

**防御措施：**
- 用户输入中禁止包含shell特殊字符
- 使用参数化调用而非字符串拼接
- MCP Server执行前强制参数白名单校验

### 4.2 SSRF 防御

**检测正则（已内置于 `MCPAuditor`）：**
```python
r"(?i)(url|endpoint|uri)\s*[=:]\s*['\"]?https?://[^'\"\s]+"
```

**防御措施：**
- 禁止用户控制URL参数
- 维护内部资源白名单（如内部API地址段）
- HTTP重定向严格限制在白名单域名内

### 4.3 凭证泄露防御

**检测正则（已内置于 `MCPAuditor`）：**
```python
r"(?i)(api[_-]?key|token|secret|password|auth)\s*[=:]\s*['\"]?[\w\-]{8,}"
```

**防御措施：**
- 所有凭证通过环境变量注入
- MCP Server日志中自动脱敏
- 凭证访问操作记录至 `mcp_credential_exposure` 事件

### 4.4 速率限制

```json
{
  "mcp": {
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 60,
      "burst_size": 10,
      "per_session": true
    }
  }
}
```

**告警规则：**
- `mcp_rate_limit_exceeded.count > 10 in 5 minutes` → `suspend_session`

---

## 5. MCP 服务器配置检查清单

### 部署前必须验证

```bash
# 1. 传输方式检查
jq ".mcp.transport" security/audit_log_config.json
# 预期：streamablehttp（禁止stdio跨网络）

# 2. 认证检查
jq ".mcp.auth.enabled" security/audit_log_config.json
# 预期：true

# 3. IP白名单检查
jq ".mcp.auth.allowed_ips | length" security/audit_log_config.json
# 预期：> 0

# 4. 凭证脱敏检查
grep -r "api_key\|token\|secret" ./security/audit_logs \
  | grep -v "REDACTED" | grep -v "\.keep"
# 预期：无匹配（所有凭证已脱敏）

# 5. MCP审计模块集成检查
python -c "from security.mcp_audit import AUDITOR; print('MCP Audit: OK')"
# 预期：MCP Audit: OK

# 6. 漏洞扫描运行
python -c "
from security.mcp_audit import MCPAuditor
auditor = MCPAuditor()
report = auditor.run_vulnerability_scan('config', {
    'mcp': {'transport': 'streamablehttp', 'auth': {'enabled': True}},
    'audit': {'enabled': True}
})
print(f'Risk Score: {report.overall_risk_score:.2f}')
# 预期：Risk Score ≤ 0.3
"
```

---

## 6. 应急响应流程

```
┌─────────────────────────────────────────────────────┐
│  MCP 安全事件响应流程                                 │
├─────────────────────────────────────────────────────┤
│ 1. 检测到 mcp_command_injection / mcp_ssrf_attempt  │
│    ↓                                                 │
│ 2. 立即通知管理员（immediate_notify）                │
│    ↓                                                 │
│ 3. 封禁相关会话（suspend_session）                   │
│    ↓                                                 │
│ 4. 保存完整审计日志供取证                             │
│    ↓                                                 │
│ 5. 调查工具调用链，定位漏洞点                          │
│    ↓                                                 │
│ 6. 修复配置或代码，更新 MCP Server                    │
│    ↓                                                 │
│ 7. 重新运行漏洞扫描，验证修复                          │
│    ↓                                                 │
│ 8. 更新本文件记录本次事件                             │
└─────────────────────────────────────────────────────┘
```

---

## 7. 参考来源

| 来源 | 链接 | 说明 |
|------|------|------|
| GitHub MCP Server 事件报告 | https://github.com/github/copilot-extensions/issues | 2025-04凭证泄露事件 |
| Anthropic MCP安全指南 | MCP官方文档 | 传输安全、认证规范 |
| OWASP API Security | https://owasp.org/API-Security/ | SSRF/Cmd-Injection防御 |
| SOC 2 CC框架 | AICPA SOC 2标准 | 合规审计要求 |
