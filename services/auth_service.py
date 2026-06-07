from datetime import datetime, timedelta, timezone
from secrets import randbelow

from werkzeug.security import check_password_hash, generate_password_hash

from db import get_connection

# 使用带盐的 SHA-256 派生算法保存密码，避免明文密码落库。
PASSWORD_HASH_METHOD = "pbkdf2:sha256"
PASSWORD_SALT_LENGTH = 16

MAX_LOGIN_FAILURES = 5
CAPTCHA_AFTER_FAILURES = 3
LOCKOUT_MINUTES = 5

# 简单风控状态：按用户名统计失败次数。进程重启后会清空；生产环境可迁移到数据库/Redis。
_login_risk_state = {}


def hash_password(password):
    return generate_password_hash(
        password,
        method=PASSWORD_HASH_METHOD,
        salt_length=PASSWORD_SALT_LENGTH,
    )


def is_password_hash(value):
    if not value:
        return False
    return value.startswith(("pbkdf2:", "scrypt:", "bcrypt$", "$2a$", "$2b$", "$2y$"))


def verify_password(stored_password, candidate_password):
    if is_password_hash(stored_password):
        return check_password_hash(stored_password, candidate_password)
    return stored_password == candidate_password


def get_utc_now():
    return datetime.now(timezone.utc)


def _normalize_username(username):
    return (username or "").strip().lower()


def get_login_risk(username):
    key = _normalize_username(username)
    state = _login_risk_state.get(key, {})
    locked_until = state.get("locked_until")

    if locked_until and locked_until <= get_utc_now():
        _login_risk_state.pop(key, None)
        return {"failed_count": 0, "locked_until": None, "requires_captcha": False}

    failed_count = state.get("failed_count", 0)
    return {
        "failed_count": failed_count,
        "locked_until": locked_until,
        "requires_captcha": failed_count >= CAPTCHA_AFTER_FAILURES,
    }


def register_login_failure(username):
    key = _normalize_username(username)
    state = _login_risk_state.setdefault(key, {"failed_count": 0, "locked_until": None})
    state["failed_count"] = state.get("failed_count", 0) + 1

    if state["failed_count"] >= MAX_LOGIN_FAILURES:
        state["locked_until"] = get_utc_now() + timedelta(minutes=LOCKOUT_MINUTES)

    return get_login_risk(username)


def clear_login_failures(username):
    _login_risk_state.pop(_normalize_username(username), None)


def generate_captcha_code():
    return f"{randbelow(9000) + 1000}"


def check_login(username, password):
    risk = get_login_risk(username)
    if risk["locked_until"]:
        return None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, username, password, role, status
        FROM users
        WHERE username = %s;
    """, (username,))

    user = cur.fetchone()

    if user is None:
        cur.close()
        conn.close()
        return None

    user_id, username, stored_password, role, status = user

    if not verify_password(stored_password, password):
        cur.close()
        conn.close()
        return None

    if not is_password_hash(stored_password):
        cur.execute("""
            UPDATE users
            SET password = %s
            WHERE user_id = %s;
        """, (hash_password(password), user_id))

        conn.commit()

    cur.close()
    conn.close()

    clear_login_failures(username)
    return user_id, username, role, status
