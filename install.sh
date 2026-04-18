#!/bin/bash
# 外贸硅基军团一键安装脚本
# 服务器IP: 8.161.224.177

set -e

echo "🚀 开始安装外贸硅基军团..."
echo "================================"

# 1. 检查系统
if [ ! -f /etc/os-release ]; then
    echo "❌ 无法识别操作系统"
    exit 1
fi

# 2. 更新系统
echo "📦 更新系统包..."
apt update && apt upgrade -y

# 3. 安装依赖
echo "📦 安装必要依赖..."
apt install -y python3 python3-pip nginx git certbot python3-certbot-nginx

# 4. 克隆代码
echo "📥 克隆代码..."
cd /root
if [ -d "silicon-army" ]; then
    echo "⚠️  silicon-army目录已存在，跳过克隆"
else
    git clone https://github.com/WangM-A3/silicon-army-deployment.git silicon-army
fi

# 5. 进入项目目录
cd /root/silicon-army

# 6. 安装Python依赖
echo "📦 安装Python依赖..."
pip3 install -r requirements.txt

# 7. 配置环境变量
echo "⚙️  配置环境变量..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  重要：请编辑 .env 文件，填入你的MiniMax API Key"
    echo "命令：nano /root/silicon-army/.env"
    echo ""
fi

# 8. 初始化数据库
echo "📊 初始化数据库..."
python3 init_db.py

# 9. 配置Nginx
echo "🌐 配置Nginx..."
cp nginx.conf /etc/nginx/sites-available/silicon-army
ln -sf /etc/nginx/sites-available/silicon-army /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# 10. 配置Systemd服务
echo "🔧 配置系统服务..."
cp gunicorn-silicon-army.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable gunicorn-silicon-army
systemctl start gunicorn-silicon-army

# 11. 检查服务状态
echo ""
echo "✅ 安装完成！"
echo "================================"
echo ""
echo "📋 后续步骤："
echo ""
echo "1️⃣  编辑配置文件，填入API Key："
echo "   nano /root/silicon-army/.env"
echo ""
echo "2️⃣  重启服务："
echo "   systemctl restart gunicorn-silicon-army"
echo ""
echo "3️⃣  访问网站："
echo "   http://8.161.224.177"
echo ""
echo "4️⃣  配置域名（可选）："
echo "   - 在阿里云域名控制台添加A记录"
echo "   - 主机记录：@，记录值：8.161.224.177"
echo "   - 主机记录：www，记录值：8.161.224.177"
echo ""
echo "5️⃣  配置SSL证书（可选）："
echo "   certbot --nginx -d silicon-army.com -d www.silicon-army.com"
echo ""
echo "📊 查看日志："
echo "   tail -f /var/log/gunicorn/silicon-army.log"
echo ""
echo "🎉 恭喜！外贸硅基军团已就绪！"
