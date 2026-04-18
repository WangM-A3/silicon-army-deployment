# ============================================
# 外贸硅基军团 - 套餐配置
# ============================================
"""
套餐定义和价格策略

定价逻辑：
- Starter版：满足个人SOHO或小团队日常使用，门槛低
- Pro版：适合成长中的外贸团队，功能完整
- Growth版：面向企业客户，按效果付费模式
"""

PACKAGES = {
    'free': {
        'id': 'free',
        'name': '免费版',
        'name_en': 'Free',
        'price': 0,
        'price_monthly': 0,
        'description': '体验基础功能，开启外贸之旅',
        'features': [
            '每日10次AI对话',
            '基础客户发现（每次5个）',
            '3套开发信模板',
            '单语言支持（中文）',
            '7天对话历史'
        ],
        'chat_limit': 10,              # 每日对话限制
        'chat_limit_period': 'daily',   # 限制周期
        'customer_discovery_limit': 5,  # 每次客户发现数量
        'email_templates': 3,           # 开发信模板数量
        'languages': ['zh'],           # 支持语言
        'history_days': 7,             # 对话历史保留天数
        'api_access': False,           # API接入
        'priority_support': False,     # 优先客服
        'whatsapp_reach': False,        # WhatsApp触达
        'email_reach': False,           # 邮件触达
        'inquiry_analysis': False,      # 询盘分析
        'recommended': False
    },
    
    'starter': {
        'id': 'starter',
        'name': 'Starter版',
        'name_en': 'Starter',
        'price': 399,
        'price_monthly': 39,
        'description': '个人SOHO首选，高性价比入门套餐',
        'features': [
            '每日100次AI对话',
            '标准客户发现（每次20个）',
            '10套开发信模板',
            '中英双语支持',
            '30天对话历史',
            '基础询盘分析',
            '邮件触达（每日10封）'
        ],
        'chat_limit': 100,
        'chat_limit_period': 'daily',
        'customer_discovery_limit': 20,
        'email_templates': 10,
        'languages': ['zh', 'en'],
        'history_days': 30,
        'api_access': False,
        'priority_support': False,
        'whatsapp_reach': False,
        'email_reach': True,
        'email_reach_limit': 10,       # 每日邮件限制
        'inquiry_analysis': True,
        'recommended': False
    },
    
    'pro': {
        'id': 'pro',
        'name': 'Pro版',
        'name_en': 'Professional',
        'price': 1999,
        'price_monthly': 199,
        'description': '外贸团队必备，功能完整强大',
        'features': [
            '每日500次AI对话',
            '深度客户发现（每次50个）',
            '无限开发信模板',
            '5种语言支持（中/英/西/法/德）',
            '90天对话历史',
            '高级询盘分析+客户评级',
            '邮件触达（每日50封）',
            'WhatsApp触达（每日10条）',
            '多Agent协作',
            '优先客服支持'
        ],
        'chat_limit': 500,
        'chat_limit_period': 'daily',
        'customer_discovery_limit': 50,
        'email_templates': -1,          # 无限
        'languages': ['zh', 'en', 'es', 'fr', 'de'],
        'history_days': 90,
        'api_access': False,
        'priority_support': False,
        'whatsapp_reach': True,
        'whatsapp_reach_limit': 10,
        'email_reach': True,
        'email_reach_limit': 50,
        'inquiry_analysis': True,
        'inquiry_analysis_advanced': True,
        'multi_agent': True,
        'recommended': True            # 推荐标记
    },
    
    'growth': {
        'id': 'growth',
        'name': 'Growth版',
        'name_en': 'Enterprise Growth',
        'price': 4999,
        'price_monthly': 499,
        'description': '企业级解决方案，无限可能',
        'features': [
            '无限AI对话',
            '无限客户发现',
            '无限开发信模板',
            '全语言支持（20+种语言）',
            '无限对话历史',
            'AI询盘分析+自动跟进',
            '无限邮件触达',
            '无限WhatsApp触达',
            'API接口接入',
            '专属客户成功经理',
            '定制化培训',
            '7x24小时技术支持',
            '私有化部署选项'
        ],
        'chat_limit': -1,              # 无限
        'chat_limit_period': 'daily',
        'customer_discovery_limit': -1,
        'email_templates': -1,
        'languages': ['zh', 'en', 'es', 'fr', 'de', 'pt', 'ru', 'ja', 'ko', 'ar', 'it', 'nl', 'pl', 'tr', 'vi', 'th', 'id', 'ms', 'hi', 'bn'],
        'history_days': -1,
        'api_access': True,
        'api_calls_limit': -1,
        'priority_support': True,
        'whatsapp_reach': True,
        'whatsapp_reach_limit': -1,
        'email_reach': True,
        'email_reach_limit': -1,
        'inquiry_analysis': True,
        'inquiry_analysis_advanced': True,
        'auto_follow_up': True,
        'multi_agent': True,
        'dedicated_manager': True,
        'custom_training': True,
        'sla_247': True,
        'private_deployment': True,
        'recommended': False
    }
}


# 套餐时长配置
PACKAGE_DURATIONS = {
    'monthly': {
        'name': '月付',
        'multiplier': 1,
        'discount': 0
    },
    'quarterly': {
        'name': '季付',
        'multiplier': 3,
        'discount': 0.05  # 95折
    },
    'yearly': {
        'name': '年付',
        'multiplier': 12,
        'discount': 0.17  # 83折（约8折）
    }
}


def get_package(package_id: str) -> dict:
    """获取套餐信息"""
    return PACKAGES.get(package_id, PACKAGES['free'])


def get_package_price(package_id: str, duration: str = 'monthly') -> dict:
    """
    计算套餐最终价格
    
    Args:
        package_id: 套餐ID
        duration: 时长（月付/季付/年付）
    
    Returns:
        包含原价、折扣、最终价格的字典
    """
    package = get_package(package_id)
    duration_config = PACKAGE_DURATIONS.get(duration, PACKAGE_DURATIONS['monthly'])
    
    base_price = package['price']
    months = duration_config['multiplier']
    discount = duration_config['discount']
    
    total_price = base_price * months * (1 - discount)
    
    return {
        'package_id': package_id,
        'package_name': package['name'],
        'duration': duration,
        'duration_name': duration_config['name'],
        'months': months,
        'base_price': base_price,
        'total_base': base_price * months,
        'discount': discount,
        'discount_amount': base_price * months * discount,
        'final_price': round(total_price, 2),
        'per_month': round(total_price / months, 2)
    }


def get_all_packages() -> list:
    """获取所有套餐列表（带价格信息）"""
    return [
        {**pkg, 'id': pkg_id}
        for pkg_id, pkg in PACKAGES.items()
    ]


def get_featured_packages() -> list:
    """获取推荐套餐列表"""
    return [
        {**pkg, 'id': pkg_id}
        for pkg_id, pkg in PACKAGES.items()
        if pkg.get('recommended')
    ]


def check_feature_access(package_id: str, feature: str) -> bool:
    """
    检查套餐是否支持某功能
    
    Args:
        package_id: 套餐ID
        feature: 功能名称（如 'api_access', 'whatsapp_reach'）
    
    Returns:
        是否支持
    """
    package = get_package(package_id)
    return package.get(feature, False)


def get_upgradable_packages(current_package: str) -> list:
    """获取可升级的套餐列表"""
    order = ['free', 'starter', 'pro', 'growth']
    try:
        current_index = order.index(current_package)
        return [
            {**PACKAGES[pkg_id], 'id': pkg_id}
            for pkg_id in order[current_index + 1:]
        ]
    except ValueError:
        return []


# 价格展示文案生成
def generate_price_display(package_id: str) -> str:
    """生成套餐价格展示文案"""
    package = get_package(package_id)
    if package['price'] == 0:
        return '免费'
    
    return f"¥{package['price']}/月"


def generate_features_comparison() -> dict:
    """生成功能对比表数据"""
    features = [
        {'key': 'chat_limit', 'name': '每日对话次数', 'format': 'num'},
        {'key': 'customer_discovery_limit', 'name': '每次客户发现', 'format': 'num'},
        {'key': 'email_templates', 'name': '开发信模板', 'format': 'unlimited'},
        {'key': 'languages', 'name': '支持语言', 'format': 'list'},
        {'key': 'history_days', 'name': '历史记录', 'format': 'days'},
        {'key': 'email_reach', 'name': '邮件触达', 'format': 'bool'},
        {'key': 'whatsapp_reach', 'name': 'WhatsApp触达', 'format': 'bool'},
        {'key': 'inquiry_analysis', 'name': '询盘分析', 'format': 'bool'},
        {'key': 'api_access', 'name': 'API接入', 'format': 'bool'},
        {'key': 'priority_support', 'name': '优先客服', 'format': 'bool'}
    ]
    
    comparison = {}
    for pkg_id, pkg in PACKAGES.items():
        comparison[pkg_id] = {}
        for feat in features:
            value = pkg.get(feat['key'])
            if feat['format'] == 'num':
                comparison[pkg_id][feat['key']] = value if value != -1 else '∞'
            elif feat['format'] == 'unlimited':
                comparison[pkg_id][feat['key']] = '无限' if value == -1 else str(value)
            elif feat['format'] == 'list':
                comparison[pkg_id][feat['key']] = f"{len(value)}种语言"
            elif feat['format'] == 'days':
                comparison[pkg_id][feat['key']] = f"{value}天" if value != -1 else '永久'
            elif feat['format'] == 'bool':
                comparison[pkg_id][feat['key']] = '✓' if value else '—'
    
    return {
        'features': features,
        'packages': comparison
    }
