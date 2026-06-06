from db import get_connection

def get_all_products():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.product_id,
            p.product_name,
            p.product_code,
            p.category_id,
            pb.batch_id,
            pb.purchase_price,
            pb.selling_price,
            pb.stock_quantity,
            p.manufacturer
    FROM products p
    LEFT JOIN product_batches pb
        ON p.product_id = pb.product_id
    WHERE p.status = 'available'
    ORDER BY p.product_id, pb.batch_id;
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows
def search_products(keyword):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.product_id,
            p.product_name,
            p.product_code,
            p.category_id,
            b.batch_id,
            COALESCE(b.purchase_price, p.price) AS cost_price,
            COALESCE(b.selling_price, p.price) AS selling_price,
            COALESCE(b.stock_quantity, p.stock_quantity) AS stock_quantity,
            p.manufacturer
        FROM products p
        LEFT JOIN product_batches b
            ON p.product_id = b.product_id
        WHERE p.product_name ILIKE %s
           OR p.product_code ILIKE %s
           OR p.manufacturer ILIKE %s
        ORDER BY p.product_id, b.batch_id;
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
def update_product(product_id, product_name, price, stock_quantity):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE products
        SET product_name = %s,
            price = %s,
            stock_quantity = %s
        WHERE product_id = %s;
    """, (product_name, price, stock_quantity, product_id))

    cur.execute("""
        UPDATE product_batches
        SET selling_price = %s,
            stock_quantity = %s
        WHERE product_id = %s;
    """, (price, stock_quantity, product_id))

    conn.commit()
    cur.close()
    conn.close()
def delete_product(product_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE products
        SET status = 'unavailable'
        WHERE product_id = %s;
    """, (product_id,))

    conn.commit()
    cur.close()
    conn.close()
def add_product(
    product_name,
    product_code,
    category_id,
    price,
    stock_quantity,
    manufacturer
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO products
            (
                product_name,
                product_code,
                category_id,
                price,
                stock_quantity,
                manufacturer
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING product_id;
        """, (
            product_name,
            product_code,
            category_id,
            price,
            stock_quantity,
            manufacturer
        ))


        conn.commit()



    finally:
        cur.close()
        conn.close()
def add_batch(product_id, purchase_price, selling_price, stock_quantity):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO product_batches
            (
                product_id,
                purchase_price,
                selling_price,
                stock_quantity
            )
            VALUES (%s, %s, %s, %s);
        """, (
            product_id,
            purchase_price,
            selling_price,
            stock_quantity
        ))

        cur.execute("""
            UPDATE products
            SET stock_quantity = (
                SELECT COALESCE(SUM(stock_quantity), 0)
                FROM product_batches
                WHERE product_id = %s
            ),
            price = %s
            WHERE product_id = %s;
        """, (
            product_id,
            selling_price,
            product_id
        ))

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()
def get_sales_statistics():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS order_count,
            COALESCE(SUM(total_amount), 0) AS total_sales,
            COALESCE(SUM(total_profit), 0) AS total_profit
        FROM sales_orders;
    """)
    summary = cur.fetchone()

    cur.execute("""
        SELECT
            p.product_name,
            p.product_code,
            SUM(soi.quantity) AS total_quantity,
            SUM(soi.subtotal) AS total_amount,
            SUM(soi.profit) AS total_profit
        FROM sales_order_items soi
        JOIN products p ON soi.product_id = p.product_id
        GROUP BY p.product_id, p.product_name, p.product_code
        ORDER BY total_quantity DESC;
    """)
    product_stats = cur.fetchall()

    cur.close()
    conn.close()

    return summary, product_stats