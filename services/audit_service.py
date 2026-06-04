from db import get_connection
from datetime import datetime
current_time = datetime.now()
def add_audit_log(user_id, username, role, action, target_table=None, target_id=None, description=None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO audit_logs
        (
            user_id,
            username,
            role,
            action,
            target_table,
            target_id,
            description,
            created_at
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        user_id,
        username,
        role,
        action,
        target_table,
        target_id,
        description,
        current_time
    ))

    conn.commit()
    cur.close()
    conn.close()

def get_audit_logs():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT log_id, username, role, action, target_table, target_id, description, created_at
        FROM audit_logs
        ORDER BY created_at DESC;
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows