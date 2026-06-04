from db import get_connection


def get_products_for_sales():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT product_id, product_name, product_code, price, stock_quantity, manufacturer
        FROM products
        ORDER BY product_id;
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def search_products_for_sales(keyword):
    conn = get_connection()
    cur = conn.cursor()

    like_keyword = "%" + keyword + "%"

    cur.execute("""
        SELECT product_id, product_name, product_code, price, stock_quantity, manufacturer
        FROM products
        WHERE product_name ILIKE %s
           OR product_code ILIKE %s
           OR manufacturer ILIKE %s
        ORDER BY product_id;
    """, (like_keyword, like_keyword, like_keyword))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def sell_product(cashier_id, product_id, quantity):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT product_name
            FROM products
            WHERE product_id = %s;
        """, (product_id,))


        product = cur.fetchone()

        if product is None:
            return False, "Product does not exist."

        product_name = product[0]

        cur.execute("""
            SELECT batch_id, purchase_price, selling_price, stock_quantity
            FROM product_batches
            WHERE product_id = %s AND stock_quantity > 0
            ORDER BY purchase_time ASC
            LIMIT 1;
        """, (product_id,))

        batch = cur.fetchone()

        if batch is None:
            return False, "No available stock batch for this product."

        batch_id, purchase_price, selling_price, batch_stock = batch

        if batch_stock < quantity:
            return False, f"Insufficient stock in current batch. Current batch stock: {batch_stock}."

        subtotal = selling_price * quantity
        profit = (selling_price - purchase_price) * quantity

        cur.execute("""
            INSERT INTO sales_orders (cashier_id, total_amount)
            VALUES (%s, %s)
            RETURNING order_id;
        """, (cashier_id, subtotal))

        order_id = cur.fetchone()[0]

        cur.execute("""
                    UPDATE product_batches
                    SET stock_quantity = stock_quantity - %s
                    WHERE batch_id = %s;
                    """, (quantity, batch_id))

        cur.execute("""
                    UPDATE products
                    SET stock_quantity = stock_quantity - %s
                    WHERE product_id = %s;
                    """, (quantity, product_id))

        cur.execute("""
            INSERT INTO sales_order_items
            (order_id, product_id, batch_id, quantity, unit_price, subtotal, purchase_price, profit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            order_id,
            product_id,
            batch_id,
            quantity,
            selling_price,
            subtotal,
            purchase_price,
            profit
        ))

        cur.execute("""
            UPDATE product_batches
            SET stock_quantity = stock_quantity - %s
            WHERE batch_id = %s;
        """, (quantity, batch_id))

        conn.commit()

        return True, f"Sale successful. Order ID: {order_id}, Product: {product_name}, Batch: {batch_id}, Total: {subtotal}, Profit: {profit}"

    except Exception as e:
        conn.rollback()
        return False, f"Sale failed: {e}"

    finally:
        cur.close()
        conn.close()


def get_my_orders(cashier_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            so.order_id,
            so.total_amount,
            COALESCE(SUM(soi.profit), 0) AS total_profit,
            so.sale_time
        FROM sales_orders so
        LEFT JOIN sales_order_items soi
            ON so.order_id = soi.order_id
        WHERE so.cashier_id = %s
        GROUP BY so.order_id, so.total_amount, so.sale_time
        ORDER BY so.sale_time DESC;
    """, (cashier_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
def get_order_details(order_id, cashier_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            so.order_id,
            p.product_name,
            p.product_code,
            soi.quantity,
            soi.unit_price,
            soi.subtotal,
            soi.profit,
            so.sale_time
        FROM sales_orders so
        JOIN sales_order_items soi
            ON so.order_id = soi.order_id
        JOIN products p
            ON soi.product_id = p.product_id
        WHERE so.order_id = %s
          AND so.cashier_id = %s
        ORDER BY soi.item_id;
    """, (order_id, cashier_id))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows