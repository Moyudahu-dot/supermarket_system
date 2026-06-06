from db import get_connection


def _sync_product_stock(cur, product_id):
    cur.execute("""
        UPDATE products
        SET stock_quantity = (
            SELECT COALESCE(SUM(stock_quantity), 0)
            FROM product_batches
            WHERE product_id = %s
        )
        WHERE product_id = %s;
    """, (product_id, product_id))


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
            COALESCE(pb.purchase_price, 0) AS purchase_price,
            COALESCE(pb.selling_price, p.price) AS selling_price,
            COALESCE(pb.stock_quantity, 0) AS stock_quantity,
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
            COALESCE(b.purchase_price, 0) AS cost_price,
            COALESCE(b.selling_price, p.price) AS selling_price,
            COALESCE(b.stock_quantity, 0) AS stock_quantity,
            p.manufacturer
        FROM products p
        LEFT JOIN product_batches b
            ON p.product_id = b.product_id
        WHERE p.status = 'available'
          AND (
              p.product_name ILIKE %s
              OR p.product_code ILIKE %s
              OR p.manufacturer ILIKE %s
          )
        ORDER BY p.product_id, b.batch_id;
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def update_product(product_id, product_name, price):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE products
            SET product_name = %s,
                price = %s
            WHERE product_id = %s
              AND status = 'available';
        """, (product_name, price, product_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def update_batch(batch_id, purchase_price, selling_price, stock_quantity):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE product_batches
            SET purchase_price = %s,
                selling_price = %s,
                stock_quantity = %s
            WHERE batch_id = %s
            RETURNING product_id;
        """, (purchase_price, selling_price, stock_quantity, batch_id))

        row = cur.fetchone()
        if row is None:
            raise ValueError("Batch does not exist.")

        product_id = row[0]
        _sync_product_stock(cur, product_id)

        cur.execute("""
            UPDATE products
            SET price = %s
            WHERE product_id = %s;
        """, (selling_price, product_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
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
    purchase_price,
    selling_price,
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
            selling_price,
            stock_quantity,
            manufacturer
        ))

        product_id = cur.fetchone()[0]

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

        _sync_product_stock(cur, product_id)
        conn.commit()
        return product_id

    except Exception as e:
        conn.rollback()
        raise e
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

        _sync_product_stock(cur, product_id)

        cur.execute("""
            UPDATE products
            SET price = %s
            WHERE product_id = %s;
        """, (selling_price, product_id))

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
