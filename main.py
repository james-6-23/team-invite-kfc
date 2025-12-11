from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_session import Session
import requests
import os
import re
import secrets
import time
import json
import redis
import atexit
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")

# Session 配置 - 使用 Redis 存储
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_KEY_PREFIX'] = 'team_invite:session:'
app.config['SESSION_USE_SIGNER'] = True

# ==================== 日志配置 ====================
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# 自定义日志格式
log_formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 配置应用日志
app.logger.setLevel(logging.INFO)
for handler in app.logger.handlers:
    handler.setFormatter(log_formatter)

# 如果没有 handler，添加一个
if not app.logger.handlers:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    app.logger.addHandler(stream_handler)


class No404Filter(logging.Filter):
    def filter(self, record):
        return not (getattr(record, "status_code", None) == 404)


logging.getLogger("werkzeug").addFilter(No404Filter())


def log_info(module: str, action: str, message: str = "", **kwargs):
    """统一 INFO 日志格式"""
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    log_msg = f"[{module}] {action}"
    if message:
        log_msg += f" - {message}"
    if extra:
        log_msg += f" | {extra}"
    app.logger.info(log_msg)


def log_error(module: str, action: str, message: str = "", **kwargs):
    """统一 ERROR 日志格式"""
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    log_msg = f"[{module}] {action}"
    if message:
        log_msg += f" - {message}"
    if extra:
        log_msg += f" | {extra}"
    app.logger.error(log_msg)


def log_warn(module: str, action: str, message: str = "", **kwargs):
    """统一 WARNING 日志格式"""
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    log_msg = f"[{module}] {action}"
    if message:
        log_msg += f" - {message}"
    if extra:
        log_msg += f" | {extra}"
    app.logger.warning(log_msg)

# ChatGPT Team 配置
_token = os.getenv("AUTHORIZATION_TOKEN", "")
AUTHORIZATION_TOKEN = _token if _token.startswith("Bearer ") else f"Bearer {_token}"
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

# Cloudflare Turnstile (保留兼容)
CF_TURNSTILE_SECRET_KEY = os.getenv("CF_TURNSTILE_SECRET_KEY")
CF_TURNSTILE_SITE_KEY = os.getenv("CF_TURNSTILE_SITE_KEY")

# Linux DO OAuth 配置
LINUXDO_CLIENT_ID = os.getenv("LINUXDO_CLIENT_ID")
LINUXDO_CLIENT_SECRET = os.getenv("LINUXDO_CLIENT_SECRET")
LINUXDO_REDIRECT_URI = os.getenv("LINUXDO_REDIRECT_URI", "http://127.0.0.1:39001/callback")
LINUXDO_AUTHORIZE_URL = "https://connect.linux.do/oauth2/authorize"
LINUXDO_TOKEN_URL = "https://connect.linux.do/oauth2/token"
LINUXDO_USER_URL = "https://connect.linux.do/api/user"

# 邮箱平台配置
EMAIL_API_AUTH = os.getenv("EMAIL_API_AUTH")
EMAIL_API_BASE = os.getenv("EMAIL_API_BASE", "https://kyx-cloud-email.kkyyxx.top/api/public")
EMAIL_DOMAIN = os.getenv("EMAIL_DOMAIN", "kyx03.de")
EMAIL_ROLE = os.getenv("EMAIL_ROLE", "gpt-team")

# 信任等级要求
MIN_TRUST_LEVEL = int(os.getenv("MIN_TRUST_LEVEL", "1"))

# 缓存配置
STATS_CACHE_TTL = 120  # 统计数据缓存时间（秒）
STATS_REFRESH_INTERVAL = 60  # 后台刷新间隔（秒）

# Redis 配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Redis 连接池
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD or None,
    db=REDIS_DB,
    decode_responses=True,
    max_connections=10,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)
redis_client = redis.Redis(connection_pool=redis_pool)

# Session 使用 Redis 存储（需要单独的连接，不使用 decode_responses）
session_redis = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD or None,
    db=REDIS_DB
)
app.config['SESSION_REDIS'] = session_redis
Session(app)

# Redis Key
INVITE_RECORDS_KEY = "team_invite:records"
INVITE_COUNTER_KEY = "team_invite:counter"
INVITE_LOCK_KEY = "team_invite:lock"
STATS_CACHE_KEY = "team_invite:stats_cache"
PENDING_INVITES_CACHE_KEY = "team_invite:pending_invites"

# 后台管理密码
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 统一密码
DEFAULT_PASSWORD = "kfcvivo50"


def get_client_ip_address():
    if "CF-Connecting-IP" in request.headers:
        return request.headers["CF-Connecting-IP"]
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr or "unknown"


def build_base_headers():
    return {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "authorization": AUTHORIZATION_TOKEN,
        "chatgpt-account-id": ACCOUNT_ID,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }


def build_invite_headers():
    headers = build_base_headers()
    headers.update(
        {
            "content-type": "application/json",
            "origin": "https://chatgpt.com",
            "referer": "https://chatgpt.com/",
            'sec-ch-ua': '"Chromium";v="135", "Not)A;Brand";v="99", "Google Chrome";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }
    )
    return headers


def parse_emails(raw_emails):
    if not raw_emails:
        return [], []
    parts = raw_emails.replace("\n", ",").split(",")
    emails = [p.strip() for p in parts if p.strip()]
    valid = [e for e in emails if e.count("@") == 1]
    return emails, valid


def validate_turnstile(turnstile_response):
    if not turnstile_response:
        return False
    data = {
        "secret": CF_TURNSTILE_SECRET_KEY,
        "response": turnstile_response,
        "remoteip": get_client_ip_address(),
    }
    try:
        response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=data,
            timeout=10,
        )
        result = response.json()
        return result.get("success", False)
    except Exception:
        return False


class TeamBannedException(Exception):
    """Team 账号被封禁异常"""
    pass


def get_cached_stats():
    """从 Redis 获取缓存的统计数据"""
    try:
        cached = redis_client.get(STATS_CACHE_KEY)
        if cached:
            return json.loads(cached)
    except Exception as e:
        log_error("Cache", "读取统计缓存失败", str(e))
    return None


def set_cached_stats(stats_data):
    """将统计数据存入 Redis 缓存"""
    try:
        cache_obj = {
            "data": stats_data,
            "timestamp": time.time(),
            "updated_at": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
        }
        redis_client.setex(STATS_CACHE_KEY, STATS_CACHE_TTL, json.dumps(cache_obj))
    except Exception as e:
        log_error("Cache", "写入统计缓存失败", str(e))


def get_cached_pending_invites():
    """从 Redis 获取缓存的待处理邀请"""
    try:
        cached = redis_client.get(PENDING_INVITES_CACHE_KEY)
        if cached:
            return json.loads(cached)
    except Exception as e:
        log_error("Cache", "读取待处理邀请缓存失败", str(e))
    return None


def set_cached_pending_invites(items, total):
    """将待处理邀请存入 Redis 缓存"""
    try:
        cache_obj = {
            "items": items,
            "total": total,
            "timestamp": time.time()
        }
        redis_client.setex(PENDING_INVITES_CACHE_KEY, STATS_CACHE_TTL, json.dumps(cache_obj))
    except Exception as e:
        log_error("Cache", "写入待处理邀请缓存失败", str(e))


def fetch_stats_from_api():
    """从 API 获取最新统计数据（内部使用）"""
    base_headers = build_base_headers()
    subs_url = f"https://chatgpt.com/backend-api/subscriptions?account_id={ACCOUNT_ID}"
    invites_url = f"https://chatgpt.com/backend-api/accounts/{ACCOUNT_ID}/invites?offset=0&limit=1&query="

    subs_resp = requests.get(subs_url, headers=base_headers, timeout=10)

    # 检查是否被封禁 (401/403 表示账号异常)
    if subs_resp.status_code in [401, 403]:
        log_error("Stats", "账号异常", "Team account banned or unauthorized", status=subs_resp.status_code)
        raise TeamBannedException("Team 账号状态异常")
    subs_resp.raise_for_status()
    subs_data = subs_resp.json()

    invites_resp = requests.get(invites_url, headers=base_headers, timeout=10)
    if invites_resp.status_code in [401, 403]:
        log_error("Stats", "账号异常", "Team account banned or unauthorized", status=invites_resp.status_code)
        raise TeamBannedException("Team 账号状态异常")
    invites_resp.raise_for_status()
    invites_data = invites_resp.json()

    return {
        "seats_in_use": subs_data.get("seats_in_use"),
        "seats_entitled": subs_data.get("seats_entitled"),
        "pending_invites": invites_data.get("total"),
        "plan_type": subs_data.get("plan_type"),
        "active_start": subs_data.get("active_start"),
        "active_until": subs_data.get("active_until"),
        "billing_period": subs_data.get("billing_period"),
        "billing_currency": subs_data.get("billing_currency"),
        "will_renew": subs_data.get("will_renew"),
        "is_delinquent": subs_data.get("is_delinquent"),
    }


def refresh_stats(force=False):
    """获取统计数据（优先从缓存读取）"""
    if not force:
        cached = get_cached_stats()
        if cached:
            return cached["data"], cached.get("updated_at")

    # 缓存不存在或强制刷新，从 API 获取
    stats = fetch_stats_from_api()
    set_cached_stats(stats)
    updated_at = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    log_info("Stats", "统计数据已刷新", seats_in_use=stats.get("seats_in_use"), pending=stats.get("pending_invites"))
    return stats, updated_at


def background_refresh_stats():
    """后台刷新统计数据（由定时任务调用）"""
    try:
        stats = fetch_stats_from_api()
        set_cached_stats(stats)
        log_info("Background", "统计数据刷新完成", seats=stats.get("seats_in_use"), pending=stats.get("pending_invites"))
    except TeamBannedException:
        log_error("Background", "统计刷新失败", "账号被封禁")
    except Exception as e:
        log_error("Background", "统计刷新失败", str(e))


# ==================== Linux DO OAuth 相关函数 ====================

def generate_email_for_user(username):
    """根据用户信息生成邮箱地址: {username}kfc@domain"""
    safe_username = re.sub(r'[^a-zA-Z0-9]', '', username.lower())[:20]
    return f"{safe_username}kfc@{EMAIL_DOMAIN}"


def generate_password():
    """返回统一密码"""
    return DEFAULT_PASSWORD


def create_email_user(email, password, role_name):
    """在邮箱平台创建用户"""
    url = f"{EMAIL_API_BASE}/addUser"
    headers = {
        "Authorization": EMAIL_API_AUTH,
        "Content-Type": "application/json"
    }
    payload = {
        "list": [{"email": email, "password": password, "roleName": role_name}]
    }
    try:
        log_info("Email", "创建邮箱", email=email, role=role_name)
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()
        success = data.get("code") == 200
        msg = data.get("message", "Unknown error")
        if success:
            log_info("Email", "创建成功", email=email)
        else:
            log_warn("Email", "创建失败", msg, email=email, code=data.get("code"))
        return success, msg
    except Exception as e:
        log_error("Email", "创建异常", str(e), email=email)
        return False, str(e)


def fetch_pending_invites_from_api(limit=100):
    """从 API 获取待处理邀请列表（内部使用）"""
    url = f"https://chatgpt.com/backend-api/accounts/{ACCOUNT_ID}/invites?offset=0&limit={limit}&query="
    headers = build_base_headers()

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("items", []), data.get("total", 0)
        else:
            log_error("Invite", "获取待处理邀请失败", status=response.status_code)
            return [], 0
    except Exception as e:
        log_error("Invite", "获取待处理邀请异常", str(e))
        return [], 0


def get_pending_invites(force=False):
    """获取待处理邀请列表（优先从缓存读取）"""
    if not force:
        cached = get_cached_pending_invites()
        if cached:
            return cached["items"], cached["total"]

    # 缓存不存在或强制刷新
    items, total = fetch_pending_invites_from_api(100)
    set_cached_pending_invites(items, total)
    return items, total


def check_invite_pending(email):
    """检查邮箱是否在待处理邀请列表中（实时查询，不使用缓存）"""
    items, _ = fetch_pending_invites_from_api(100)
    for item in items:
        if item.get("email_address", "").lower() == email.lower():
            return True
    return False


def background_refresh_pending_invites():
    """后台刷新待处理邀请（由定时任务调用）"""
    try:
        items, total = fetch_pending_invites_from_api(100)
        set_cached_pending_invites(items, total)
        log_info("Background", "待处理邀请刷新完成", total=total)
    except Exception as e:
        log_error("Background", "待处理邀请刷新失败", str(e))


def send_chatgpt_invite(email):
    """发送 ChatGPT Team 邀请"""
    url = f"https://chatgpt.com/backend-api/accounts/{ACCOUNT_ID}/invites"
    headers = build_invite_headers()
    payload = {
        "email_addresses": [email],
        "role": "standard-user",
        "resend_emails": True
    }

    log_info("Invite", "发送邀请", email=email, account_id=ACCOUNT_ID[:8] + "..." if ACCOUNT_ID else "None")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            # 验证邀请是否真的发送成功
            if check_invite_pending(email):
                log_info("Invite", "邀请成功(已验证)", email=email)
                return True, "success"
            else:
                log_warn("Invite", "邀请状态不确定", "API返回200但未在待处理列表中找到", email=email)
                return True, "success"  # 仍然返回成功，可能有延迟
        else:
            log_error("Invite", "邀请失败", response.text[:200], email=email, status=response.status_code)
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        log_error("Invite", "邀请异常", str(e), email=email)
        return False, str(e)


def get_verification_code(email, max_retries=10, interval=3):
    """从邮箱获取验证码"""
    url = f"{EMAIL_API_BASE}/emailList"
    headers = {
        "Authorization": EMAIL_API_AUTH,
        "Content-Type": "application/json"
    }
    payload = {"toEmail": email}

    log_info("Code", "获取验证码", email=email, max_retries=max_retries)

    for i in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            data = response.json()

            if data.get("code") == 200:
                emails = data.get("data", [])
                if emails:
                    latest_email = emails[0]
                    subject = latest_email.get("subject", "")
                    match = re.search(r"代码为\s*(\d{6})", subject)
                    if match:
                        code = match.group(1)
                        log_info("Code", "验证码获取成功", email=email, code=code, attempt=i+1)
                        return code, None
        except Exception as e:
            log_error("Code", "获取异常", str(e), email=email, attempt=i+1)

        if i < max_retries - 1:
            time.sleep(interval)

    log_warn("Code", "验证码获取失败", email=email, attempts=max_retries)
    return None, "未能获取验证码"


def is_logged_in():
    """检查用户是否已登录"""
    return "user" in session


def get_current_user():
    """获取当前登录用户"""
    return session.get("user")


def check_seats_available(force_refresh=False):
    """检查是否还有可用名额

    Args:
        force_refresh: 是否强制刷新数据（高并发场景下应该为 True）
    """
    try:
        data, _ = refresh_stats(force=force_refresh)
        if not data:
            return False, None  # 无法获取数据时默认拒绝（更安全）
        seats_in_use = data.get("seats_in_use", 0)
        seats_entitled = data.get("seats_entitled", 0)
        pending = data.get("pending_invites", 0)
        available = seats_entitled - seats_in_use - pending
        return available > 0, data
    except TeamBannedException:
        raise  # 传递给上层处理
    except Exception:
        return False, None  # 出错时默认拒绝


def acquire_invite_lock(user_id, timeout=30):
    """获取邀请分布式锁，防止并发超卖
    
    Args:
        user_id: 用户ID，用于锁的唯一标识
        timeout: 锁超时时间（秒）
    
    Returns:
        lock_token: 锁令牌，用于释放锁；None 表示获取失败
    """
    lock_key = f"{INVITE_LOCK_KEY}:{user_id}"
    lock_token = secrets.token_hex(8)
    
    # 使用 SET NX EX 原子操作获取锁
    acquired = redis_client.set(lock_key, lock_token, nx=True, ex=timeout)
    return lock_token if acquired else None


def release_invite_lock(user_id, lock_token):
    """释放邀请锁
    
    使用 Lua 脚本确保只有持有锁的人才能释放
    """
    lock_key = f"{INVITE_LOCK_KEY}:{user_id}"
    lua_script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    try:
        redis_client.eval(lua_script, 1, lock_key, lock_token)
    except Exception:
        pass  # 释放锁失败不影响主流程


def acquire_global_invite_lock(timeout=10):
    """获取全局邀请锁，用于检查和发送邀请的原子操作"""
    lock_token = secrets.token_hex(8)
    acquired = redis_client.set(INVITE_LOCK_KEY, lock_token, nx=True, ex=timeout)
    return lock_token if acquired else None


def release_global_invite_lock(lock_token):
    """释放全局邀请锁"""
    lua_script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    try:
        redis_client.eval(lua_script, 1, INVITE_LOCK_KEY, lock_token)
    except Exception:
        pass


def add_invite_record(user, email, password, success, message=""):
    """添加邀请记录到 Redis"""
    try:
        record_id = redis_client.incr(INVITE_COUNTER_KEY)
        record = {
            "id": record_id,
            "linuxdo_id": user.get("id"),
            "linuxdo_username": user.get("username"),
            "linuxdo_name": user.get("name"),
            "trust_level": user.get("trust_level"),
            "email": email,
            "password": password,
            "success": success,
            "message": message,
            "created_at": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
            "ip": get_client_ip_address()
        }
        redis_client.lpush(INVITE_RECORDS_KEY, json.dumps(record))
        return record
    except Exception as e:
        log_error("Redis", "保存记录失败", str(e))
        return None


def get_invite_records(limit=100):
    """从 Redis 获取邀请记录"""
    try:
        records = redis_client.lrange(INVITE_RECORDS_KEY, 0, limit - 1)
        return [json.loads(r) for r in records]
    except Exception as e:
        log_error("Redis", "获取记录失败", str(e))
        return []


def get_invite_stats():
    """获取邀请统计"""
    try:
        records = get_invite_records(1000)
        total = len(records)
        success_count = sum(1 for r in records if r.get("success"))
        return {
            "total_invites": total,
            "success_count": success_count,
            "fail_count": total - success_count
        }
    except Exception:
        return {"total_invites": 0, "success_count": 0, "fail_count": 0}


# ==================== 自动邀请处理 ====================

def process_auto_invite(user):
    """处理自动邀请流程（登录后自动调用）

    Returns:
        dict: 邀请结果，包含 success, email, password, message 等字段
    """
    user_id = user.get("id")
    username = user.get("username")
    client_ip = get_client_ip_address()

    result = {
        "success": False,
        "email": None,
        "password": None,
        "message": "",
        "code": None,
        "seats_full": False,
        "banned": False
    }

    # 1. 获取用户锁（防止同一用户重复提交）
    user_lock = acquire_invite_lock(user_id, timeout=60)
    if not user_lock:
        result["message"] = "您有一个邀请正在处理中，请稍后再试"
        return result

    try:
        # 2. 获取全局锁（防止并发超卖）
        global_lock = None
        for _ in range(3):
            global_lock = acquire_global_invite_lock(timeout=15)
            if global_lock:
                break
            time.sleep(0.5)

        if not global_lock:
            result["message"] = "系统繁忙，请稍后再试"
            return result

        try:
            # 3. 检查名额
            try:
                available, stats_data = check_seats_available(force_refresh=True)
            except TeamBannedException:
                result["message"] = "车已翻 - Team 账号状态异常"
                result["banned"] = True
                return result

            if not available:
                result["message"] = "车门已焊死，名额已满"
                result["seats_full"] = True
                return result

            # 4. 生成邮箱和密码
            email = generate_email_for_user(username)
            password = generate_password()
            result["email"] = email
            result["password"] = password

            log_info("Invite", "开始自动邀请流程", username=username, email=email, ip=client_ip)

            # 5. 创建邮箱用户
            success, msg = create_email_user(email, password, EMAIL_ROLE)
            if not success and "已存在" not in msg:
                result["message"] = f"创建邮箱失败: {msg}"
                add_invite_record(user, email, password, False, result["message"])
                return result

            # 6. 发送 ChatGPT 邀请
            success, msg = send_chatgpt_invite(email)
            if not success:
                result["message"] = f"发送邀请失败: {msg}"
                add_invite_record(user, email, password, False, result["message"])
                return result

            # 7. 邀请成功，保存待处理邀请信息用于轮询验证码
            session["pending_invite"] = {
                "email": email,
                "password": password,
                "created_at": time.time()
            }

            result["success"] = True
            result["message"] = "邀请发送成功，正在等待验证码"
            add_invite_record(user, email, password, True, "邀请发送成功")

            return result

        finally:
            if global_lock:
                release_global_invite_lock(global_lock)
    finally:
        release_invite_lock(user_id, user_lock)


# ==================== OAuth 路由 ====================

@app.route("/login")
def login():
    """重定向到 Linux DO OAuth 授权页面"""
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state

    params = {
        "client_id": LINUXDO_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": LINUXDO_REDIRECT_URI,
        "state": state,
    }
    auth_url = f"{LINUXDO_AUTHORIZE_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """OAuth 回调处理"""
    error = request.args.get("error")
    if error:
        return render_template("error.html", message=f"授权失败: {error}"), 400

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return render_template("error.html", message="未收到授权码"), 400

    if state != session.get("oauth_state"):
        return render_template("error.html", message="状态验证失败，请重试"), 400

    # 用授权码换取 access_token
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": LINUXDO_REDIRECT_URI,
        "client_id": LINUXDO_CLIENT_ID,
        "client_secret": LINUXDO_CLIENT_SECRET,
    }

    try:
        token_resp = requests.post(LINUXDO_TOKEN_URL, data=token_data, timeout=10)
        token_json = token_resp.json()

        if "access_token" not in token_json:
            log_error("Auth", "Token exchange failed", str(token_json))
            return render_template("error.html", message="获取令牌失败"), 400

        access_token = token_json["access_token"]

        # 获取用户信息
        user_resp = requests.get(
            LINUXDO_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        user_info = user_resp.json()

        # 检查信任等级
        trust_level = user_info.get("trust_level", 0)
        if trust_level < MIN_TRUST_LEVEL:
            return render_template(
                "error.html",
                message=f"您的信任等级为 {trust_level}，需要达到 {MIN_TRUST_LEVEL} 级才能使用此服务"
            ), 403

        # 保存用户信息到 session
        user = {
            "id": user_info.get("id"),
            "username": user_info.get("username"),
            "name": user_info.get("name"),
            "avatar_template": user_info.get("avatar_template"),
            "trust_level": trust_level,
            "active": user_info.get("active"),
        }
        session["user"] = user

        log_info("Auth", "用户登录", username=user_info.get("username"), trust_level=trust_level)
        session.permanent = True  # 启用持久化 Session

        # 登录成功后自动执行邀请流程
        invite_result = process_auto_invite(user)
        session["invite_result"] = invite_result

        return redirect(url_for("invite_page"))

    except Exception as e:
        log_error("Auth", "OAuth callback error", str(e))
        return render_template("error.html", message=f"认证过程出错: {str(e)}"), 500


@app.route("/logout")
def logout():
    """登出"""
    session.clear()
    return redirect(url_for("index"))


@app.route("/invite")
def invite_page():
    """邀请页面 - 需要登录"""
    if not is_logged_in():
        return redirect(url_for("login"))
    user = get_current_user()
    invite_result = session.get("invite_result", {})
    return render_template("invite.html", user=user, invite_result=invite_result)


@app.route("/api/auto-invite", methods=["POST"])
def auto_invite():
    """自动邀请 API - 执行完整的邀请流程（带并发控制）"""
    if not is_logged_in():
        return jsonify({"success": False, "message": "请先登录"}), 401

    user = get_current_user()
    user_id = user.get("id")
    client_ip = get_client_ip_address()

    # 1. 获取用户锁（防止同一用户重复提交）
    user_lock = acquire_invite_lock(user_id, timeout=60)
    if not user_lock:
        return jsonify({
            "success": False,
            "message": "您有一个邀请正在处理中，请稍后再试",
            "retry_after": 10
        }), 429

    try:
        # 2. 获取全局锁（防止并发超卖）
        global_lock = None
        for _ in range(3):  # 重试3次获取全局锁
            global_lock = acquire_global_invite_lock(timeout=15)
            if global_lock:
                break
            time.sleep(0.5)
        
        if not global_lock:
            return jsonify({
                "success": False,
                "message": "系统繁忙，请稍后再试",
                "retry_after": 5
            }), 503

        try:
            # 3. 在锁内强制刷新检查名额（双重检查）
            try:
                available, stats_data = check_seats_available(force_refresh=True)
            except TeamBannedException:
                return jsonify({
                    "success": False,
                    "message": "车已翻 - Team 账号状态异常",
                    "banned": True
                }), 503

            if not available:
                return jsonify({
                    "success": False,
                    "message": "车门已焊死，名额已满",
                    "seats_full": True,
                    "stats": stats_data
                })

            # 4. 名额充足，开始邀请流程
            email = generate_email_for_user(user["username"])
            password = generate_password()

            log_info("Invite", "开始自动邀请流程", username=user["username"], email=email, ip=client_ip)

            result = {
                "email": email,
                "password": password,
                "steps": []
            }

            # 步骤1: 创建邮箱用户
            success, msg = create_email_user(email, password, EMAIL_ROLE)
            result["steps"].append({
                "step": 1,
                "name": "创建邮箱用户",
                "success": success,
                "message": msg if not success else "成功"
            })
            if not success and "已存在" not in msg:
                add_invite_record(user, email, password, False, f"创建邮箱失败: {msg}")
                return jsonify({"success": False, "message": f"创建邮箱失败: {msg}", "result": result})

            # 步骤2: 发送邀请
            success, msg = send_chatgpt_invite(email)
            result["steps"].append({
                "step": 2,
                "name": "发送 ChatGPT 邀请",
                "success": success,
                "message": "成功" if success else msg
            })
            if not success:
                add_invite_record(user, email, password, False, f"发送邀请失败: {msg}")
                return jsonify({"success": False, "message": f"发送邀请失败: {msg}", "result": result})

            # 步骤3: 获取验证码 (异步方式，先返回，让前端轮询)
            result["steps"].append({
                "step": 3,
                "name": "等待验证码",
                "success": True,
                "message": "邀请已发送，请稍后获取验证码"
            })

            session["pending_invite"] = {
                "email": email,
                "password": password,
                "created_at": time.time()
            }

            # 记录成功邀请
            add_invite_record(user, email, password, True, "邀请发送成功")

            return jsonify({
                "success": True,
                "message": "邀请流程已启动",
                "result": result,
                "next": "poll_code"
            })
        finally:
            # 释放全局锁
            if global_lock:
                release_global_invite_lock(global_lock)
    finally:
        # 释放用户锁
        release_invite_lock(user_id, user_lock)


@app.route("/api/poll-code", methods=["GET"])
def poll_code():
    """轮询获取验证码"""
    if not is_logged_in():
        return jsonify({"success": False, "message": "请先登录"}), 401

    pending = session.get("pending_invite")
    if not pending:
        return jsonify({"success": False, "message": "没有待处理的邀请"})

    email = pending["email"]
    code, error = get_verification_code(email, max_retries=1, interval=0)

    if code:
        return jsonify({
            "success": True,
            "found": True,
            "code": code,
            "email": email,
            "password": pending["password"]
        })
    else:
        return jsonify({
            "success": True,
            "found": False,
            "message": "验证码尚未到达，请继续等待"
        })


@app.route("/")
def index():
    return render_template("index.html", site_key=CF_TURNSTILE_SITE_KEY)


@app.route("/send-invites", methods=["POST"])
def send_invites():
    client_ip = get_client_ip_address()

    raw_emails = request.form.get("emails", "").strip()
    email_list, valid_emails = parse_emails(raw_emails)

    cf_turnstile_response = request.form.get("cf-turnstile-response")
    turnstile_valid = validate_turnstile(cf_turnstile_response)

    if not turnstile_valid:
        log_warn("API", "CAPTCHA验证失败", ip=client_ip)
        return jsonify({"success": False, "message": "CAPTCHA verification failed. Please try again."})

    if not email_list:
        return jsonify({"success": False, "message": "Please enter at least one email address."})

    if not valid_emails:
        return jsonify({"success": False, "message": "Email addresses are not valid. Please check and try again."})

    headers = build_invite_headers()
    payload = {"email_addresses": valid_emails, "role": "standard-user", "resend_emails": True}
    invite_url = f"https://chatgpt.com/backend-api/accounts/{ACCOUNT_ID}/invites"

    try:
        resp = requests.post(invite_url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            log_info("API", "批量邀请成功", count=len(valid_emails), ip=client_ip)
            return jsonify(
                {
                    "success": True,
                    "message": f"Successfully sent invitations for: {', '.join(valid_emails)}",
                }
            )
        else:
            log_error("API", "批量邀请失败", status=resp.status_code, ip=client_ip)
            return jsonify(
                {
                    "success": False,
                    "message": "Failed to send invitations.",
                    "details": {"status_code": resp.status_code, "body": resp.text},
                }
            )
    except Exception as e:
        log_error("API", "批量邀请异常", str(e), ip=client_ip)
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


@app.route("/stats")
def stats():
    force_refresh = request.args.get("refresh") == "1"

    try:
        data, updated_at = refresh_stats(force=force_refresh)

        return jsonify(
            {
                "success": True,
                "data": data,
                "updated_at": updated_at,
                "cached": not force_refresh
            }
        )
    except TeamBannedException:
        log_error("Stats", "账号异常", "Team account banned")
        return jsonify({
            "success": False,
            "banned": True,
            "message": "车已翻 - Team 账号状态异常"
        }), 503
    except Exception as e:
        log_error("Stats", "获取统计失败", str(e))
        return jsonify({"success": False, "message": f"Error fetching stats: {str(e)}"}), 500


# ==================== 后台管理路由 ====================

@app.route("/admin")
def admin_page():
    """后台管理页面"""
    if not session.get("admin_logged_in"):
        return render_template("admin_login.html")
    return render_template("admin.html")


@app.route("/admin/login", methods=["POST"])
def admin_login():
    """后台登录"""
    password = request.form.get("password", "")
    if password == ADMIN_PASSWORD:
        session["admin_logged_in"] = True
        session.permanent = True  # 启用持久化 Session
        return redirect(url_for("admin_page"))
    return render_template("admin_login.html", error="密码错误")


@app.route("/admin/logout")
def admin_logout():
    """后台登出"""
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_page"))


@app.route("/api/admin/records")
def admin_records():
    """获取邀请记录"""
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "未授权"}), 401
    
    # 从 Redis 获取记录（已按时间倒序）
    records = get_invite_records(200)
    return jsonify({
        "success": True,
        "records": records,
        "total": len(records)
    })


@app.route("/api/admin/stats")
def admin_stats():
    """获取统计概览"""
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "未授权"}), 401
    
    stats = get_invite_stats()
    return jsonify({
        "success": True,
        "stats": stats
    })


@app.route("/api/admin/pending-invites")
def admin_pending_invites():
    """获取 ChatGPT Team 待处理邀请列表"""
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "未授权"}), 401

    items, total = get_pending_invites(100)
    log_info("Admin", "查询待处理邀请", total=total)
    return jsonify({
        "success": True,
        "items": items,
        "total": total
    })


# ==================== 健康检查 ====================

@app.route("/health")
def health_check():
    """健康检查端点"""
    status = {"status": "healthy", "redis": False, "scheduler": False}
    try:
        redis_client.ping()
        status["redis"] = True
    except Exception:
        status["status"] = "degraded"

    if scheduler and scheduler.running:
        status["scheduler"] = True

    return jsonify(status)


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


# ==================== 后台定时任务 ====================

def init_scheduler():
    """初始化后台定时任务"""
    global scheduler
    scheduler = BackgroundScheduler(daemon=True)

    # 每 60 秒刷新统计数据
    scheduler.add_job(
        func=background_refresh_stats,
        trigger="interval",
        seconds=STATS_REFRESH_INTERVAL,
        id="refresh_stats",
        name="刷新统计数据",
        replace_existing=True
    )

    # 每 60 秒刷新待处理邀请
    scheduler.add_job(
        func=background_refresh_pending_invites,
        trigger="interval",
        seconds=STATS_REFRESH_INTERVAL,
        id="refresh_pending_invites",
        name="刷新待处理邀请",
        replace_existing=True
    )

    scheduler.start()
    log_info("Scheduler", "后台定时任务已启动", interval=f"{STATS_REFRESH_INTERVAL}s")

    # 注册退出时关闭调度器
    atexit.register(lambda: scheduler.shutdown())


# 全局调度器变量
scheduler = None

# 初始化调度器（仅在非 reloader 进程中运行）
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    init_scheduler()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=39001)
