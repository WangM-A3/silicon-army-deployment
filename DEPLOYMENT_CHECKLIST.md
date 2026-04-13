# OpenClaw 硅基军团 · 企业级部署清单

> 版本：v1.0.0 | 更新日期：2025-01-01 | 适用：产业互联网 / 制造型企业

---

## 📋 目录

- [一、部署概览](#一部署概览)
- [二、目录结构](#二目录结构)
- [三、配置文件清单](#三配置文件清单)
- [四、部署步骤](#四部署步骤)
- [五、Agent 路由表](#五agent-路由表)
- [六、安全配置](#六安全配置)
- [七、运维指南](#七运维指南)
- [八、故障排查](#八故障排查)

---

## 一、部署概览

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   硅基军团 · 幕僚长模式                     │
│                    ChiefOfStaff                          │
│            （关键词路由 → 专业Agent集群）                   │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│ 采购类    │ 生产类   │ 销售类   │ 财务类   │ 运营类        │
│ Material │ Planning │ Order    │Accounting│ Equipment   │
│ Supplier │ Schedule │ Quote    │ Report  │ Warehouse   │
│ Price    │ Quality  │ Service  │ Risk    │ SupplyChain │
├──────────┴──────────┴──────────┴──────────┴──────────────┤
│ 战略类    │ 研发类   │ 人力类   │ 安全类                   │
│ Planning │   RD    │   HR    │  Safety                  │
│ Analysis │         │         │                          │
│ Project  │         │         │                          │
├─────────────────────────────────────────────────────────┤
│              记忆层（Engram）+ 安全层（Security）          │
│              MCP Server + 飞书集成 + 邮件系统             │
└─────────────────────────────────────────────────────────┘
```

### 20 个专业 Agent

| 类别 | Agent | 职责 |
|------|-------|------|
| 采购 | ProcurementMaterial | 原料采购 |
| 采购 | ProcurementSupplier | 供应商管理 |
| 采购 | ProcurementPrice | 采购价格分析 |
| 生产 | ProductionPlanning | 生产计划 |
| 生产 | ProductionScheduling | 生产排程 |
| 生产 | ProductionQuality | 质量管控 |
| 销售 | SalesOrder | 订单管理 |
| 销售 | SalesQuote | 报价管理 |
| 销售 | SalesService | 客服与售后 |
| 财务 | FinanceAccounting | 财务核算 |
| 财务 | FinanceReport | 财务报表 |
| 财务 | FinanceRisk | 财务风控 |
| 运营 | OpsEquipment | 设备管理 |
| 运营 | OpsWarehouse | 仓储管理 |
| 运营 | OpsSupplyChain | 供应链管理 |
| 战略 | StrategyPlanning | 战略规划 |
| 战略 | StrategyAnalysis | 战略分析 |
| 战略 | StrategyProject | 项目管理 |
| 研发 | RD | 研发管理 |
| 人力 | HR | 人力资源 |
| 安全 | Safety | 安全管理 |

---

## 二、目录结构

```
silicon-army-deployment/
├── .env.example              ✅ 环境变量模板
├── openclaw.config.js        ✅ OpenClaw 核心配置（20个Agent路由）
├── package.json              ✅ npm 依赖声明
├── scripts/
│   ├── init_agent_brain.sh   ✅ 一键初始化脚本
│   └── run_agent_task.sh     ✅ 任务执行脚本
├── security/
│   ├── access_control.json   ✅ RBAC 权限配置
│   ├── audit_log_config.json ✅ 审计日志配置
│   └── audit_logs/           📁 审计日志存储
└── Company_Agent_Brain/       📁 企业知识库根目录
    ├── 0_company_base/       📁 企业基础信息
    │   ├── 01_compliance/    📁 合规文档
    │   ├── 02_process/       📁 流程文档
    │   └── 03_resource/      📁 资源文档
    ├── 1_project_assets/    📁 项目资产
    ├── 2_agent_knowledge/    📁 Agent 知识库
    │   ├── 01_skill_lib/      📁 技能库
    │   └── 02_task_log/       📁 任务日志
    ├── 3_team_collaboration/ 📁 团队协作
    │   ├── 01_meeting_minutes/ 📁 会议纪要
    │   └── 02_discussion/    📁 讨论记录
    ├── 4_archive/           📁 历史归档
    ├── company_brain.db      📁 SQLite 记忆数据库
    └── logs/                  📁 系统运行日志
```

---

## 三、配置文件清单

### 3.1 环境变量 `.env.example`

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `OPENCLAW_ENV` | 运行环境 | `production` |
| `AGENT_WORLD_API_KEY` | Agent World 身份密钥 | `agent-world-xxx` |
| `LLM_PROVIDER` | LLM 提供商 | `minimax` |
| `MINIMAX_API_KEY` | MiniMax API Key | `your_key` |
| `KNOWLEDGE_BASE_PATH` | 知识库路径 | `./Company_Agent_Brain/2_agent_knowledge` |
| `AUDIT_LOG_ENABLED` | 审计日志开关 | `true` |
| `SQLITE_DB_PATH` | 数据库路径 | `./Company_Agent_Brain/company_brain.db` |
| `JWT_SECRET` | JWT 密钥（≥16字符） | `your_secret_here` |

### 3.2 核心配置 `openclaw.config.js`

| 配置节 | 说明 |
|--------|------|
| `soul` | Agent 价值观、角色定位、沟通风格 |
| `agentWorld` | Agent World 统一身份 |
| `llm` | LLM Provider（MiniMax / OpenAI） |
| `knowledge` | RAG 知识库配置 |
| `agents` | 20个专业Agent路由表 |
| `memory` | Engram 记忆层配置 |
| `security` | 安全模块配置 |
| `mcpServers` | MCP Server 配置 |
| `feishu` | 飞书集成配置 |

### 3.3 权限配置 `security/access_control.json`

| 角色 | 说明 |
|------|------|
| `admin` | 最高权限，配置管理 |
| `chief_of_staff` | 幕僚长，Agent 调度 |
| `department_head` | 部门负责人，部门级权限 |
| `operator` | 运维人员，运营操作 |
| `viewer` | 只读用户 |
| `external_partner` | 外部合作伙伴，受限权限 |

---

## 四、部署步骤

### 4.1 快速部署（推荐）

```bash
# 1. 克隆项目
cd silicon-army-deployment

# 2. 复制并编辑环境变量
cp .env.example .env
# 编辑 .env 填入实际 API Key 等

# 3. 一键初始化
chmod +x scripts/init_agent_brain.sh
bash scripts/init_agent_brain.sh

# 4. 启动任务（交互模式）
chmod +x scripts/run_agent_task.sh
bash scripts/run_agent_task.sh
```

### 4.2 Docker 部署

```bash
# 构建镜像
docker build -t silicon-army:latest .

# 运行容器
docker run -d \
  --name silicon-army \
  --env-file .env \
  -v $(pwd)/Company_Agent_Brain:/app/Company_Agent_Brain \
  -v $(pwd)/security:/app/security \
  -p 8080:8080 \
  silicon-army:latest
```

### 4.3 Docker Compose 部署（生产推荐）

```yaml
# docker-compose.yml
version: '3.8'
services:
  silicon-army:
    build: .
    env_file: .env
    volumes:
      - ./Company_Agent_Brain:/app/Company_Agent_Brain
      - ./security:/app/security
    ports:
      - "8080:8080"
    restart: unless-stopped
    networks:
      - company_internal

networks:
  company_internal:
    driver: bridge
```

```bash
docker compose up -d
docker compose logs -f
```

---

## 五、Agent 路由表

### 5.1 关键词路由规则

| Agent | 触发关键词 |
|-------|-----------|
| `ProcurementMaterial` | 原料、材料、库存原料、供应 |
| `ProcurementSupplier` | 供应商、评估、准入、绩效 |
| `ProcurementPrice` | 价格、采购成本、议价、降价 |
| `ProductionPlanning` | 生产计划、排产、产能 |
| `ProductionScheduling` | 排程、工单、工序 |
| `ProductionQuality` | 质量、质检、合格率 |
| `SalesOrder` | 订单、订单管理 |
| `SalesQuote` | 报价、报价单 |
| `SalesService` | 客服、售后、投诉 |
| `FinanceAccounting` | 财务、核算、报销 |
| `FinanceReport` | 报表、财务报表 |
| `FinanceRisk` | 风控、合规、审计 |
| `OpsEquipment` | 设备、维修、保养 |
| `OpsWarehouse` | 仓储、库存、盘点 |
| `OpsSupplyChain` | 供应链、物流、交付 |
| `StrategyPlanning` | 战略、规划、目标 |
| `StrategyAnalysis` | 分析、竞品分析 |
| `StrategyProject` | 项目、进度、里程碑 |
| `RD` | 研发、需求、PRD |
| `HR` | 人力、招聘、绩效 |
| `Safety` | 安全、EHS、应急 |

### 5.2 路由测试

```bash
# 测试路由
./scripts/run_agent_task.sh -r "查询今日原料库存"
# 路由结果: ProcurementMaterial

./scripts/run_agent_task.sh -r "调整某产品价格到9.9美元"
# 路由结果: ProcurementPrice

./scripts/run_agent_task.sh -r "生产计划需要调整"
# 路由结果: ProductionPlanning
```

---

## 六、安全配置

### 6.1 数据敏感等级

| 等级 | 说明 | 加密 | 审计 | 保留期 |
|------|------|------|------|--------|
| `low` | 公开信息 | ❌ | ❌ | 30天 |
| `medium` | 内部信息 | ✅ | ✅ | 90天 |
| `high` | 敏感信息 | ✅ | ✅ | 180天 |
| `critical` | 核心机密 | ✅ | ✅ | 365天 |

### 6.2 审计日志事件

- ✅ `agent_execution` - Agent 执行记录
- ✅ `authentication` - 认证事件
- ✅ `authorization` - 授权事件
- ✅ `pii_access` - PII 数据访问
- ✅ `pii_redaction` - PII 脱敏记录
- ✅ `sensitive_data_export` - 敏感数据导出
- ✅ `system_config_change` - 配置变更
- ✅ `skill_installation` - 技能安装
- ✅ `api_request` - API 请求
- ✅ `error` - 错误事件

---

## 七、运维指南

### 7.1 日常运维命令

```bash
# 查看系统状态
./scripts/run_agent_task.sh -s

# 交互模式
./scripts/run_agent_task.sh -i

# 批量任务
./scripts/run_agent_task.sh -b tasks/batch_purchase.txt

# 查看日志
tail -f Company_Agent_Brain/logs/task_*.log

# 健康检查
curl http://localhost:8080/health
```

### 7.2 数据库维护

```bash
# 备份数据库
cp Company_Agent_Brain/company_brain.db Company_Agent_Brain/backup/company_brain_$(date +%Y%m%d).db

# 清理过期日志（> 90天）
find Company_Agent_Brain/logs/ -name "*.log" -mtime +90 -delete
find security/audit_logs/ -name "*.jsonl" -mtime +90 -delete
```

### 7.3 定时任务（Cron）

| 时间 | 任务 | 说明 |
|------|------|------|
| `0 3 * * *` | Dreaming 睡眠整理 | 记忆整合与晋升 |
| `0 8 * * *` | 健康检查 | 每日系统状态报告 |
| `0 0 1 * *` | SOC 2 报告生成 | 月度合规报告 |
| `0 0 * * 0` | 日志归档 | 周归档审计日志 |

---

## 八、故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `sqlite3.OperationalError: database is locked` | 并发写入冲突 | 检查 `SQLITE_JOURNAL_MODE=WAL` 配置 |
| 路由结果不准确 | 关键词匹配失败 | 调整 `openclaw.config.js` 中的 `keywords` |
| PII 检测误报 | 正则规则过宽 | 调整 `security/access_control.json` 规则 |
| Agent World 连接失败 | API Key 错误 | 确认 `AGENT_WORLD_API_KEY` 配置正确 |
| 依赖安装失败 | Node 版本过低 | 升级至 Node.js ≥ 18.0 |
| 审计日志缺失 | 路径无写权限 | 检查 `security/audit_logs/` 目录权限 |

---

## 九、文件路径索引

| 文件 | 路径 |
|------|------|
| 环境变量模板 | `./silicon-army-deployment/.env.example` |
| OpenClaw 核心配置 | `./silicon-army-deployment/openclaw.config.js` |
| npm 依赖声明 | `./silicon-army-deployment/package.json` |
| 初始化脚本 | `./silicon-army-deployment/scripts/init_agent_brain.sh` |
| 任务执行脚本 | `./silicon-army-deployment/scripts/run_agent_task.sh` |
| RBAC 权限配置 | `./silicon-army-deployment/security/access_control.json` |
| 审计日志配置 | `./silicon-army-deployment/security/audit_log_config.json` |
| 部署清单文档 | `./silicon-army-deployment/DEPLOYMENT_CHECKLIST.md` |
| 初始化脚本日志 | `./silicon-army-deployment/logs/init_*.log` |
| 任务执行日志 | `./silicon-army-deployment/logs/task_*.log` |
| SQLite 数据库 | `./silicon-army-deployment/Company_Agent_Brain/company_brain.db` |

---

> **📌 注意**：`.env.example` 复制为 `.env` 后，请务必填入真实配置值，特别是 API Key 和 JWT Secret。
