#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外贸硅基军团 - 数据库初始化脚本
首次部署时运行此脚本
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Payment, ChatHistory, SubscriptionLog
from packages import PACKAGES


def init_database():
    """初始化数据库"""
    print("📦 开始初始化数据库...")
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✅ 数据表创建成功")
        
        # 创建管理员账户（如果不存在）
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@silicon-army.com')
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            import uuid
            admin = User(
                user_id=str(uuid.uuid4()),
                email=admin_email,
                phone='13800138000',
                package='growth',  # 管理员使用Growth版
                is_active=True
            )
            admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
            print(f"✅ 管理员账户创建成功")
            print(f"   邮箱: {admin_email}")
            print(f"   密码: {os.getenv('ADMIN_PASSWORD', 'admin123')} (请修改)")
        else:
            print("ℹ️ 管理员账户已存在")
        
        # 创建示例套餐测试订单（可选）
        test_order = Payment.query.filter_by(order_id='TEST_ORDER_001').first()
        if not test_order:
            print("ℹ️ 可运行 /api/payment/create 测试支付流程")
        
        print("\n" + "="*50)
        print("🎉 数据库初始化完成！")
        print("="*50)
        print("\n📋 接下来请：")
        print("  1. 修改 .env 中的配置")
        print("  2. 申请 MiniMax API Key")
        print("  3. 配置支付接口（支付宝/微信）")
        print("  4. 运行部署脚本或启动服务")
        print()


def reset_database():
    """重置数据库（危险操作）"""
    confirm = input("⚠️ 确定要重置数据库吗？所有数据将丢失！(yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 已取消")
        return
    
    with app.app_context():
        db.drop_all()
        print("✅ 所有表已删除")
        init_database()


def backup_database(db_path: str = None):
    """备份数据库"""
    if db_path is None:
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ 数据库已备份到: {backup_path}")


def show_stats():
    """显示数据库统计"""
    with app.app_context():
        print("\n📊 数据库统计")
        print("-" * 40)
        print(f"用户总数: {User.query.count()}")
        print(f"  - 活跃订阅: {User.query.filter(User.package != 'free').count()}")
        print(f"  - 免费用户: {User.query.filter_by(package='free').count()}")
        print(f"订单总数: {Payment.query.count()}")
        print(f"  - 已支付: {Payment.query.filter_by(status='paid').count()}")
        print(f"  - 待支付: {Payment.query.filter_by(status='pending').count()}")
        print(f"对话记录: {ChatHistory.query.count()}")
        print("-" * 40)


if __name__ == '__main__':
    from datetime import datetime
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'init':
            init_database()
        elif command == 'reset':
            reset_database()
        elif command == 'backup':
            backup_database()
        elif command == 'stats':
            show_stats()
        elif command == 'help':
            print("""
📖 数据库管理脚本

用法:
  python init_db.py [command]

命令:
  init    - 初始化数据库（创建表、管理员等）
  reset   - 重置数据库（危险！会删除所有数据）
  backup  - 备份数据库
  stats   - 显示数据库统计
  help    - 显示帮助信息
            """)
        else:
            print(f"❌ 未知命令: {command}")
            print("运行 'python init_db.py help' 查看帮助")
    else:
        # 默认初始化
        show_stats()
        init_database()
