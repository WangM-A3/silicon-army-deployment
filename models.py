#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外贸硅基军团 - 数据库模型
支持用户管理、支付记录、对话历史
"""

import os
from datetime import datetime
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# 创建数据库实例
db = SQLAlchemy()


class User(db.Model):
    """
    用户表
    存储用户账户信息和订阅状态
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), unique=True, nullable=False, index=True, 
                        doc="用户唯一标识（UUID）")
    email = db.Column(db.String(255), unique=True, nullable=False, index=True,
                     doc="用户邮箱")
    phone = db.Column(db.String(32), unique=True, nullable=True, index=True,
                     doc="用户手机号")
    password_hash = db.Column(db.String(255), nullable=False,
                             doc="密码哈希值")
    
    # 订阅信息
    package = db.Column(db.String(32), default='free',
                       doc="当前套餐：free/starter/pro/growth")
    subscription_start = db.Column(db.DateTime, nullable=True,
                                   doc="订阅开始时间")
    subscription_end = db.Column(db.DateTime, nullable=True,
                                 doc="订阅到期时间")
    is_active = db.Column(db.Boolean, default=True,
                         doc="账户是否激活")
    
    # 额度管理
    chat_count_today = db.Column(db.Integer, default=0,
                                 doc="今日对话次数")
    chat_count_reset_date = db.Column(db.Date, default=datetime.utcnow().date,
                                     doc="对话次数重置日期")
    total_chat_count = db.Column(db.Integer, default=0,
                                doc="历史对话总次数")
    
    # API额度（用于Growth套餐API调用）
    api_calls_today = db.Column(db.Integer, default=0,
                                doc="今日API调用次数")
    api_calls_reset_date = db.Column(db.Date, default=datetime.utcnow().date,
                                     doc="API调用重置日期")
    
    # 账户信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow,
                          doc="创建时间")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                          onupdate=datetime.utcnow,
                          doc="最后更新时间")
    last_login = db.Column(db.DateTime, nullable=True,
                           doc="最后登录时间")
    last_active = db.Column(db.DateTime, nullable=True,
                           doc="最后活跃时间")
    
    # 推荐人
    referrer_id = db.Column(db.String(64), nullable=True,
                           doc="推荐人用户ID")

    # 关联关系
    payments = db.relationship('Payment', backref='user', lazy='dynamic',
                               cascade='all, delete-orphan')
    chat_histories = db.relationship('ChatHistory', backref='user', lazy='dynamic',
                                     cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """设置密码（自动哈希）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    @property
    def is_subscribed(self) -> bool:
        """检查用户是否有效订阅"""
        if not self.package or self.package == 'free':
            return False
        if self.subscription_end and self.subscription_end < datetime.utcnow():
            return False
        return self.is_active

    @property
    def chat_limit(self) -> int:
        """获取当前套餐的对话限制"""
        from packages import PACKAGES
        if self.package in PACKAGES:
            return PACKAGES[self.package].get('chat_limit', -1)
        return 10  # free用户每天10次

    def can_use_chat(self) -> bool:
        """检查是否可以发起对话"""
        # 检查是否订阅
        if not self.is_subscribed and self.chat_count_today >= 10:
            return False
        # 检查额度
        if self.chat_limit > 0 and self.chat_count_today >= self.chat_limit:
            return False
        return True

    def increment_chat_count(self) -> None:
        """增加对话次数（每日重置）"""
        today = datetime.utcnow().date()
        if self.chat_count_reset_date < today:
            self.chat_count_today = 0
            self.chat_count_reset_date = today
        self.chat_count_today += 1
        self.total_chat_count += 1

    def to_dict(self) -> dict:
        """转换为字典（脱敏）"""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'phone': self.phone,
            'package': self.package,
            'is_subscribed': self.is_subscribed,
            'subscription_end': self.subscription_end.isoformat() if self.subscription_end else None,
            'chat_count_today': self.chat_count_today,
            'chat_limit': self.chat_limit,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Payment(db.Model):
    """
    支付记录表
    存储所有支付订单信息
    """
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(64), unique=True, nullable=False, index=True,
                        doc="订单号（唯一）")
    trade_id = db.Column(db.String(128), nullable=True, index=True,
                        doc="支付平台交易号")
    
    # 用户信息
    user_id = db.Column(db.String(64), db.ForeignKey('users.user_id'), 
                        nullable=False, index=True,
                        doc="用户ID")
    
    # 订单信息
    package = db.Column(db.String(32), nullable=False,
                       doc="购买的套餐")
    amount = db.Column(db.Numeric(10, 2), nullable=False,
                      doc="支付金额（元）")
    currency = db.Column(db.String(8), default='CNY',
                       doc="货币类型")
    
    # 支付方式
    payment_method = db.Column(db.String(32), nullable=False,
                              doc="支付方式：alipay/wechat/card")
    
    # 状态
    STATUS_PENDING = 'pending'      # 待支付
    STATUS_PAID = 'paid'            # 已支付
    STATUS_REFUNDED = 'refunded'    # 已退款
    STATUS_EXPIRED = 'expired'      # 已过期
    STATUS_FAILED = 'failed'        # 支付失败
    
    status = db.Column(db.String(32), default=STATUS_PENDING, index=True,
                      doc="订单状态")
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True,
                          doc="创建时间")
    paid_at = db.Column(db.DateTime, nullable=True,
                       doc="支付时间")
    expired_at = db.Column(db.DateTime, nullable=True,
                          doc="过期时间")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow,
                          doc="更新时间")
    
    # 回调信息
    raw_response = db.Column(db.Text, nullable=True,
                            doc="支付平台原始回调数据（JSON）")
    
    # 退款信息
    refund_amount = db.Column(db.Numeric(10, 2), nullable=True,
                             doc="退款金额")
    refund_reason = db.Column(db.String(500), nullable=True,
                              doc="退款原因")

    @property
    def is_paid(self) -> bool:
        """是否已支付"""
        return self.status == self.STATUS_PAID

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        return self.expired_at and self.expired_at < datetime.utcnow()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'trade_id': self.trade_id,
            'user_id': self.user_id,
            'package': self.package,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }


class ChatHistory(db.Model):
    """
    对话历史表
    存储用户与AI的对话记录
    """
    __tablename__ = 'chat_histories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(64), nullable=False, index=True,
                          doc="会话ID")
    
    # 用户信息
    user_id = db.Column(db.String(64), db.ForeignKey('users.user_id'),
                       nullable=False, index=True,
                       doc="用户ID")
    
    # 对话内容
    role = db.Column(db.String(16), nullable=False,
                    doc="角色：user/assistant/system")
    content = db.Column(db.Text, nullable=False,
                       doc="消息内容")
    
    # 元数据
    message_type = db.Column(db.String(32), nullable=True,
                           doc="消息类型：text/image/tool_call等")
    tokens_used = db.Column(db.Integer, default=0,
                           doc="使用的Token数")
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True,
                          doc="创建时间")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'message_type': self.message_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SubscriptionLog(db.Model):
    """
    订阅变更日志表
    记录用户订阅状态的所有变更
    """
    __tablename__ = 'subscription_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), db.ForeignKey('users.user_id'),
                       nullable=False, index=True,
                       doc="用户ID")
    
    # 变更信息
    action = db.Column(db.String(32), nullable=False,
                      doc="操作类型：subscribe/upgrade/downgrade/cancel/expire/refund")
    from_package = db.Column(db.String(32), nullable=True,
                            doc="变更前套餐")
    to_package = db.Column(db.String(32), nullable=True,
                         doc="变更后套餐")
    
    # 关联订单
    order_id = db.Column(db.String(64), db.ForeignKey('payments.order_id'),
                        nullable=True,
                        doc="关联订单号")
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow,
                          doc="操作时间")
    
    # 备注
    note = db.Column(db.String(500), nullable=True,
                    doc="备注信息")


def init_db(app):
    """
    初始化数据库
    在Flask应用中使用
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("✅ 数据库表创建成功")


def backup_db(db_path: str, backup_path: str) -> bool:
    """
    备份数据库
    """
    import shutil
    try:
        shutil.copy2(db_path, backup_path)
        return True
    except Exception as e:
        print(f"❌ 数据库备份失败: {e}")
        return False
