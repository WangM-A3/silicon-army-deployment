# =============================================================================
# 外贸硅基军团 - Gunicorn配置文件
# =============================================================================
# Gunicorn是一个Python WSGI HTTP服务器
# 用于生产环境运行Flask应用
# =============================================================================

import multiprocessing
import os

# -----------------------------------------
# 基本配置
# -----------------------------------------

# 绑定地址和端口
bind = ['127.0.0.1:5000']

# 工作模式
worker_class = 'sync'  # 可选: sync, gevent, eventlet, tornado

# 工作进程数（推荐: CPU核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# 每个worker的线程数（仅sync模式）
threads = 2

# 进程名（用于ps/htop显示）
proc_name = 'silicon-army'

# PID文件
pidfile = '/var/run/gunicorn/silicon-army.pid'

# 守护进程模式（生产环境推荐关闭，由systemd管理）
daemon = False

# -----------------------------------------
# 超时配置
# -----------------------------------------

# 请求超时（秒）
timeout = 120

# Worker超时（秒）
graceful_timeout = 30

# keep-alive时间（秒）
keepalive = 5

# -----------------------------------------
# 日志配置
# -----------------------------------------

# 访问日志
accesslog = '/var/log/gunicorn/silicon-army_access.log'

# 错误日志
errorlog = '/var/log/gunicorn/silicon-army_error.log'

# 日志级别
loglevel = 'info'  # debug, info, warning, error, critical

# 日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 日志时间格式
access_log_format += ' - %(L)s'
access_log_format += ' [%(p)s]'

# -----------------------------------------
# 进程限制
# -----------------------------------------

# 最大请求数（达到后重启worker，防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50  # 随机抖动，避免所有worker同时重启

# Worker超时重启
worker_tmp_dir = '/dev/shm'

# -----------------------------------------
# 安全配置
# -----------------------------------------

# 切换到非root用户（需要手动创建用户）
# user = 'www-data'
# group = 'www-data'

# 限制工作目录
# chroot = '/var/www/silicon-army'

# 关闭核心转储
worker_tmp_dir = '/dev/shm'

# -----------------------------------------
# 钩子函数
# -----------------------------------------

def on_starting(server):
    """服务器启动前调用"""
    print("🚀 Gunicorn正在启动...")
    pass

def on_reload(server):
    """服务器重载前调用"""
    print("🔄 Gunicorn正在重载...")
    pass

def when_ready(server):
    """服务器准备就绪时调用"""
    print("✅ Gunicorn已启动，PID:", os.getpid())
    pass

def on_exit(server):
    """服务器退出时调用"""
    print("👋 Gunicorn正在关闭...")
    pass

def worker_int(worker):
    """Worker接收到SIGINT信号时调用"""
    print(f"⚠️ Worker {worker.pid} 收到中断信号")
    pass

def worker_abort(worker):
    """Worker接收到SIGABRT信号时调用"""
    print(f"⚠️ Worker {worker.pid} 异常终止")
    pass

def pre_fork(server, worker):
    """Fork worker前调用"""
    pass

def post_fork(server, worker):
    """Fork worker后调用"""
    print(f"✅ Worker {worker.pid} 已启动")
    pass

def pre_exec(server):
    """重新执行master进程前调用"""
    print("🔄 重新执行master进程...")
    pass

def pre_request(worker, req):
    """处理请求前调用"""
    worker.log.debug("%s %s" % (req.method, req.path))
    pass

def post_request(worker, req, environ, resp):
    """处理请求后调用"""
    pass

# -----------------------------------------
# SSL配置（如需要直接处理HTTPS）
# -----------------------------------------

# keyfile = '/path/to/key.pem'
# certfile = '/path/to/cert.pem'
# ssl_version = 'TLSv1_2'
# ciphers = 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256'

# -----------------------------------------
# 高级配置
# -----------------------------------------

# 开启钩子
hook_markers = ['starting', 'reloading', 'ready', 'exit', 'worker_int', 'worker_abort',
                'pre_fork', 'post_fork', 'pre_exec', 'pre_request', 'post_request']

# 分叉前保持监听（用于平滑重启）
# preload_app = True

# 禁用请求超时（仅在特定场景使用）
# graceful_timeout = 0
