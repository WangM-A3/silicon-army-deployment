#!/bin/bash
# =============================================================================
# 外贸硅基军团 - 一键部署脚本
# =============================================================================
# 适用环境：Ubuntu 20.04+ / Debian 11+
# 使用方式：bash deploy.sh
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查root权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_warn "建议使用sudo运行此脚本以获得完整权限"
    fi
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# =============================================================================
# 1. 系统环境检查
# =============================================================================

log_step "========================================"
log_step "  1. 检查系统环境"
log_step "========================================"

# 检查操作系统
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
    log_info "操作系统: $PRETTY_NAME"
else
    log_error "无法识别操作系统"
    exit 1
fi

# 验证支持的操作系统
if [[ "$OS" != "ubuntu" && "$OS" != "debian" && "$OS" != "centos" && "$OS" != "rocky" ]]; then
    log_warn "未测试的操作系统，可能存在兼容性问题"
fi

# 检查Python版本
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -ge 8 ]]; then
        log_info "Python版本: $PYTHON_VERSION ✓"
    else
        log_error "需要Python 3.8+，当前版本: $PYTHON_VERSION"
        exit 1
    fi
else
    log_error "未安装Python3"
    log_info "安装Python3..."
    if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
    elif [[ "$OS" == "centos" || "$OS" == "rocky" ]]; then
        sudo yum install -y python3 python3-pip
    fi
fi

# 检查Git
if ! command -v git &> /dev/null; then
    log_info "安装Git..."
    sudo apt install -y git
fi

# =============================================================================
# 2. 创建应用目录和用户
# =============================================================================

log_step "========================================"
log_step "  2. 创建应用环境"
log_step "========================================"

APP_NAME="silicon-army"
APP_DIR="/var/www/$APP_NAME"
APP_USER="www-data"
APP_PORT=5000

# 创建应用目录
if [ -d "$APP_DIR" ]; then
    log_warn "应用目录已存在: $APP_DIR"
    read -p "是否要重新部署？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "取消部署"
        exit 0
    fi
    # 备份旧版本
    BACKUP_DIR="/var/www/${APP_NAME}_backup_$(date +%Y%m%d_%H%M%S)"
    sudo mv "$APP_DIR" "$BACKUP_DIR"
    log_info "旧版本已备份到: $BACKUP_DIR"
fi

# 创建目录结构
log_info "创建目录结构..."
sudo mkdir -p "$APP_DIR"/{data,logs,static,templates}
sudo mkdir -p /var/log/gunicorn

# 设置权限
if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
    sudo chown -R www-data:www-data "$APP_DIR"
elif [[ "$OS" == "centos" || "$OS" == "rocky" ]]; then
    sudo chown -R nginx:nginx "$APP_DIR"
    APP_USER="nginx"
fi

# =============================================================================
# 3. 复制应用文件
# =============================================================================

log_step "========================================"
log_step "  3. 复制应用文件"
log_step "========================================"

# 复制应用文件（排除.env等敏感文件）
log_info "复制应用文件..."
sudo cp -r "$SCRIPT_DIR"/* "$APP_DIR/" 2>/dev/null || true

# 创建.env文件
if [ ! -f "$APP_DIR/.env" ]; then
    log_info "创建环境配置文件..."
    sudo cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    sudo chown $APP_USER:$APP_USER "$APP_DIR/.env"
    log_warn "请编辑 $APP_DIR/.env 填入您的配置"
fi

# =============================================================================
# 4. 创建Python虚拟环境
# =============================================================================

log_step "========================================"
log_step "  4. 配置Python环境"
log_step "========================================"

log_info "创建Python虚拟环境..."
cd "$APP_DIR"
sudo python3 -m venv venv
source venv/bin/activate

log_info "安装依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    log_info "依赖安装成功 ✓"
else
    log_error "依赖安装失败"
    exit 1
fi

# =============================================================================
# 5. 配置数据库
# =============================================================================

log_step "========================================"
log_step "  5. 初始化数据库"
log_step "========================================"

log_info "初始化数据库..."
cd "$APP_DIR"
source venv/bin/activate
python3 -c "from models import db, init_db; from app import create_app; app = create_app(); init_db(app)"
# 简化的初始化命令
python3 -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('Database initialized')
"

log_info "数据库初始化完成 ✓"

# =============================================================================
# 6. 配置Gunicorn
# =============================================================================

log_step "========================================"
log_step "  6. 配置Gunicorn服务"
log_step "========================================"

# 创建Gunicorn systemd服务文件
log_info "创建Systemd服务..."
sudo tee /etc/systemd/system/gunicorn-$APP_NAME.service > /dev/null <<EOF
[Unit]
Description=Gunicorn for $APP_NAME
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:$APP_PORT \
    --timeout 120 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --log-level info \
    app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
sudo systemctl daemon-reload

log_info "Gunicorn服务配置完成 ✓"

# =============================================================================
# 7. 配置Nginx
# =============================================================================

log_step "========================================"
log_step "  7. 配置Nginx反向代理"
log_step "========================================"

# 检查Nginx是否安装
if ! command -v nginx &> /dev/null; then
    log_info "安装Nginx..."
    sudo apt install -y nginx
fi

# 创建Nginx配置
DOMAIN=${DOMAIN:-silicon-army.com}
LOG_FILE="/var/log/nginx/${APP_NAME}_access.log"
ERROR_LOG="/var/log/nginx/${APP_NAME}_error.log"

log_info "创建Nginx配置..."
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # 重定向到HTTPS（SSL配置后启用）
    # return 301 https://\$server_name\$request_uri;
    
    # 临时HTTP配置
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket支持（如需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件
    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 上传文件（如有）
    location /uploads/ {
        alias $APP_DIR/data/uploads/;
        expires 7d;
    }
    
    # 日志
    access_log $LOG_FILE;
    error_log $ERROR_LOG;
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/

# 测试Nginx配置
if sudo nginx -t; then
    log_info "Nginx配置测试通过 ✓"
else
    log_error "Nginx配置测试失败"
    exit 1
fi

# 重启Nginx
sudo systemctl restart nginx
log_info "Nginx已启动 ✓"

# =============================================================================
# 8. 配置SSL证书（可选）
# =============================================================================

log_step "========================================"
log_step "  8. 配置SSL证书 (Let's Encrypt)"
log_step "========================================"

read -p "是否配置SSL证书？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 检查certbot是否安装
    if ! command -v certbot &> /dev/null; then
        log_info "安装Certbot..."
        sudo apt install -y certbot python3-certbot-nginx
    fi
    
    # 申请证书
    log_info "申请SSL证书..."
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN
    
    if [ $? -eq 0 ]; then
        log_info "SSL证书申请成功 ✓"
        
        # 设置自动续期
        sudo systemctl enable certbot.timer
        sudo systemctl start certbot.timer
        log_info "自动续期已启用 ✓"
    else
        log_warn "SSL证书申请失败，请稍后重试或手动配置"
    fi
else
    log_warn "跳过SSL配置，请稍后手动配置HTTPS"
fi

# =============================================================================
# 9. 启动服务
# =============================================================================

log_step "========================================"
log_step "  9. 启动服务"
log_step "========================================"

# 启动Gunicorn
log_info "启动Gunicorn服务..."
sudo systemctl enable gunicorn-$APP_NAME
sudo systemctl start gunicorn-$APP_NAME

# 检查服务状态
sleep 2
if sudo systemctl is-active --quiet gunicorn-$APP_NAME; then
    log_info "Gunicorn服务运行中 ✓"
else
    log_error "Gunicorn服务启动失败"
    sudo systemctl status gunicorn-$APP_NAME
    exit 1
fi

# =============================================================================
# 10. 配置防火墙
# =============================================================================

log_step "========================================"
log_step "  10. 配置防火墙"
log_step "========================================"

if command -v ufw &> /dev/null; then
    log_info "配置UFW防火墙..."
    sudo ufw allow ssh
    sudo ufw allow http
    sudo ufw allow https
    sudo ufw --force enable
    log_info "防火墙配置完成 ✓"
elif command -v firewall-cmd &> /dev/null; then
    log_info "配置firewalld..."
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --reload
    log_info "防火墙配置完成 ✓"
fi

# =============================================================================
# 部署完成
# =============================================================================

log_step "========================================"
log_step ""
log_step "  🎉 部署完成！"
log_step ""
log_step "========================================"

echo ""
log_info "访问地址: http://$DOMAIN"
log_info "管理命令:"
echo "  - 查看服务状态: sudo systemctl status gunicorn-$APP_NAME"
echo "  - 查看日志: sudo journalctl -u gunicorn-$APP_NAME -f"
echo "  - 重启服务: sudo systemctl restart gunicorn-$APP_NAME"
echo "  - 停止服务: sudo systemctl stop gunicorn-$APP_NAME"
echo ""

log_warn "请记得:"
echo "  1. 编辑 $APP_DIR/.env 配置API密钥"
echo "  2. 配置支付接口（支付宝/微信）"
echo "  3. 配置域名DNS解析"
echo "  4. 测试所有功能"
echo ""

# 服务健康检查
log_info "进行健康检查..."
sleep 2
if curl -s http://127.0.0.1:$APP_PORT/health | grep -q "healthy"; then
    log_info "服务健康检查通过 ✓"
else
    log_warn "健康检查可能失败，请检查服务状态"
fi

echo ""
log_info "祝您使用愉快！🚀"
