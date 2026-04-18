# 外贸硅基军团 - 生产环境部署

![版本](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

外贸硅基军团是一款面向外贸从业者的AI智能助手系统，提供客户发现、邮件触达、WhatsApp营销等全链路获客能力。

---

## 目录

- [功能特性](#功能特性)
- [技术架构](#技术架构)
- [快速部署](#快速部署)
- [配置说明](#配置说明)
- [API文档](#api文档)
- [套餐定价](#套餐定价)
- [常见问题](#常见问题)

---

## 功能特性

### 🤖 AI对话助手
- 基于MiniMax大模型的智能对话
- 支持外贸场景专业问答
- 多轮对话上下文理解

### 🔍 客户发现
- 多渠道客户信息聚合
- AI决策人识别
- 客户质量评分

### 📧 开发信生成
- AI智能撰写多语言邮件
- 多种专业模板
- 个性化内容生成

### 💬 WhatsApp触达
- 批量消息发送
- 多语言支持
- 送达状态追踪

### 📊 询盘分析
- AI自动解析询盘
- 客户意图识别
- 报价建议生成

### 💳 支付订阅
- 支付宝/微信支付
- 多种套餐选择
- 灵活的订阅周期

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      用户端                              │
│   Web App / Mobile / API                               │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                   Nginx反向代理                          │
│              (SSL / 负载均衡 / 静态资源)                  │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│              Gunicorn + Flask                          │
│         (Python Web Application)                       │
└──────┬───────────────────────────────────┬──────────────┘
       │                                   │
┌──────▼──────┐                   ┌────────▼────────┐
│  SQLite/    │                   │   MiniMax API   │
│  MySQL      │                   │   (AI服务)      │
└─────────────┘                   └─────────────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│              外部支付平台                               │
│         支付宝 / 微信支付                              │
└──────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | HTML5 + JavaScript | 响应式Web界面 |
| 后端 | Flask + Python | Web框架 |
| 数据库 | SQLite/MySQL | 数据存储 |
| 缓存 | Redis | 会话缓存 |
| WSGI | Gunicorn | Python应用服务器 |
| Web服务器 | Nginx | 反向代理+静态资源 |
| AI服务 | MiniMax API | 智能对话 |

---

## 快速部署

### 方式一：一键部署（推荐）

```bash
# 下载代码
git clone https://your-repo/silicon-army.git
cd silicon-army/production

# 运行部署脚本
chmod +x deploy.sh
sudo ./deploy.sh
```

### 方式二：手动部署

#### 1. 环境要求

- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Python 3.8+
- Nginx
- Git

#### 2. 安装依赖

```bash
# 安装系统依赖
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx git

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
cp .env.example .env
nano .env  # 编辑配置文件
```

#### 4. 初始化数据库

```bash
python3 -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
"
```

#### 5. 启动服务

```bash
# 启动Gunicorn
gunicorn -c gunicorn.conf.py app:app

# 或使用systemd服务
sudo cp gunicorn-silicon-army.service /etc/systemd/system/
sudo systemctl start gunicorn-silicon-army
sudo systemctl enable gunicorn-silicon-army
```

---

## 配置说明

### 环境变量配置

创建 `.env` 文件，复制 `.env.example` 的内容并修改：

```env
# MiniMax API配置（必须）
MINIMAX_API_KEY=your_api_key_here
MINIMAX_API_URL=https://api.minimax.io/v1/chat/completions

# 支付宝配置
ALIPAY_APP_ID=your_app_id
ALIPAY_PRIVATE_KEY=your_private_key
ALIPAY_PUBLIC_KEY=alipay_public_key
ALIPAY_SANDBOX_MODE=true  # 沙箱环境测试

# 微信支付配置
WECHAT_APP_ID=your_appid
WECHAT_MCH_ID=your_mch_id
WECHAT_API_KEY=your_api_key

# 数据库配置
DATABASE_URL=sqlite:///data/subscribers.db

# 安全配置
SECRET_KEY=your-secret-key-32-chars
```

### Nginx配置

```bash
# 复制Nginx配置
sudo cp nginx.conf /etc/nginx/sites-available/silicon-army
sudo ln -s /etc/nginx/sites-available/silicon-army /etc/nginx/sites-enabled/

# 测试并重载
sudo nginx -t
sudo systemctl reload nginx
```

### SSL证书

使用Let's Encrypt免费证书：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d silicon-army.com -d www.silicon-army.com
```

---

## API文档

### 认证接口

#### 注册
```http
POST /api/auth/register
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123",
    "phone": "+86 13800138000"
}
```

#### 登录
```http
POST /api/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123"
}
```

### 套餐接口

#### 获取套餐列表
```http
GET /api/packages
```

#### 购买套餐
```http
POST /api/payment/create
Content-Type: application/json

{
    "user_id": "user_xxx",
    "package": "pro",
    "payment_method": "alipay",
    "duration": "yearly"
}
```

### AI对话接口

#### 发送消息
```http
POST /api/chat
X-User-ID: user_xxx
Content-Type: application/json

{
    "message": "帮我找一些美国的LED灯具客户",
    "session_id": "session_xxx"
}
```

### 客户发现接口

#### 发现客户
```http
POST /api/discovery
X-User-ID: user_xxx
Content-Type: application/json

{
    "keywords": ["LED lighting", "LED panel"],
    "market": "USA",
    "limit": 20
}
```

### 开发信接口

#### 生成邮件
```http
POST /api/email/generate
X-User-ID: user_xxx
Content-Type: application/json

{
    "customer_info": {
        "company_name": "ABC Corp",
        "contact": "John Smith",
        "product": "LED Lights"
    },
    "style": "professional",
    "language": "en"
}
```

---

## 套餐定价

| 套餐 | 价格 | 每日对话 | 客户发现 | 邮件触达 | API接入 |
|------|------|----------|----------|----------|---------|
| 免费版 | ¥0 | 10次 | 5个/次 | - | - |
| Starter | ¥399/月 | 100次 | 20个/次 | 10封/天 | - |
| Pro | ¥1,999/月 | 500次 | 50个/次 | 50封/天 | - |
| Growth | ¥4,999/月 | ∞ | ∞ | ∞ | ✓ |

### 详细对比

详见 [packages.py](packages.py) 文件

---

## 常见问题

### Q: 如何申请MiniMax API Key？
A: 访问 https://platform.minimax.io 注册并创建应用

### Q: 支付回调失败怎么办？
A: 
1. 确认服务器80/443端口开放
2. 检查回调地址可公网访问
3. 查看日志排查问题

### Q: 如何升级到正式支付环境？
A: 
1. 完成支付宝/微信商户认证
2. 将 `.env` 中的 `ALIPAY_SANDBOX_MODE` 改为 `false`
3. 替换为正式环境的密钥

### Q: 数据库如何迁移到MySQL？
A: 
```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/silicon_army
```

---

## 目录结构

```
production/
├── app.py              # Flask应用主文件
├── models.py           # 数据库模型
├── payment.py          # 支付系统
├── packages.py         # 套餐配置
├── requirements.txt    # Python依赖
├── .env.example        # 环境变量示例
├── nginx.conf          # Nginx配置
├── gunicorn.conf.py   # Gunicorn配置
├── deploy.sh           # 部署脚本
└── README.md           # 本文件
```

---

## 运维命令

```bash
# 查看服务状态
sudo systemctl status gunicorn-silicon-army

# 查看日志
sudo journalctl -u gunicorn-silicon-army -f

# 重启服务
sudo systemctl restart gunicorn-silicon-army

# 更新代码后重载
sudo systemctl reload gunicorn-silicon-army
```

---

## 许可证

本项目采用 MIT 许可证

---

## 联系方式

- 邮箱：support@silicon-army.com
- 官网：https://silicon-army.com
- 文档：https://docs.silicon-army.com

---

**© 2024 外贸硅基军团 - 让外贸更简单**
