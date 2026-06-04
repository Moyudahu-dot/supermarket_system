from db import get_connection
from werkzeug.security import check_password_hash, generate_password_hash

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, username, role, full_name, phone, status
        FROM users
        ORDER BY user_id;
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def add_user(username, password, role, full_name, phone):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (username, password, role, full_name, phone, status)
        VALUES (%s, %s, %s, %s, %s, 'active');
    """, (username, password, role, full_name, phone))

    conn.commit()
    cur.close()
    conn.close()


def update_user(user_id, role, status):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET role = %s,
            status = %s
        WHERE user_id = %s;
    """, (role, status, user_id))

    conn.commit()
    cur.close()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM users
        WHERE user_id = %s;
    """, (user_id,))

    conn.commit()
    cur.close()
    conn.close()

def change_password(user_id, old_password, new_password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT password
        FROM users
        WHERE user_id = %s;
    """, (user_id,))

    row = cur.fetchone()

    if row is None:
        cur.close()
        conn.close()
        return False, "User not found."

    stored_password = row[0]

    if stored_password == old_password:
        pass
    elif not check_password_hash(stored_password, old_password):
        cur.close()
        conn.close()
        return False, "Old password is incorrect."

    new_hashed_password = generate_password_hash(new_password)

    cur.execute("""
        UPDATE users
        SET password = %s
        WHERE user_id = %s;
    """, (new_hashed_password, user_id))

    conn.commit()
    cur.close()
    conn.close()

    return True, "Password changed successfully."