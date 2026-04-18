#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外贸硅基军团 - 生产环境主应用
Flask + Gunicorn 部署
"""

import os
import sys
import logging
from datetime import datetime
from functools import wraps

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, g, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# Flask应用初始化
# ============================================

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data/subscribers.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    app.config['BASE_URL'] = os.getenv('BASE_URL', 'https://silicon-army.com')
    
    # CORS配置
    CORS(app, origins=os.getenv('CORS_ORIGINS', '*').split(','), supports_credentials=True)
    
    # 限流配置
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=os.getenv('REDIS_URL', 'memory://')
    )
    
    # 初始化数据库
    from models import db, init_db
    db.init_app(app)
    
    # 创建数据目录
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    with app.app_context():
        db.create_all()
        logger.info("✅ 数据库初始化完成")
    
    # 初始化支付
    from payment import PaymentFactory
    payment_config = {
        'ALIPAY_APP_ID': os.getenv('ALIPAY_APP_ID'),
        'ALIPAY_PRIVATE_KEY': os.getenv('ALIPAY_PRIVATE_KEY'),
        'ALIPAY_PUBLIC_KEY': os.getenv('ALIPAY_PUBLIC_KEY'),
        'ALIPAY_SANDBOX_MODE': os.getenv('ALIPAY_SANDBOX_MODE', 'true').lower() == 'true',
        'WECHAT_APP_ID': os.getenv('WECHAT_APP_ID'),
        'WECHAT_MCH_ID': os.getenv('WECHAT_MCH_ID'),
        'WECHAT_API_KEY': os.getenv('WECHAT_API_KEY'),
        'WECHAT_SANDBOX_MODE': os.getenv('WECHAT_SANDBOX_MODE', 'false').lower() == 'true',
    }
    payment = PaymentFactory(payment_config)
    
    # 注册路由
    register_routes(app, payment, limiter)
    
    return app


# ============================================
# 认证装饰器
# ============================================

def require_auth(f):
    """需要登录认证"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = request.headers.get('X-User-ID') or session.get('user_id')
        if not user_id:
            return jsonify({'error': '请先登录'}), 401
        
        from models import User
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def require_subscription(f):
    """需要有效订阅"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.current_user.is_subscribed:
            return jsonify({
                'error': '需要订阅才能使用此功能',
                'upgrade_url': '/pricing'
            }), 403
        return f(*args, **kwargs)
    return decorated


def check_quota(f):
    """检查额度"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = g.current_user
        if not user.can_use_chat():
            return jsonify({
                'error': '今日对话次数已用完',
                'upgrade_url': '/pricing',
                'reset_at': datetime.combine(
                    datetime.utcnow().date(), 
                    datetime.max.time()
                ).isoformat()
            }), 429
        return f(*args, **kwargs)
    return decorated


# ============================================
# API路由
# ============================================

def register_routes(app, payment, limiter):
    """注册所有路由"""
    
    # ---------- 首页 ----------
    @app.route('/')
    def index():
        return jsonify({
            'name': '外贸硅基军团',
            'version': '1.0.0',
            'status': 'running',
            'docs': '/api/docs'
        })
    
    # ---------- 健康检查 ----------
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # ---------- 认证相关 ----------
    
    @app.route('/api/auth/register', methods=['POST'])
    @limiter.limit("10 per hour")
    def register():
        """用户注册"""
        from models import db, User
        import uuid
        
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        phone = data.get('phone', '')
        referrer_id = data.get('referrer_id', '')
        
        # 验证
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        if len(password) < 6:
            return jsonify({'error': '密码至少6位'}), 400
        
        # 检查邮箱是否已注册
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '邮箱已被注册'}), 400
        
        # 创建用户
        user = User(
            user_id=str(uuid.uuid4()),
            email=email,
            phone=phone,
            package='free',
            referrer_id=referrer_id if referrer_id else None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"✅ 新用户注册: {email}")
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'token': user.user_id  # 简化处理，实际应使用JWT
        }), 201
    
    @app.route('/api/auth/login', methods=['POST'])
    @limiter.limit("20 per hour")
    def login():
        """用户登录"""
        from models import db, User
        
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': '邮箱或密码错误'}), 401
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'token': user.user_id
        })
    
    @app.route('/api/auth/me', methods=['GET'])
    @require_auth
    def get_current_user():
        """获取当前用户信息"""
        return jsonify({
            'user': g.current_user.to_dict()
        })
    
    # ---------- 套餐相关 ----------
    
    @app.route('/api/packages', methods=['GET'])
    def get_packages():
        """获取套餐列表"""
        from packages import get_all_packages, generate_features_comparison
        
        packages = get_all_packages()
        comparison = generate_features_comparison()
        
        return jsonify({
            'packages': packages,
            'comparison': comparison
        })
    
    @app.route('/api/packages/<package_id>', methods=['GET'])
    def get_package(package_id):
        """获取单个套餐详情"""
        from packages import get_package_price, PACKAGE_DURATIONS
        
        package_info = get_package_price(package_id)
        durations = PACKAGE_DURATIONS
        
        # 计算所有时长的价格
        prices = {}
        for duration_id, config in durations.items():
            prices[duration_id] = get_package_price(package_id, duration_id)
        
        return jsonify({
            'package': package_info,
            'prices': prices
        })
    
    # ---------- 支付相关 ----------
    
    # 注册支付路由（在payment.py中定义）
    from payment import register_payment_routes
    register_payment_routes(app, payment)
    
    # ---------- AI对话 ----------
    
    @app.route('/api/chat', methods=['POST'])
    @require_auth
    @check_quota
    @limiter.limit("60 per minute")
    def chat():
        """AI对话接口"""
        from models import db, ChatHistory
        
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        context = data.get('context', [])
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
        
        user = g.current_user
        
        # 保存用户消息
        user_msg = ChatHistory(
            session_id=session_id,
            user_id=user.user_id,
            role='user',
            content=message
        )
        db.session.add(user_msg)
        
        # 调用AI
        try:
            response = call_minimax_api(message, context, user)
        except Exception as e:
            logger.error(f"❌ AI调用失败: {e}")
            return jsonify({'error': 'AI服务暂时不可用'}), 503
        
        # 保存AI回复
        ai_msg = ChatHistory(
            session_id=session_id,
            user_id=user.user_id,
            role='assistant',
            content=response['content'],
            tokens_used=response.get('tokens', 0)
        )
        db.session.add(ai_msg)
        
        # 更新对话次数
        user.increment_chat_count()
        user.last_active = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': response['content'],
            'session_id': session_id,
            'usage': {
                'chat_count_today': user.chat_count_today,
                'chat_limit': user.chat_limit,
                'tokens_used': response.get('tokens', 0)
            }
        })
    
    @app.route('/api/chat/history', methods=['GET'])
    @require_auth
    def get_chat_history():
        """获取对话历史"""
        from models import ChatHistory
        
        user = g.current_user
        session_id = request.args.get('session_id', 'default')
        limit = request.args.get('limit', 50, type=int)
        
        messages = ChatHistory.query.filter_by(
            user_id=user.user_id,
            session_id=session_id
        ).order_by(ChatHistory.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'messages': [msg.to_dict() for msg in reversed(messages)]
        })
    
    @app.route('/api/chat/sessions', methods=['GET'])
    @require_auth
    def get_chat_sessions():
        """获取会话列表"""
        from models import ChatHistory
        from sqlalchemy import func
        
        user = g.current_user
        
        # 获取会话列表和最新消息
        sessions = db.session.query(
            ChatHistory.session_id,
            func.max(ChatHistory.created_at).label('last_message_time')
        ).filter(
            ChatHistory.user_id == user.user_id
        ).group_by(
            ChatHistory.session_id
        ).order_by(
            func.max(ChatHistory.created_at).desc()
        ).limit(20).all()
        
        return jsonify({
            'sessions': [
                {
                    'session_id': s.session_id,
                    'last_message_time': s.last_message_time.isoformat()
                }
                for s in sessions
            ]
        })
    
    # ---------- 客户发现 ----------
    
    @app.route('/api/discovery', methods=['POST'])
    @require_auth
    @require_subscription
    @limiter.limit("10 per hour")
    def discover_customers():
        """发现潜在客户"""
        from packages import check_feature_access
        
        user = g.current_user
        
        # 检查功能权限
        if not check_feature_access(user.package, 'customer_discovery_limit'):
            return jsonify({'error': '当前套餐不支持此功能'}), 403
        
        data = request.get_json()
        keywords = data.get('keywords', [])
        market = data.get('market', '')
        limit = data.get('limit', 20)
        
        # 根据套餐限制
        package_limit = user.chat_limit if hasattr(user, 'chat_limit') else 20
        if limit > package_limit:
            limit = package_limit
        
        # 调用客户发现Agent
        try:
            customers = discover_customers_agent(keywords, market, limit)
        except Exception as e:
            logger.error(f"❌ 客户发现失败: {e}")
            return jsonify({'error': '客户发现服务暂时不可用'}), 503
        
        return jsonify({
            'success': True,
            'customers': customers,
            'count': len(customers)
        })
    
    # ---------- 开发信 ----------
    
    @app.route('/api/email/generate', methods=['POST'])
    @require_auth
    @check_quota
    def generate_email():
        """生成开发信"""
        from packages import check_feature_access
        
        user = g.current_user
        
        data = request.get_json()
        customer_info = data.get('customer_info', {})
        template_style = data.get('style', 'professional')
        language = data.get('language', 'zh')
        
        # 调用AI生成
        try:
            email_content = generate_outreach_email(
                customer_info, 
                template_style, 
                language
            )
        except Exception as e:
            logger.error(f"❌ 开发信生成失败: {e}")
            return jsonify({'error': '服务暂时不可用'}), 503
        
        return jsonify({
            'success': True,
            'email': email_content
        })
    
    @app.route('/api/email/templates', methods=['GET'])
    @require_auth
    def get_email_templates():
        """获取开发信模板"""
        from packages import check_feature_access
        
        user = g.current_user
        
        # 内置模板
        templates = [
            {
                'id': 'intro',
                'name': '首次联系',
                'name_en': 'Introduction',
                'description': '适合首次开发潜在客户',
                'languages': ['zh', 'en']
            },
            {
                'id': 'follow_up',
                'name': '跟进邮件',
                'name_en': 'Follow Up',
                'description': '针对已有沟通的客户',
                'languages': ['zh', 'en']
            },
            {
                'id': 'product',
                'name': '产品介绍',
                'name_en': 'Product Introduction',
                'description': '介绍产品优势和特点',
                'languages': ['zh', 'en', 'es']
            }
        ]
        
        # 检查是否有自定义模板权限
        template_limit = check_feature_access(user.package, 'email_templates')
        
        return jsonify({
            'templates': templates,
            'custom_limit': user.chat_limit if template_limit else 0
        })
    
    # ---------- 询盘分析 ----------
    
    @app.route('/api/inquiry/analyze', methods=['POST'])
    @require_auth
    @require_subscription
    @check_quota
    def analyze_inquiry():
        """分析询盘"""
        from packages import check_feature_access
        
        data = request.get_json()
        inquiry_text = data.get('inquiry', '')
        
        if not inquiry_text:
            return jsonify({'error': '询盘内容不能为空'}), 400
        
        try:
            result = analyze_inquiry_agent(inquiry_text)
        except Exception as e:
            logger.error(f"❌ 询盘分析失败: {e}")
            return jsonify({'error': '分析服务暂时不可用'}), 503
        
        return jsonify({
            'success': True,
            'analysis': result
        })
    
    # ---------- 用户管理 ----------
    
    @app.route('/api/user/profile', methods=['GET'])
    @require_auth
    def get_profile():
        """获取用户资料"""
        return jsonify({
            'user': g.current_user.to_dict()
        })
    
    @app.route('/api/user/profile', methods=['PUT'])
    @require_auth
    def update_profile():
        """更新用户资料"""
        from models import db
        
        data = request.get_json()
        user = g.current_user
        
        if 'phone' in data:
            user.phone = data['phone']
        
        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'error': '密码至少6位'}), 400
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    
    @app.route('/api/user/usage', methods=['GET'])
    @require_auth
    def get_usage():
        """获取使用统计"""
        from models import ChatHistory
        from sqlalchemy import func
        
        user = g.current_user
        
        # 统计数据
        total_chats = ChatHistory.query.filter_by(
            user_id=user.user_id,
            role='user'
        ).count()
        
        total_tokens = db.session.query(
            func.sum(ChatHistory.tokens_used)
        ).filter_by(user_id=user.user_id).scalar() or 0
        
        return jsonify({
            'usage': {
                'chat_count_today': user.chat_count_today,
                'chat_limit': user.chat_limit,
                'chat_limit_period': 'daily',
                'total_chats': total_chats,
                'total_tokens': total_tokens,
                'subscription_end': user.subscription_end.isoformat() if user.subscription_end else None
            }
        })
    
    # ---------- 管理后台 ----------
    
    @app.route('/api/admin/users', methods=['GET'])
    @require_auth
    def admin_list_users():
        """管理员：用户列表"""
        from models import User
        
        # 简单权限检查（实际应使用角色权限）
        if not g.current_user.email.endswith('@silicon-army.com'):
            return jsonify({'error': '权限不足'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users = User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [u.to_dict() for u in users.items],
            'total': users.total,
            'page': page,
            'per_page': per_page,
            'pages': users.pages
        })
    
    @app.route('/api/admin/payments', methods=['GET'])
    @require_auth
    def admin_list_payments():
        """管理员：订单列表"""
        from models import Payment
        
        if not g.current_user.email.endswith('@silicon-army.com'):
            return jsonify({'error': '权限不足'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        query = Payment.query
        if status:
            query = query.filter_by(status=status)
        
        payments = query.order_by(Payment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'payments': [p.to_dict() for p in payments.items],
            'total': payments.total,
            'page': page,
            'per_page': per_page,
            'pages': payments.pages
        })
    
    # ---------- 错误处理 ----------
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': '资源不存在'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"服务器错误: {e}")
        return jsonify({'error': '服务器内部错误'}), 500
    
    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({
            'error': '请求过于频繁，请稍后再试',
            'retry_after': e.description
        }), 429


# ============================================
# AI Agent 函数
# ============================================

def call_minimax_api(message: str, context: list, user) -> dict:
    """
    调用MiniMax API
    
    Args:
        message: 用户消息
        context: 对话上下文
        user: 当前用户
    
    Returns:
        AI回复
    """
    import httpx
    
    api_key = os.getenv('MINIMAX_API_KEY')
    api_url = os.getenv('MINIMAX_API_URL', 'https://api.minimax.io/v1/chat/completions')
    
    if not api_key:
        raise Exception("MiniMax API未配置")
    
    # 构建消息
    messages = []
    
    # 系统提示词
    system_prompt = f"""你是外贸硅基军团的AI助手，专为外贸从业者提供智能服务。

当前用户信息：
- 套餐：{user.package}
- 角色：外贸{get_package_name(user.package)}

请根据用户需求提供专业的外贸咨询、客户开发、邮件撰写等服务。回答要专业、简洁、有价值。"""
    
    messages.append({"role": "system", "content": system_prompt})
    
    # 添加上下文
    for ctx in context[-5:]:  # 最近5轮对话
        messages.append({"role": ctx.get('role', 'user'), "content": ctx.get('content', '')})
    
    # 添加当前消息
    messages.append({"role": "user", "content": message})
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                api_url,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': os.getenv('MINIMAX_MODEL', 'abab6.5s-chat'),
                    'messages': messages,
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"API调用失败: {response.status_code}")
            
            result = response.json()
            
            return {
                'content': result['choices'][0]['message']['content'],
                'tokens': result.get('usage', {}).get('total_tokens', 0)
            }
            
    except httpx.TimeoutException:
        raise Exception("请求超时，请重试")
    except Exception as e:
        logger.error(f"MiniMax API错误: {e}")
        raise


def get_package_name(package_id: str) -> str:
    """获取套餐名称"""
    names = {
        'free': '新手用户',
        'starter': 'Starter用户',
        'pro': 'Pro用户',
        'growth': '企业用户'
    }
    return names.get(package_id, '用户')


def discover_customers_agent(keywords: list, market: str, limit: int) -> list:
    """
    客户发现Agent
    模拟实现（实际需对接海关数据等）
    """
    # 这里是模拟数据，实际需要对接真实数据源
    mock_customers = [
        {
            'company_name': f'Sample Company {i}',
            'contact': f'Manager {i}',
            'email': f'info@company{i}.com',
            'phone': f'+1-555-{i:04d}',
            'country': market or 'USA',
            'website': f'www.company{i}.com',
            'match_score': 85 - i * 2
        }
        for i in range(1, min(limit + 1, 11))
    ]
    
    return mock_customers


def generate_outreach_email(customer_info: dict, style: str, language: str) -> dict:
    """
    生成外贸开发信
    """
    return {
        'subject': f"{customer_info.get('company_name', '合作机会')} - {customer_info.get('product', '产品')}",
        'content': f"""
Dear {customer_info.get('contact', 'Sir/Madam')},

I hope this email finds you well.

I am writing from [Your Company Name], a professional manufacturer of {customer_info.get('product', 'related products')} in China.

{'-' * 40}

We noticed your company and believe we could provide you with high-quality products at competitive prices.

Our advantages:
• 10+ years of manufacturing experience
• ISO9001 certified factory
• OEM/ODM available
• Fast delivery and excellent service

{'-' * 40}

I would love to schedule a call to discuss how we can support your business.

Best regards,
[Your Name]
[Your Company]
[Contact Information]
""".strip(),
        'language': language,
        'style': style
    }


def analyze_inquiry_agent(inquiry_text: str) -> dict:
    """
    询盘分析Agent
    """
    # 简化的分析逻辑
    return {
        'intent': 'procurement',
        'urgency': 'medium',
        'budget_estimate': '5000-10000',
        'quantity': '500 units',
        'decision_maker': True,
        'quality_score': 75,
        'recommendations': [
            '及时回复，展示专业性',
            '提供详细产品报价单',
            '强调质量和认证',
            '提供样品方案'
        ],
        'key_points': [
            '客户有明确的采购意向',
            '数量较大，可能有议价空间',
            '建议发送公司介绍和产品目录'
        ]
    }


# ============================================
# 启动应用
# ============================================

app = create_app()

if __name__ == '__main__':
    # 开发环境
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # 生产环境由Gunicorn管理
    pass
