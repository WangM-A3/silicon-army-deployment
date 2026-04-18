#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外贸硅基军团 - 支付系统
支持支付宝、微信支付
沙箱环境优先，正式环境替换配置即可
"""

import os
import json
import time
import uuid
import hmac
import hashlib
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import wraps

from flask import Flask, request, jsonify, current_app

# 配置日志
logger = logging.getLogger(__name__)


# ============================================
# 支付宝支付
# ============================================

class AlipayPayment:
    """
    支付宝支付处理器
    支持当面付、手机网站支付
    """
    
    def __init__(self, app_id: str, private_key: str, alipay_public_key: str, 
                 sandbox: bool = True):
        """
        初始化支付宝支付
        
        Args:
            app_id: 支付宝应用ID
            private_key: 应用私钥
            alipay_public_key: 支付宝公钥
            sandbox: 是否使用沙箱环境
        """
        self.app_id = app_id
        self.private_key = private_key
        self.alipay_public_key = alipay_public_key
        self.sandbox = sandbox
        
        # 根据环境选择网关
        if sandbox:
            self.gateway = "https://openapi.alipaydev.com/gateway.do"
        else:
            self.gateway = "https://openapi.alipay.com/gateway.do"
        
        # 初始化SDK（如果可用）
        self.sdk = None
        self._init_sdk()
    
    def _init_sdk(self):
        """初始化支付宝SDK"""
        try:
            from alipay import AliPay
            
            self.sdk = AliPay(
                appid=self.app_id,
                app_notify_url=None,  # 稍后设置
                app_private_key_string=self.private_key,
                alipay_public_key_string=self.alipay_public_key,
                sign_type="RSA2",
                debug=self.sandbox
            )
            logger.info("✅ 支付宝SDK初始化成功")
        except ImportError:
            logger.warning("⚠️ 未安装支付宝SDK，将使用HTTP请求模式")
        except Exception as e:
            logger.error(f"❌ 支付宝SDK初始化失败: {e}")
    
    def create_payment_url(self, order_id: str, amount: float, 
                          subject: str, notify_url: str, 
                          return_url: str) -> Dict[str, Any]:
        """
        创建支付链接
        
        Args:
            order_id: 订单号
            amount: 金额（元）
            subject: 商品名称
            notify_url: 异步通知地址
            return_url: 同步返回地址
        
        Returns:
            包含支付链接的字典
        """
        try:
            if self.sdk:
                # 使用SDK模式
                order_string = self.sdk.api_alipay_trade_wap_pay(
                    out_trade_no=order_id,
                    total_amount=str(amount),
                    subject=subject,
                    timeout_express="30m",
                    product_code="QUICK_WAP_WAY",
                    notify_url=notify_url,
                    return_url=return_url
                )
                payment_url = f"{self.gateway}?{order_string}"
            else:
                # HTTP请求模式（手动签名）
                payment_url = self._create_payment_url_manual(
                    order_id, amount, subject, notify_url, return_url
                )
            
            return {
                'success': True,
                'order_id': order_id,
                'payment_url': payment_url,
                'qr_code_url': None  # 可选：生成二维码URL
            }
            
        except Exception as e:
            logger.error(f"❌ 创建支付链接失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_payment_url_manual(self, order_id: str, amount: float,
                                   subject: str, notify_url: str,
                                   return_url: str) -> str:
        """
        手动创建支付链接（无SDK模式）
        """
        # 构建请求参数
        params = {
            'app_id': self.app_id,
            'method': 'alipay.trade.wap.pay',
            'charset': 'utf-8',
            'sign_type': 'RSA2',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0',
            'biz_content': json.dumps({
                'out_trade_no': order_id,
                'total_amount': str(amount),
                'subject': subject,
                'product_code': 'QUICK_WAP_WAY',
                'timeout_express': '30m'
            }),
            'notify_url': notify_url,
            'return_url': return_url
        }
        
        # 签名
        sign = self._sign_params(params)
        params['sign'] = sign
        
        # 构建URL
        query_string = '&'.join([f"{k}={self._url_encode(str(v))}" 
                                  for k, v in params.items()])
        return f"{self.gateway}?{query_string}"
    
    def _sign_params(self, params: dict) -> str:
        """签名参数"""
        # 排除sign和空值，按字典序排序
        sorted_params = sorted([
            (k, v) for k, v in params.items() 
            if k != 'sign' and v
        ])
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # 使用私钥签名
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes
        
        private_key = serialization.load_pem_private_key(
            self.private_key.encode(),
            password=None
        )
        
        signature = private_key.sign(
            sign_string.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return signature.hex()
    
    def _url_encode(self, text: str) -> str:
        """URL编码"""
        import urllib.parse
        return urllib.parse.quote_plus(text)
    
    def verify_notification(self, data: dict) -> Tuple[bool, str]:
        """
        验证支付回调通知
        
        Args:
            data: 回调数据
        
        Returns:
            (验证结果, 订单状态)
        """
        try:
            if self.sdk:
                # 使用SDK验证
                signature = data.get('sign')
                # 复制需要验证的数据
                verify_data = {k: v for k, v in data.items() if k != 'sign'}
                success = self.sdk.verify(verify_data, signature)
            else:
                # 手动验证
                success = self._verify_notification_manual(data)
            
            if success:
                trade_status = data.get('trade_status', '')
                if trade_status in ['TRADE_SUCCESS', 'TRADE_FINISHED']:
                    return True, 'paid'
                elif trade_status == 'WAIT_BUYER_PAY':
                    return True, 'pending'
                else:
                    return True, 'failed'
            
            return False, 'invalid'
            
        except Exception as e:
            logger.error(f"❌ 支付回调验证失败: {e}")
            return False, 'error'
    
    def _verify_notification_manual(self, data: dict) -> bool:
        """手动验证签名"""
        signature = data.pop('sign', None)
        if not signature:
            return False
        
        # 重新排序和编码
        sorted_params = sorted([
            (k, v) for k, v in data.items() if v
        ])
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # 使用支付宝公钥验证
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes
        
        public_key = serialization.load_pem_public_key(
            self.alipay_public_key.encode()
        )
        
        try:
            public_key.verify(
                bytes.fromhex(signature),
                sign_string.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False
    
    def query_order(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        try:
            if self.sdk:
                result = self.sdk.api_alipay_trade_query(out_trade_no=order_id)
                return {
                    'success': True,
                    'order_id': order_id,
                    'trade_status': result.get('trade_status'),
                    'amount': result.get('total_amount')
                }
            return {'success': False, 'error': 'SDK not initialized'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def refund(self, order_id: str, refund_amount: float, 
               refund_reason: str = '') -> Dict[str, Any]:
        """申请退款"""
        try:
            if self.sdk:
                result = self.sdk.api_alipay_trade_refund(
                    out_trade_no=order_id,
                    refund_amount=str(refund_amount),
                    refund_reason=refund_reason
                )
                return {
                    'success': result.get('code') == '10000',
                    'refund_id': result.get('trade_no'),
                    'refund_amount': result.get('refund_fee')
                }
            return {'success': False, 'error': 'SDK not initialized'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ============================================
# 微信支付
# ============================================

class WechatPayment:
    """
    微信支付处理器
    支持Native支付、JSAPI支付
    """
    
    def __init__(self, app_id: str, mch_id: str, api_key: str,
                 cert_path: str = None, key_path: str = None,
                 sandbox: bool = False):
        """
        初始化微信支付
        
        Args:
            app_id: 微信应用ID
            mch_id: 商户号
            api_key: API密钥
            cert_path: 证书路径（退款时需要）
            key_path: 密钥路径
            sandbox: 是否使用沙箱环境
        """
        self.app_id = app_id
        self.mch_id = mch_id
        self.api_key = api_key
        self.cert_path = cert_path
        self.key_path = key_path
        self.sandbox = sandbox
        
        # 网关地址
        if sandbox:
            self.gateway = "https://api.mch.weixin.qq.com/sandboxnew/pay/"
        else:
            self.gateway = "https://api.mch.weixin.qq.com/v3/pay/transactions/"
        
        # 初始化SDK（如果可用）
        self.sdk = None
        self._init_sdk()
    
    def _init_sdk(self):
        """初始化微信支付SDK"""
        try:
            from wechatpayv3 import WeChatPay, WeChatPayType
            
            self.sdk = WeChatPay(
                wechatpay_type=WeChatPayType.NATIVE,
                mchid=self.mch_id,
                cert_serial_no=None,
                mch_apiv3_key=self.api_key,
                appid=self.app_id,
                private_key=self._load_key_content(self.key_path) if self.key_path else None,
                cert_dir=self.cert_path,
                sandbox=self.sandbox
            )
            logger.info("✅ 微信支付SDK初始化成功")
        except ImportError:
            logger.warning("⚠️ 未安装微信支付SDK，将使用HTTP请求模式")
        except Exception as e:
            logger.error(f"❌ 微信支付SDK初始化失败: {e}")
    
    def _load_key_content(self, path: str) -> str:
        """加载密钥文件内容"""
        try:
            with open(path, 'r') as f:
                return f.read()
        except:
            return ""
    
    def create_payment(self, order_id: str, amount: float,
                      description: str, notify_url: str) -> Dict[str, Any]:
        """
        创建支付订单
        
        Args:
            order_id: 订单号
            amount: 金额（分）
            description: 商品描述
            notify_url: 回调通知地址
        
        Returns:
            包含支付二维码链接的字典
        """
        try:
            # 金额转换为分
            amount_fen = int(amount * 100)
            
            if self.sdk:
                # 使用SDK模式（Native支付）
                code, result = self.sdk.pay(
                    description=description,
                    out_trade_no=order_id,
                    amount={'total': amount_fen, 'currency': 'CNY'},
                    notify_url=notify_url
                )
                
                if code == 200:
                    return {
                        'success': True,
                        'order_id': order_id,
                        'code_url': result.get('code_url'),
                        'qr_code_url': self._generate_qr_code_url(result.get('code_url'))
                    }
                else:
                    return {'success': False, 'error': result}
            else:
                # HTTP请求模式
                return self._create_payment_manual(order_id, amount_fen, 
                                                   description, notify_url)
            
        except Exception as e:
            logger.error(f"❌ 创建微信支付订单失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_payment_manual(self, order_id: str, amount_fen: int,
                              description: str, notify_url: str) -> Dict[str, Any]:
        """手动创建支付订单"""
        import requests
        
        url = f"{self.gateway}native"
        
        # 生成随机字符串
        nonce_str = uuid.uuid4().hex
        
        # 构建请求体
        data = {
            'mchid': self.mch_id,
            'out_trade_no': order_id,
            'appid': self.app_id,
            'description': description,
            'notify_url': notify_url,
            'amount': {
                'total': amount_fen,
                'currency': 'CNY'
            },
            'nonce_str': nonce_str
        }
        
        # 签名
        sign = self._sign_wechat(data)
        data['sign'] = sign
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get('code_url'):
                return {
                    'success': True,
                    'order_id': order_id,
                    'code_url': result['code_url']
                }
            return {'success': False, 'error': result.get('message', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _sign_wechat(self, data: dict) -> str:
        """微信支付签名"""
        # 按字典序排序
        sorted_items = sorted([(k, v) for k, v in data.items() if k != 'sign'])
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted_items])
        sign_string += f"&key={self.api_key}"
        
        # MD5签名
        return hashlib.md5(sign_string.encode()).hexdigest().upper()
    
    def _generate_qr_code_url(self, code_url: str) -> str:
        """生成二维码URL（可用于展示）"""
        # 返回二维码图片API
        return f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={code_url}"
    
    def verify_notification(self, headers: dict, body: dict) -> Tuple[bool, str]:
        """
        验证微信支付回调
        
        Args:
            headers: 请求头（包含Wechatpay-Signature等）
            body: 请求体
        
        Returns:
            (验证结果, 订单状态)
        """
        try:
            if self.sdk:
                # SDK自动验证
                verified = self.sdk.verify(headers, body)
                if verified:
                    return True, body.get('trade_state', 'unknown')
                return False, 'invalid'
            else:
                # 手动验证
                return self._verify_notification_manual(headers, body)
                
        except Exception as e:
            logger.error(f"❌ 微信支付回调验证失败: {e}")
            return False, 'error'
    
    def _verify_notification_manual(self, headers: dict, body: dict) -> bool:
        """手动验证微信支付回调"""
        signature = headers.get('Wechatpay-Signature', '')
        timestamp = headers.get('Wechatpay-Timestamp', '')
        nonce = headers.get('Wechatpay-Nonce', '')
        
        # 构建签名串
        sign_string = f"{timestamp}\n{nonce}\n{json.dumps(body)}\n"
        
        # 使用API密钥验证
        import hmac
        expected_sign = hmac.new(
            self.api_key.encode(),
            sign_string.encode(),
            hashlib.sha256
        ).digest().hex()
        
        return signature == expected_sign
    
    def query_order(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        try:
            if self.sdk:
                code, result = self.sdk.query(out_trade_no=order_id)
                if code == 200:
                    return {
                        'success': True,
                        'order_id': order_id,
                        'trade_state': result.get('trade_state'),
                        'amount': result.get('amount', {}).get('total')
                    }
            return {'success': False, 'error': 'Query failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def refund(self, order_id: str, refund_amount: int,
               refund_reason: str = '') -> Dict[str, Any]:
        """申请退款"""
        try:
            if self.sdk:
                code, result = self.sdk.refund(
                    out_trade_no=order_id,
                    amount={'refund': refund_amount, 'total': refund_amount},
                    reason=refund_reason
                )
                return {
                    'success': code == 200,
                    'refund_id': result.get('refund_id') if code == 200 else None
                }
            return {'success': False, 'error': 'SDK not initialized'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ============================================
# 支付工厂
# ============================================

class PaymentFactory:
    """
    支付工厂类
    统一管理支付宝和微信支付
    """
    
    def __init__(self, config: dict):
        """
        初始化支付工厂
        
        Args:
            config: 配置字典
        """
        self.config = config
        
        # 初始化支付宝
        self.alipay = AlipayPayment(
            app_id=config.get('ALIPAY_APP_ID'),
            private_key=config.get('ALIPAY_PRIVATE_KEY'),
            alipay_public_key=config.get('ALIPAY_PUBLIC_KEY'),
            sandbox=config.get('ALIPAY_SANDBOX_MODE', True)
        )
        
        # 初始化微信支付
        self.wechat = WechatPayment(
            app_id=config.get('WECHAT_APP_ID'),
            mch_id=config.get('WECHAT_MCH_ID'),
            api_key=config.get('WECHAT_API_KEY'),
            cert_path=config.get('WECHAT_CERT_PATH'),
            key_path=config.get('WECHAT_KEY_PATH'),
            sandbox=config.get('WECHAT_SANDBOX_MODE', False)
        )
    
    def create_order(self, order_id: str, amount: float, 
                   package_name: str, payment_method: str,
                   notify_url: str, return_url: str) -> Dict[str, Any]:
        """
        创建支付订单
        
        Args:
            order_id: 订单号
            amount: 金额（元）
            package_name: 套餐名称
            payment_method: 支付方式（alipay/wechat）
            notify_url: 回调地址
            return_url: 返回地址
        
        Returns:
            支付链接信息
        """
        subject = f"外贸硅基军团-{package_name}"
        
        if payment_method == 'alipay':
            return self.alipay.create_payment_url(
                order_id=order_id,
                amount=amount,
                subject=subject,
                notify_url=notify_url,
                return_url=return_url
            )
        elif payment_method == 'wechat':
            return self.wechat.create_payment(
                order_id=order_id,
                amount=amount,
                description=subject,
                notify_url=notify_url
            )
        else:
            return {'success': False, 'error': f'Unknown payment method: {payment_method}'}
    
    def verify_notification(self, payment_method: str,
                          headers: dict, data: dict) -> Tuple[bool, str]:
        """
        验证支付回调
        
        Args:
            payment_method: 支付方式
            headers: 请求头
            data: 请求数据
        
        Returns:
            (验证结果, 订单状态)
        """
        if payment_method == 'alipay':
            return self.alipay.verify_notification(data)
        elif payment_method == 'wechat':
            return self.wechat.verify_notification(headers, data)
        else:
            return False, 'unknown'


# ============================================
# 支付路由
# ============================================

def register_payment_routes(app: Flask, payment: PaymentFactory):
    """
    注册支付相关路由
    
    Args:
        app: Flask应用
        payment: 支付工厂实例
    """
    
    @app.route('/api/payment/create', methods=['POST'])
    def create_payment():
        """创建支付订单"""
        from flask import request
        from models import db, Payment, User
        
        data = request.get_json()
        user_id = data.get('user_id')
        package_id = data.get('package')
        payment_method = data.get('payment_method', 'alipay')
        duration = data.get('duration', 'monthly')
        
        # 获取套餐信息
        from packages import get_package_price
        package_info = get_package_price(package_id, duration)
        
        # 生成订单号
        order_id = f"SA{int(time.time())}{uuid.uuid4().hex[:6].upper()}"
        
        # 创建支付记录
        payment_record = Payment(
            order_id=order_id,
            user_id=user_id,
            package=package_id,
            amount=package_info['final_price'],
            payment_method=payment_method,
            status=Payment.STATUS_PENDING,
            expired_at=datetime.utcnow() + timedelta(hours=2)
        )
        db.session.add(payment_record)
        db.session.commit()
        
        # 生成支付链接
        notify_url = f"{app.config['BASE_URL']}/api/payment/{payment_method}/notify"
        return_url = f"{app.config['BASE_URL']}/payment/success?order_id={order_id}"
        
        result = payment.create_order(
            order_id=order_id,
            amount=float(package_info['final_price']),
            package_name=package_info['package_name'],
            payment_method=payment_method,
            notify_url=notify_url,
            return_url=return_url
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'order_id': order_id,
                'payment_url': result.get('payment_url'),
                'qr_code_url': result.get('qr_code_url'),
                'amount': package_info['final_price'],
                'expired_at': payment_record.expired_at.isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '创建支付订单失败')
            }), 400
    
    @app.route('/api/payment/alipay/notify', methods=['POST'])
    def alipay_notify():
        """支付宝异步回调"""
        from models import db, Payment, User, SubscriptionLog
        from packages import get_package
        
        data = request.form.to_dict() if request.form else request.get_json() or {}
        
        # 验证签名
        verified, status = payment.verify_notification('alipay', {}, data)
        
        if not verified:
            logger.warning(f"支付宝回调验证失败: {data}")
            return 'fail'
        
        order_id = data.get('out_trade_no')
        
        # 更新订单状态
        payment_record = Payment.query.filter_by(order_id=order_id).first()
        if payment_record and payment_record.status == Payment.STATUS_PENDING:
            payment_record.status = Payment.STATUS_PAID
            payment_record.paid_at = datetime.utcnow()
            payment_record.trade_id = data.get('trade_no')
            payment_record.raw_response = json.dumps(data)
            
            # 更新用户订阅
            user = User.query.filter_by(user_id=payment_record.user_id).first()
            if user:
                package_info = get_package(payment_record.package)
                duration = request.form.get('duration', 'monthly')
                months = {'monthly': 1, 'quarterly': 3, 'yearly': 12}.get(duration, 1)
                
                # 计算订阅到期时间
                if user.subscription_end and user.subscription_end > datetime.utcnow():
                    user.subscription_end += timedelta(days=30 * months)
                else:
                    user.subscription_end = datetime.utcnow() + timedelta(days=30 * months)
                
                user.package = payment_record.package
                
                # 记录订阅日志
                log = SubscriptionLog(
                    user_id=user.user_id,
                    action='subscribe',
                    from_package=user.package,
                    to_package=payment_record.package,
                    order_id=order_id
                )
                db.session.add(log)
            
            db.session.commit()
            logger.info(f"✅ 支付宝支付成功: {order_id}")
            return 'success'
        
        return 'success'
    
    @app.route('/api/payment/wechat/notify', methods=['POST'])
    def wechat_notify():
        """微信支付异步回调"""
        from models import db, Payment, User, SubscriptionLog
        from packages import get_package
        
        headers = {
            'Wechatpay-Signature': request.headers.get('Wechatpay-Signature', ''),
            'Wechatpay-Timestamp': request.headers.get('Wechatpay-Timestamp', ''),
            'Wechatpay-Nonce': request.headers.get('Wechatpay-Nonce', '')
        }
        body = request.get_json() or {}
        
        # 验证签名
        verified, status = payment.verify_notification('wechat', headers, body)
        
        if not verified:
            logger.warning(f"微信支付回调验证失败")
            return jsonify({'code': 'FAIL', 'message': '签名验证失败'}), 400
        
        # 解密回调数据（V3版本需要解密）
        if 'resource' in body:
            # V3版本
            order_id = body['resource'].get('out_trade_no')
            trade_status = body['resource'].get('trade_state')
        else:
            order_id = body.get('out_trade_no')
            trade_status = body.get('trade_status')
        
        # 更新订单状态
        payment_record = Payment.query.filter_by(order_id=order_id).first()
        if payment_record and payment_record.status == Payment.STATUS_PENDING:
            if trade_status == 'SUCCESS':
                payment_record.status = Payment.STATUS_PAID
                payment_record.paid_at = datetime.utcnow()
                payment_record.trade_id = body.get('transaction_id')
                payment_record.raw_response = json.dumps(body)
                
                # 更新用户订阅
                user = User.query.filter_by(user_id=payment_record.user_id).first()
                if user:
                    package_info = get_package(payment_record.package)
                    
                    if user.subscription_end and user.subscription_end > datetime.utcnow():
                        user.subscription_end += timedelta(days=30)
                    else:
                        user.subscription_end = datetime.utcnow() + timedelta(days=30)
                    
                    user.package = payment_record.package
                
                db.session.commit()
                logger.info(f"✅ 微信支付成功: {order_id}")
        
        return jsonify({'code': 'SUCCESS', 'message': '成功'})
    
    @app.route('/api/payment/query/<order_id>', methods=['GET'])
    def query_payment(order_id):
        """查询订单状态"""
        from models import Payment
        payment_record = Payment.query.filter_by(order_id=order_id).first()
        
        if payment_record:
            return jsonify(payment_record.to_dict())
        return jsonify({'error': 'Order not found'}), 404
    
    @app.route('/api/payment/refund', methods=['POST'])
    def refund_payment():
        """申请退款（管理员接口）"""
        from flask import request
        from models import db, Payment, User, SubscriptionLog
        
        data = request.get_json()
        order_id = data.get('order_id')
        refund_reason = data.get('reason', '')
        
        payment_record = Payment.query.filter_by(order_id=order_id).first()
        if not payment_record or not payment_record.is_paid:
            return jsonify({'success': False, 'error': 'Invalid order'}), 400
        
        # 调用支付平台退款
        if payment_record.payment_method == 'alipay':
            result = payment.alipay.refund(
                order_id, 
                float(payment_record.amount),
                refund_reason
            )
        else:
            result = payment.wechat.refund(
                order_id,
                int(float(payment_record.amount) * 100),
                refund_reason
            )
        
        if result['success']:
            payment_record.status = Payment.STATUS_REFUNDED
            payment_record.refund_amount = payment_record.amount
            payment_record.refund_reason = refund_reason
            
            # 回滚用户订阅
            user = User.query.filter_by(user_id=payment_record.user_id).first()
            if user:
                user.package = 'free'
                user.subscription_end = None
                
                log = SubscriptionLog(
                    user_id=user.user_id,
                    action='refund',
                    to_package='free',
                    order_id=order_id,
                    note=refund_reason
                )
                db.session.add(log)
            
            db.session.commit()
        
        return jsonify(result)
    
    @app.route('/payment/success')
    def payment_success():
        """支付成功页面"""
        from models import Payment
        order_id = request.args.get('order_id')
        
        payment_record = Payment.query.filter_by(order_id=order_id).first()
        if payment_record and payment_record.is_paid:
            return jsonify({
                'success': True,
                'message': '支付成功',
                'order_id': order_id,
                'package': payment_record.package
            })
        
        return jsonify({
            'success': False,
            'message': '订单未找到或支付失败'
        }), 404
