#!/usr/bin/env bash
# =============================================================================
# OpenClaw 硅基军团 · 任务执行脚本
# run_agent_task.sh
#
# 功能：接收任务描述，通过幕僚长（ChiefOfStaff）路由到对应专业Agent执行
# 用法：./run_agent_task.sh "<任务描述>"
# 示例：./run_agent_task.sh "查询今日原料库存情况"
# =============================================================================

set -euo pipefail

# ──────────────────────────────────────────────
# 0. 全局变量
# ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
LOG_FILE="${PROJECT_ROOT}/logs/task_${TIMESTAMP}.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ──────────────────────────────────────────────
# 1. 加载环境变量
# ──────────────────────────────────────────────
load_env() {
    local env_file="${PROJECT_ROOT}/.env"
    if [ -f "${env_file}" ]; then
        set -a
        source "${env_file}"
        set +a
    fi

    # 加载 openclaw.config.js
    export OPENCLAW_CONFIG="${PROJECT_ROOT}/openclaw.config.js"
}

# ──────────────────────────────────────────────
# 2. Agent 路由函数
# ──────────────────────────────────────────────
route_agent() {
    local task="$1"

    # 幕僚长路由引擎（基于关键词匹配）
    local routing_rules='
    [
      {"agent":"ProcurementMaterial","keywords":["原料","材料","库存原料","供应"]},
      {"agent":"ProcurementSupplier","keywords":["供应商","评估","准入","绩效"]},
      {"agent":"ProcurementPrice","keywords":["价格","采购成本","议价","降价","成本"]},
      {"agent":"ProductionPlanning","keywords":["生产计划","排产","产能","调度"]},
      {"agent":"ProductionScheduling","keywords":["排程","工单","工序","在制品"]},
      {"agent":"ProductionQuality","keywords":["质量","质检","合格","不良","标准"]},
      {"agent":"SalesOrder","keywords":["订单","订单管理","状态"]},
      {"agent":"SalesQuote","keywords":["报价","报价单","价格报价"]},
      {"agent":"SalesService","keywords":["客服","售后","投诉","退换"]},
      {"agent":"FinanceAccounting","keywords":["财务","核算","账务","报销","对账"]},
      {"agent":"FinanceReport","keywords":["报表","财务报表","利润","资产"]},
      {"agent":"FinanceRisk","keywords":["风控","风险","合规","审计","内控"]},
      {"agent":"OpsEquipment","keywords":["设备","维修","保养","故障"]},
      {"agent":"OpsWarehouse","keywords":["仓储","库存","出入库","仓库","盘点"]},
      {"agent":"OpsSupplyChain","keywords":["供应链","物流","配送","运输","交付"]},
      {"agent":"StrategyPlanning","keywords":["战略","规划","年度计划","目标"]},
      {"agent":"StrategyAnalysis","keywords":["分析","市场分析","竞品","数据洞察","趋势"]},
      {"agent":"StrategyProject","keywords":["项目","进度","里程碑","计划","验收"]},
      {"agent":"RD","keywords":["研发","产品","迭代","需求","PRD"]},
      {"agent":"HR","keywords":["人力","招聘","绩效","培训","员工","薪酬","考勤"]},
      {"agent":"Safety","keywords":["安全","EHS","检查","应急","隐患"]}
    ]
    '

    local routed="ChiefOfStaff"  # 默认幕僚长

    # 遍历规则进行关键词匹配
    local result=$(node -e "
    const rules = ${routing_rules};
    const task = '${task}';
    let matched = null;
    let maxScore = 0;

    for (const rule of rules) {
      let score = 0;
      for (const kw of rule.keywords) {
        if (task.includes(kw)) score++;
      }
      if (score > maxScore) {
        maxScore = score;
        matched = rule.agent;
      }
    }

    console.log(matched || 'ChiefOfStaff');
    " 2>/dev/null || echo "ChiefOfStaff")

    echo "${result}"
}

# ──────────────────────────────────────────────
# 3. 任务执行函数
# ──────────────────────────────────────────────
execute_task() {
    local agent="$1"
    local task="$2"
    local task_id="task_${TIMESTAMP}_${RANDOM}"

    echo -e "\n${CYAN}═══════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  硅基军团 · 任务执行${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
    echo -e "  任务ID : ${task_id}"
    echo -e "  路由Agent: ${GREEN}${agent}${NC}"
    echo -e "  任务描述: ${task}"
    echo -e "${CYAN}───────────────────────────────────────────────${NC}"

    # 记录任务日志
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] TASK_START | agent=${agent} | task=${task}" >> "${LOG_FILE}"

    # 调用 OpenClaw 执行任务（Node.js 实现）
    local start_time=$(date +%s%3N)

    local result=$(node -e "
    const config = require('${PROJECT_ROOT}/openclaw.config.js');
    const { v4: uuidv4 } = require('uuid');

    async function executeAgent() {
      const agent = '${agent}';
      const task = ${task@Q};
      const taskId = '${task_id}';

      // 构建 Agent 请求
      const agentConfig = config.agents[agent] || config.agents.chiefOfStaff;
      const llmConfig = config.llm;

      // 构造系统提示词
      const systemPrompt = \`你是 ${agentConfig.role}。
企业价值观：${config.soul.values.join('、')}
沟通风格：${config.communicationStyle}
决策原则：${config.decisionPrinciples.join('；')}
关键词路由：${agentConfig.keywords.join('、')}
\`\`;

      console.log(JSON.stringify({
        success: true,
        taskId: taskId,
        agent: agent,
        role: agentConfig.role,
        systemPrompt: systemPrompt,
        llmProvider: llmConfig.provider,
        config: {
          temperature: llmConfig[llmConfig.provider]?.temperature || 0.7,
          maxTokens: llmConfig[llmConfig.provider]?.maxTokens || 8192
        }
      }, null, 2));
    }

    executeAgent().catch(err => {
      console.error(JSON.stringify({ success: false, error: err.message }));
      process.exit(1);
    });
    " 2>&1)

    local exit_code=$?
    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    echo -e "\n${GREEN}[RESULT]${NC} Agent 执行配置:"
    echo "${result}" | head -20
    echo ""

    # 记录完成日志
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] TASK_END | agent=${agent} | duration=${duration}ms | exit=${exit_code}" >> "${LOG_FILE}"

    echo -e "${CYAN}───────────────────────────────────────────────${NC}"
    echo -e "  耗时: ${duration}ms"
    echo -e "  状态: $([ ${exit_code} -eq 0 ] && echo "${GREEN}成功${NC}" || echo "${RED}失败${NC}")"
    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
}

# ──────────────────────────────────────────────
# 4. 交互模式
# ──────────────────────────────────────────────
interactive_mode() {
    echo -e "\n${GREEN}欢迎使用硅基军团 · 交互模式${NC}"
    echo "输入任务描述，AI 将自动路由到对应专业 Agent"
    echo "输入 'exit' 或 'quit' 退出\n"

    while true; do
        echo -ne "${BLUE}硅基军团 >${NC} "
        read -r user_input

        if [ -z "${user_input}" ]; then
            continue
        fi

        if [[ "${user_input}" =~ ^(exit|quit|q)$ ]]; then
            echo -e "\n${YELLOW}再见！硅基军团随时待命。${NC}"
            break
        fi

        local agent=$(route_agent "${user_input}")
        execute_task "${agent}" "${user_input}"
    done
}

# ──────────────────────────────────────────────
# 5. 批量任务模式
# ──────────────────────────────────────────────
batch_mode() {
    local batch_file="$1"

    if [ ! -f "${batch_file}" ]; then
        echo -e "${RED}[ERROR]${NC} 批量任务文件不存在: ${batch_file}"
        exit 1
    fi

    echo -e "${BLUE}[BATCH]${NC} 开始执行批量任务: ${batch_file}"
    local line_num=0

    while IFS= read -r task; do
        line_num=$((line_num + 1))
        [ -z "${task}" ] && continue
        [[ "${task}" =~ ^#.*$ ]] && continue  # 跳过注释

        echo -e "\n--- 任务 ${line_num} ---"
        local agent=$(route_agent "${task}")
        execute_task "${agent}" "${task}"
        sleep 1  # 避免频率过快
    done < "${batch_file}"

    echo -e "\n${GREEN}[BATCH]${NC} 批量任务执行完成，共 ${line_num} 个任务"
}

# ──────────────────────────────────────────────
# 6. 状态检查
# ──────────────────────────────────────────────
status_check() {
    echo -e "\n${BLUE}硅基军团 · 系统状态检查${NC}"
    echo "────────────────────────────────────"

    # 检查数据库
    local db_path="${PROJECT_ROOT}/Company_Agent_Brain/company_brain.db"
    if [ -f "${db_path}" ]; then
        echo -e "  ${GREEN}✓${NC} 数据库: 已就绪 ($(du -h "${db_path}" | cut -f1))"
    else
        echo -e "  ${RED}✗${NC} 数据库: 未初始化，请先运行 init_agent_brain.sh"
    fi

    # 检查配置文件
    if [ -f "${PROJECT_ROOT}/openclaw.config.js" ]; then
        echo -e "  ${GREEN}✓${NC} 配置文件: openclaw.config.js"
    else
        echo -e "  ${RED}✗${NC} 配置文件: openclaw.config.js 缺失"
    fi

    # 检查环境变量
    if [ -f "${PROJECT_ROOT}/.env" ]; then
        echo -e "  ${GREEN}✓${NC} 环境变量: .env"
    else
        echo -e "  ${YELLOW}⚠${NC} 环境变量: 使用 .env.example 模板"
    fi

    # 检查日志目录
    if [ -d "${PROJECT_ROOT}/logs" ]; then
        echo -e "  ${GREEN}✓${NC} 日志目录: logs/"
    fi

    echo "────────────────────────────────────"
}

# ──────────────────────────────────────────────
# 7. 帮助信息
# ──────────────────────────────────────────────
show_help() {
    cat << 'EOF'
硅基军团 · Agent 任务执行脚本
=========================================

用法:
  ./run_agent_task.sh [OPTIONS] [TASK]

参数:
  TASK                     任务描述（纯文本）

模式:
  无参数                   进入交互模式
  -i, --interactive        进入交互模式（显式指定）
  -b, --batch <FILE>       批量任务模式
  -s, --status             系统状态检查
  -h, --help               显示帮助信息
  -r, --route <TASK>       仅显示任务路由结果，不执行

示例:
  ./run_agent_task.sh "查询今日原料库存"
  ./run_agent_task.sh -i
  ./run_agent_task.sh -b tasks/batch_purchase.txt
  ./run_agent_task.sh -s
  ./run_agent_task.sh -r "调整某产品价格到9.9美元"

路由 Agent 列表（20个专业 Agent）:
  ChiefOfStaff        幕僚长 · 默认调度
  ProcurementMaterial 原料采购专家
  ProcurementSupplier 供应商管理专家
  ProcurementPrice    采购价格分析师
  ProductionPlanning  生产计划专家
  ProductionScheduling 生产排程专家
  ProductionQuality   质量管控专家
  SalesOrder          订单管理专家
  SalesQuote          报价管理专家
  SalesService        客服与售后专家
  FinanceAccounting   财务核算专家
  FinanceReport       财务报表专家
  FinanceRisk         财务风控专家
  OpsEquipment        设备管理专家
  OpsWarehouse        仓储管理专家
  OpsSupplyChain      供应链管理专家
  StrategyPlanning    战略规划专家
  StrategyAnalysis    战略分析专家
  StrategyProject     项目管理专家
  RD                  研发管理专家
  HR                  人力资源专家
  Safety              安全管理专家

EOF
}

# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────
main() {
    mkdir -p "${PROJECT_ROOT}/logs"

    load_env

    case "${1:-}" in
        -i|--interactive|"")
            interactive_mode
            ;;
        -b|--batch)
            batch_mode "${2:-}"
            ;;
        -s|--status)
            status_check
            ;;
        -r|--route)
            agent=$(route_agent "${2:-}")
            echo "路由结果: ${agent}"
            ;;
        -h|--help)
            show_help
            ;;
        *)
            agent=$(route_agent "$1")
            execute_task "${agent}" "$1"
            ;;
    esac
}

main "$@"
