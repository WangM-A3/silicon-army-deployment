#!/usr/bin/env bash
# =============================================================================
# OpenClaw 硅基军团 · Agent Brain 初始化脚本
# init_agent_brain.sh
#
# 功能：初始化企业知识库目录、配置、数据库和Agent环境
# 适用：首次部署 / 环境重建
# =============================================================================

set -euo pipefail

# ──────────────────────────────────────────────
# 0. 全局变量
# ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
LOG_FILE="${PROJECT_ROOT}/logs/init_${TIMESTAMP}.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ──────────────────────────────────────────────
# 1. 初始化日志目录
# ──────────────────────────────────────────────
init_logging() {
    mkdir -p "${PROJECT_ROOT}/logs"
    mkdir -p "${PROJECT_ROOT}/security/audit_logs"
    echo "[${TIMESTAMP}] ====== 硅基军团初始化开始 ======" >> "${LOG_FILE}"
    echo -e "${BLUE}[INFO]${NC} 日志文件: ${LOG_FILE}"
}

# ──────────────────────────────────────────────
# 2. 检查环境依赖
# ──────────────────────────────────────────────
check_dependencies() {
    echo -e "\n${BLUE}[STEP 1/7]${NC} 检查环境依赖..."

    local missing=()

    command -v node >/dev/null 2>&1 || missing+=("node")
    command -v npm  >/dev/null 2>&1 || missing+=("npm")
    command -v bash >/dev/null 2>&1 || missing+=("bash")

    if [ ${#missing[@]} -ne 0 ]; then
        echo -e "${RED}[ERROR]${NC} 缺少依赖: ${missing[*]}"
        echo "请先安装以上依赖后重试。"
        exit 1
    fi

    local node_version=$(node -v | sed 's/v//')
    echo -e "${GREEN}[OK]${NC} Node.js ${node_version}, npm $(npm -v)"
}

# ──────────────────────────────────────────────
# 3. 加载环境变量
# ──────────────────────────────────────────────
load_env() {
    echo -e "\n${BLUE}[STEP 2/7]${NC} 加载环境变量配置..."

    local env_file="${PROJECT_ROOT}/.env"

    if [ -f "${env_file}" ]; then
        set -a
        source "${env_file}"
        set +a
        echo -e "${GREEN}[OK]${NC} 已加载 .env 配置文件"
    else
        if [ -f "${PROJECT_ROOT}/.env.example" ]; then
            cp "${PROJECT_ROOT}/.env.example" "${env_file}"
            echo -e "${YELLOW}[WARN]${NC} .env 文件不存在，已从 .env.example 复制模板"
            echo -e "${YELLOW}[WARN]${NC} 请编辑 ${env_file} 填入实际配置值"
        else
            echo -e "${RED}[ERROR]${NC} .env.example 也不存在，无法创建配置"
            exit 1
        fi
    fi
}

# ──────────────────────────────────────────────
# 4. 初始化目录结构
# ──────────────────────────────────────────────
init_directories() {
    echo -e "\n${BLUE}[STEP 3/7]${NC} 初始化企业知识库目录结构..."

    local dirs=(
        "0_company_base/01_compliance"
        "0_company_base/02_process"
        "0_company_base/03_resource"
        "1_project_assets"
        "2_agent_knowledge/01_skill_lib"
        "2_agent_knowledge/02_task_log"
        "3_team_collaboration/01_meeting_minutes"
        "3_team_collaboration/02_discussion"
        "4_archive"
        "logs"
        "security/audit_logs"
        "skills"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "${PROJECT_ROOT}/Company_Agent_Brain/${dir}"
        echo "  ✓ ${dir}" >> "${LOG_FILE}"
    done

    echo -e "${GREEN}[OK]${NC} 目录结构初始化完成（${#dirs[@]} 个目录）"
    echo "[INFO] 目录创建完成" >> "${LOG_FILE}"
}

# ──────────────────────────────────────────────
# 5. 初始化示例文档
# ──────────────────────────────────────────────
init_templates() {
    echo -e "\n${BLUE}[STEP 4/7]${NC} 生成示例文档模板..."

    # 合规文档模板
    cat > "${PROJECT_ROOT}/Company_Agent_Brain/0_company_base/01_compliance/README.md" << 'EOF'
# 企业合规文档库

本目录存放企业级合规文档，包括但不限于：
- 数据安全政策
- 信息保密制度
- 隐私保护规范
- 行业法规合规
- 安全审计报告

> 负责人：合规部门 | 更新周期：季度
EOF

    # 流程文档模板
    cat > "${PROJECT_ROOT}/Company_Agent_Brain/0_company_base/02_process/README.md" << 'EOF'
# 企业流程文档库

本目录存放企业标准操作流程（SOP）：
- 采购流程
- 生产流程
- 销售流程
- 财务流程
- 人员管理流程

> 负责人：运营部门 | 更新周期：年度
EOF

    # 资源文档模板
    cat > "${PROJECT_ROOT}/Company_Agent_Brain/0_company_base/03_resource/README.md" << 'EOF'
# 企业资源文档库

本目录存放企业核心资源信息：
- 供应商名录
- 客户名录
- 产品目录
- 设备台账
- 员工手册

> 负责人：行政部门 | 更新周期：实时
EOF

    # Agent 知识库 README
    cat > "${PROJECT_ROOT}/Company_Agent_Brain/2_agent_knowledge/README.md" << 'EOF'
# Agent 知识库

硅基军团 Agent 的核心知识库目录。

## 目录说明
- `01_skill_lib/` - 技能库：存放可复用的 Agent 技能模块
- `02_task_log/` - 任务日志：记录所有 Agent 任务执行记录

## 技能管理
新技能发布后，放入 `01_skill_lib/` 目录，命名规范：
`skill_<category>_<name>.md`
EOF

    # 团队协作 README
    cat > "${PROJECT_ROOT}/Company_Agent_Brain/3_team_collaboration/README.md" << 'EOF'
# 团队协作空间

记录团队协作全流程：
- `01_meeting_minutes/` - 会议纪要
- `02_discussion/` - 讨论记录

## 协作规范
- 会议纪要格式：`YYYYMMDD_会议名称.md`
- 讨论记录格式：`YYYYMMDD_HHMMSS_讨论主题.md`
EOF

    echo -e "${GREEN}[OK]${NC} 示例文档模板生成完成"
}

# ──────────────────────────────────────────────
# 6. 初始化 SQLite 数据库
# ──────────────────────────────────────────────
init_database() {
    echo -e "\n${BLUE}[STEP 5/7]${NC} 初始化 SQLite 记忆数据库..."

    local db_path="${PROJECT_ROOT}/Company_Agent_Brain/company_brain.db"
    export SQLITE_DB_PATH="${db_path}"

    # 使用 Node.js 初始化数据库
    node -e "
    const sqlite3 = require('sqlite3').verbose();
    const path = require('path');
    const dbPath = process.env.SQLITE_DB_PATH || '${db_path}';

    const db = new sqlite3.Database(dbPath, (err) => {
      if (err) {
        console.error('数据库连接失败:', err.message);
        process.exit(1);
      }
      console.log('✓ SQLite 连接成功:', dbPath);
    });

    // 启用 WAL 模式
    db.run('PRAGMA journal_mode=WAL');
    db.run('PRAGMA busy_timeout=30000');

    // 创建记忆表（Engram）
    db.run(\`
      CREATE TABLE IF NOT EXISTS engram (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        tier TEXT DEFAULT 'context',
        embedding BLOB,
        tags TEXT DEFAULT '[]',
        metadata TEXT DEFAULT '{}',
        access_count INTEGER DEFAULT 0,
        score REAL DEFAULT 0.5,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
      )
    \`);

    // 创建 FTS5 全文索引
    db.run(\`
      CREATE VIRTUAL TABLE IF NOT EXISTS engram_fts USING fts5(
        content,
        content_rowid='rowid',
        tokenize='unicode61 remove_diacritics 1'
      )
    \`, () => {
      console.log('✓ Engram FTS5 索引创建完成');
    });

    // 创建任务日志表
    db.run(\`
      CREATE TABLE IF NOT EXISTS task_log (
        id TEXT PRIMARY KEY,
        agent TEXT NOT NULL,
        task TEXT NOT NULL,
        result TEXT,
        status TEXT DEFAULT 'pending',
        duration_ms INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        completed_at TEXT
      )
    \`);

    // 创建审计日志表
    db.run(\`
      CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT (datetime('now')),
        user_id TEXT,
        action TEXT NOT NULL,
        resource TEXT,
        result TEXT,
        ip_address TEXT,
        user_agent TEXT,
        metadata TEXT DEFAULT '{}'
      )
    \`);

    // 创建知识库文档表
    db.run(\`
      CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        path TEXT NOT NULL,
        title TEXT,
        category TEXT,
        tags TEXT DEFAULT '[]',
        content TEXT,
        checksum TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
      )
    \`);

    db.close(() => {
      console.log('✓ 数据库初始化完成');
    });
    " >> "${LOG_FILE}" 2>&1

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[OK]${NC} SQLite 数据库初始化完成"
    else
        echo -e "${RED}[ERROR]${NC} 数据库初始化失败，详见日志"
    fi
}

# ──────────────────────────────────────────────
# 7. 安装 npm 依赖
# ──────────────────────────────────────────────
install_dependencies() {
    echo -e "\n${BLUE}[STEP 6/7]${NC} 安装 Node.js 依赖..."

    cd "${PROJECT_ROOT}"

    if [ ! -f "package.json" ]; then
        echo -e "${RED}[ERROR]${NC} package.json 不存在"
        exit 1
    fi

    if [ -d "node_modules" ]; then
        echo -e "${YELLOW}[SKIP]${NC} node_modules 已存在，跳过安装"
    else
        npm install >> "${LOG_FILE}" 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[OK]${NC} 依赖安装完成"
        else
            echo -e "${RED}[ERROR]${NC} 依赖安装失败，详见日志"
        fi
    fi
}

# ──────────────────────────────────────────────
# 8. 最终检查
# ──────────────────────────────────────────────
final_check() {
    echo -e "\n${BLUE}[STEP 7/7]${NC} 最终环境检查..."

    local checks=(
        "${PROJECT_ROOT}/openclaw.config.js"
        "${PROJECT_ROOT}/.env"
        "${PROJECT_ROOT}/Company_Agent_Brain/2_agent_knowledge/01_skill_lib"
        "${PROJECT_ROOT}/Company_Agent_Brain/2_agent_knowledge/02_task_log"
        "${PROJECT_ROOT}/Company_Agent_Brain/company_brain.db"
    )

    local all_ok=true
    for item in "${checks[@]}"; do
        if [ -e "${item}" ]; then
            echo -e "  ${GREEN}✓${NC} $(basename $(dirname ${item}))/$(basename ${item})"
        else
            echo -e "  ${RED}✗${NC} $(basename $(dirname ${item}))/$(basename ${item}) [缺失]"
            all_ok=false
        fi
    done

    if [ "${all_ok}" = true ]; then
        echo -e "\n${GREEN}=============================================="
        echo "  硅基军团 Agent Brain 初始化完成！"
        echo "==============================================${NC}"
        echo ""
        echo "  下一步："
        echo "  1. 编辑 .env 填入实际配置"
        echo "  2. 运行 ./scripts/run_agent_task.sh 启动任务"
        echo ""
    else
        echo -e "\n${RED}[ERROR]${NC} 部分检查项未通过，请修复后重试"
        exit 1
    fi
}

# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────
main() {
    init_logging
    check_dependencies
    load_env
    init_directories
    init_templates
    init_database
    install_dependencies
    final_check
}

main "$@"
