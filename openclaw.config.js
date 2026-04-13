/**
 * OpenClaw 企业级硅基军团 · 核心配置文件
 * Silicon Army · Company Agent Brain System
 *
 * 幕僚长（ChiefOfStaff）调度模式
 * 1 个主 Agent + 20 个专业 Agent，关键词路由
 */

const path = require('path');

// ──────────────────────────────────────────────
// 1. 全局基础配置
// ──────────────────────────────────────────────
module.exports = {
  version: "1.0.0",
  environment: process.env.OPENCLAW_ENV || "production",
  logLevel: process.env.OPENCLAW_LOG_LEVEL || "info",

  // OpenClaw 主目录
  home: process.env.OPENCLAW_HOME || "./Company_Agent_Brain",

  // ──────────────────────────────────────────────
  // 2. SOUL 配置（Agent 灵魂）
  // ──────────────────────────────────────────────
  soul: {
    // 企业价值观
    values: [
      "安全第一，合规优先",
      "数据驱动，智能决策",
      "协作共赢，敏捷响应",
      "持续进化，透明可审计"
    ],
    // 角色定位
    role: "企业智能幕僚长 · 硅基军团指挥官",
    // 沟通风格
    communicationStyle: "专业 · 简洁 · 可执行",
    // 决策原则
    decisionPrinciples: [
      "先合规，后效率",
      "证据支撑，逻辑推理",
      "多方案对比，最优推荐"
    ]
  },

  // ──────────────────────────────────────────────
  // 3. Agent World 统一身份
  // ──────────────────────────────────────────────
  agentWorld: {
    enabled: true,
    apiUrl: process.env.AGENT_WORLD_API_URL || "https://world.coze.site",
    apiKey: process.env.AGENT_WORLD_API_KEY,
    agentId: process.env.AGENT_ID || "b665c20e-0ae3-4f66-9a1e-ebf081d10aaa",
    username: "m-a3"
  },

  // ──────────────────────────────────────────────
  // 4. LLM Provider 配置
  // ──────────────────────────────────────────────
  llm: {
    provider: process.env.LLM_PROVIDER || "minimax",
    minimax: {
      apiKey: process.env.MINIMAX_API_KEY,
      model: process.env.MINIMAX_MODEL || "abab6.5s-chat",
      apiBase: process.env.MINIMAX_API_BASE || "https://api.minimax.chat/v1",
      temperature: 0.7,
      maxTokens: 8192
    },
    openai: {
      apiKey: process.env.OPENAI_API_KEY || "",
      model: "gpt-4o",
      apiBase: "https://api.openai.com/v1"
    }
  },

  // ──────────────────────────────────────────────
  // 5. 知识库配置
  // ──────────────────────────────────────────────
  knowledge: {
    basePath: process.env.KNOWLEDGE_BASE_PATH || "./Company_Agent_Brain/2_agent_knowledge",
    skillLibPath: process.env.SKILL_LIB_PATH || "./Company_Agent_Brain/2_agent_knowledge/01_skill_lib",
    taskLogPath: process.env.TASK_LOG_PATH || "./Company_Agent_Brain/2_agent_knowledge/02_task_log",
    // RAG 配置
    rag: {
      enabled: true,
      chunkSize: 512,
      chunkOverlap: 64,
      topK: 5,
      embeddingModel: "text-embedding-ada-002"
    }
  },

  // ──────────────────────────────────────────────
  // 6. 硅基军团 · 20 个专业 Agent 路由表
  // ──────────────────────────────────────────────
  agents: {
    chiefOfStaff: {
      name: "ChiefOfStaff",
      role: "幕僚长 · 任务调度中心",
      keywords: ["规划", "分析", "战略", "决策", "统筹", "协调", "概述", "总结"],
      routeMode: "keyword_match"
    },
    // ── 采购类 ──
    procurementMaterial: {
      name: "ProcurementMaterial",
      role: "原料采购专家",
      keywords: ["原料", "材料采购", "大宗商品", "库存原料", "供应"],
      routeMode: "keyword_match"
    },
    procurementSupplier: {
      name: "ProcurementSupplier",
      role: "供应商管理专家",
      keywords: ["供应商", "供应商评估", "供应商准入", "供应商绩效", "供应商合同"],
      routeMode: "keyword_match"
    },
    procurementPrice: {
      name: "ProcurementPrice",
      role: "采购价格分析师",
      keywords: ["价格", "采购成本", "议价", "降价", "价格分析", "成本优化"],
      routeMode: "keyword_match"
    },
    // ── 生产类 ──
    productionPlanning: {
      name: "ProductionPlanning",
      role: "生产计划专家",
      keywords: ["生产计划", "排产", "产能", "生产调度", "计划排程"],
      routeMode: "keyword_match"
    },
    productionScheduling: {
      name: "ProductionScheduling",
      role: "生产排程专家",
      keywords: ["排程", "生产排程", "工单", "工序", "在制品"],
      routeMode: "keyword_match"
    },
    productionQuality: {
      name: "ProductionQuality",
      role: "质量管控专家",
      keywords: ["质量", "质检", "合格率", "不良率", "质量标准", "质量改善"],
      routeMode: "keyword_match"
    },
    // ── 销售类 ──
    salesOrder: {
      name: "SalesOrder",
      role: "订单管理专家",
      keywords: ["订单", "订单管理", "订单查询", "订单状态", "订单确认"],
      routeMode: "keyword_match"
    },
    salesQuote: {
      name: "SalesQuote",
      role: "报价管理专家",
      keywords: ["报价", "报价单", "价格报价", "销售报价", "价格策略"],
      routeMode: "keyword_match"
    },
    salesService: {
      name: "SalesService",
      role: "客服与售后专家",
      keywords: ["客服", "售后", "投诉", "退换货", "客户反馈", "服务响应"],
      routeMode: "keyword_match"
    },
    // ── 财务类 ──
    financeAccounting: {
      name: "FinanceAccounting",
      role: "财务核算专家",
      keywords: ["财务", "核算", "账务", "记账", "报销", "对账"],
      routeMode: "keyword_match"
    },
    financeReport: {
      name: "FinanceReport",
      role: "财务报表专家",
      keywords: ["报表", "财务报表", "利润表", "资产负债表", "现金流量表", "财务分析"],
      routeMode: "keyword_match"
    },
    financeRisk: {
      name: "FinanceRisk",
      role: "财务风控专家",
      keywords: ["风控", "风险", "合规", "审计", "内控", "合规检查"],
      routeMode: "keyword_match"
    },
    // ── 运营类 ──
    opsEquipment: {
      name: "OpsEquipment",
      role: "设备管理专家",
      keywords: ["设备", "维修", "保养", "设备维护", "TPM", "设备故障"],
      routeMode: "keyword_match"
    },
    opsWarehouse: {
      name: "OpsWarehouse",
      role: "仓储管理专家",
      keywords: ["仓储", "库存", "出入库", "仓库", "库位", "盘点"],
      routeMode: "keyword_match"
    },
    opsSupplyChain: {
      name: "OpsSupplyChain",
      role: "供应链管理专家",
      keywords: ["供应链", "物流", "配送", "运输", "履约", "交付"],
      routeMode: "keyword_match"
    },
    // ── 战略类 ──
    strategyPlanning: {
      name: "StrategyPlanning",
      role: "战略规划专家",
      keywords: ["战略", "规划", "年度计划", "战略目标", "商业模式", "战略分析"],
      routeMode: "keyword_match"
    },
    strategyAnalysis: {
      name: "StrategyAnalysis",
      role: "战略分析专家",
      keywords: ["分析", "市场分析", "竞品分析", "数据分析", "洞察", "趋势"],
      routeMode: "keyword_match"
    },
    strategyProject: {
      name: "StrategyProject",
      role: "项目管理专家",
      keywords: ["项目", "项目管理", "项目进度", "里程碑", "项目计划", "项目验收"],
      routeMode: "keyword_match"
    },
    // ── 研发类 ──
    rd: {
      name: "RD",
      role: "研发管理专家",
      keywords: ["研发", "产品", "迭代", "需求", "PRD", "技术方案", "创新"],
      routeMode: "keyword_match"
    },
    // ── 人力类 ──
    hr: {
      name: "HR",
      role: "人力资源专家",
      keywords: ["人力", "招聘", "绩效", "培训", "员工", "HR", "考勤", "薪酬"],
      routeMode: "keyword_match"
    },
    // ── 安全类 ──
    safety: {
      name: "Safety",
      role: "安全管理专家",
      keywords: ["安全", "生产安全", "EHS", "安全检查", "应急预案", "隐患"],
      routeMode: "keyword_match"
    }
  },

  // ──────────────────────────────────────────────
  // 7. 记忆系统配置（Engram）
  // ──────────────────────────────────────────────
  memory: {
    enabled: true,
    type: "sqlite_fts",
    dbPath: process.env.SQLITE_DB_PATH || "./Company_Agent_Brain/company_brain.db",
    engram: {
      ngramMin: 1,
      ngramMax: 3,
      tierWeights: {
        fact: 1.0,
        insight: 0.85,
        plan: 0.7,
        context: 0.6
      },
      gatingScoreThreshold: 0.65,
      latThreshold: 35
    },
    dreaming: {
      enabled: true,
      schedule: "0 3 * * *",  // 每天凌晨3点执行睡眠整理
      lightSleepThreshold: 0.9,   // Jaccard 去重阈值
      deepSleepPromotionMin: 0.7  // Deep Sleep 晋升最低分
    }
  },

  // ──────────────────────────────────────────────
  // 8. 安全模块配置
  // ──────────────────────────────────────────────
  security: {
    enabled: true,
    piiDetection: {
      enabled: process.env.PII_DETECTION_ENABLED === "true",
      redactMode: process.env.PII_REDACT_MODE || "mask",
      types: ["email", "phone", "id_card", "bank_card", "api_key", "password"]
    },
    audit: {
      enabled: process.env.AUDIT_LOG_ENABLED === "true",
      logPath: process.env.AUDIT_LOG_PATH || "./security/audit_logs",
      rotation: "daily",
      retentionDays: 90
    },
    whitelist: {
      enabled: process.env.WHITELIST_DOMAIN_MODE === "strict",
      domains: (process.env.ALLOWED_DOMAINS || "api.openai.com,api.minimax.chat,world.coze.site,xiaping.coze.site").split(",")
    },
    gateway: {
      jwtSecret: process.env.JWT_SECRET || "openclaw-enterprise-default-secret-change-in-production",
      accessTokenTTL: parseInt(process.env.JWT_ACCESS_TOKEN_TTL) || 3600,
      refreshTokenTTL: parseInt(process.env.JWT_REFRESH_TOKEN_TTL) || 604800,
      rateLimit: {
        enabled: process.env.RATE_LIMIT_ENABLED !== "false",
        requestsPerMinute: parseInt(process.env.RATE_LIMIT_REQUESTS_PER_MINUTE) || 60,
        burst: parseInt(process.env.RATE_LIMIT_BURST) || 100
      }
    }
  },

  // ──────────────────────────────────────────────
  // 9. MCP Server 配置（可选）
  // ──────────────────────────────────────────────
  mcpServers: {
    github: {
      enabled: false,
      transport: "docker",
      image: "ghcr.io/github/github-mcp-server",
      env: {
        GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_MCP_TOKEN || ""
      }
    },
    slack: {
      enabled: false,
      transport: "docker",
      image: "mcp/slack",
      env: {
        SLACK_BOT_TOKEN: process.env.SLACK_BOT_TOKEN || "",
        SLACK_TEAM_ID: process.env.SLACK_TEAM_ID || ""
      }
    }
  },

  // ──────────────────────────────────────────────
  // 10. 飞书集成配置（可选）
  // ──────────────────────────────────────────────
  feishu: {
    enabled: false,
    appId: process.env.FEISHU_APP_ID || "",
    appSecret: process.env.FEISHU_APP_SECRET || "",
    webhookUrl: process.env.FEISHU_WEBHOOK_URL || ""
  },

  // ──────────────────────────────────────────────
  // 11. 邮件配置
  // ──────────────────────────────────────────────
  email: {
    enabled: false,
    smtp: {
      host: process.env.SMTP_HOST || "smtp.company.com",
      port: parseInt(process.env.SMTP_PORT) || 465,
      user: process.env.SMTP_USER || "",
      password: process.env.SMTP_PASSWORD || "",
      from: process.env.EMAIL_FROM || "agent@company.com"
    }
  },

  // ──────────────────────────────────────────────
  // 12. 插件与技能
  // ──────────────────────────────────────────────
  plugins: {
    skillsDir: "./skills",
    autoLoad: true,
    trustedSources: ["clawhub", "xiaping", "clawsec"]
  },

  // ──────────────────────────────────────────────
  // 13. 部署配置
  // ──────────────────────────────────────────────
  deployment: {
    mode: process.env.DEPLOY_MODE || "docker",
    docker: {
      network: process.env.DOCKER_NETWORK || "company_internal",
      restartPolicy: "unless-stopped",
      logDriver: "json-file",
      logMaxSize: "10m",
      logMaxFiles: 3
    },
    cron: {
      enabled: process.env.CRON_ENABLED === "true",
      expression: process.env.CRON_EXPRESSION || "0 8 * * *"
    }
  }
};
