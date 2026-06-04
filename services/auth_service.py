from werkzeug.security import check_password_hash, generate_password_hash
from db import get_connection

def check_login(username, password):
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

    # 兼容旧的明文密码
    if stored_password == password:
        hashed_password = generate_password_hash(password)

        cur.execute("""
            UPDATE users
            SET password = %s
            WHERE user_id = %s;
        """, (hashed_password, user_id))

        conn.commit()

    elif not check_password_hash(stored_password, password):
        cur.close()
        conn.close()
        return None

    cur.close()
    conn.close()

    return user_id, username, role, status