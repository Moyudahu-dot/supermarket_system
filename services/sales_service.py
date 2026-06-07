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


def get_products_for_sales():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.product_id,
            p.product_name,
            p.product_code,
            COALESCE((
                SELECT b.selling_price
                FROM product_batches b
                WHERE b.product_id = p.product_id
                  AND b.stock_quantity > 0
                ORDER BY b.purchase_time ASC, b.batch_id ASC
                LIMIT 1
            ), p.price) AS price,
            p.stock_quantity,
            p.manufacturer
        FROM products p
        WHERE p.status = 'available'
          AND p.stock_quantity > 0
        ORDER BY p.product_id;
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
        SELECT
            p.product_id,
            p.product_name,
            p.product_code,
            COALESCE((
                SELECT b.selling_price
                FROM product_batches b
                WHERE b.product_id = p.product_id
                  AND b.stock_quantity > 0
                ORDER BY b.purchase_time ASC, b.batch_id ASC
                LIMIT 1
            ), p.price) AS price,
            p.stock_quantity,
            p.manufacturer
        FROM products p
        WHERE p.status = 'available'
          AND p.stock_quantity > 0
          AND (
              p.product_name ILIKE %s
              OR p.product_code ILIKE %s
              OR p.manufacturer ILIKE %s
          )
        ORDER BY p.product_id;
    """, (like_keyword, like_keyword, like_keyword))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def create_order(cashier_id, items):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO sales_orders (cashier_id, total_amount, total_profit)
            VALUES (%s, 0, 0)
            RETURNING order_id;
        """, (cashier_id,))

        order_id = cur.fetchone()[0]
        total_amount = 0
        total_profit = 0
        touched_product_ids = set()

        for item in items:
            product_id = int(item['product_id'])
            quantity = int(item['quantity'])

            if quantity <= 0:
                raise ValueError("Quantity must be greater than 0.")

            cur.execute("""
                SELECT product_name, stock_quantity
                FROM products
                WHERE product_id = %s
                  AND status = 'available'
                FOR UPDATE;
            """, (product_id,))

            product = cur.fetchone()
            if product is None:
                raise ValueError("Product does not exist or is unavailable.")

            product_name, total_stock = product
            if total_stock < quantity:
                raise ValueError(f"Not enough stock for {product_name}.")

            cur.execute("""
                SELECT batch_id, purchase_price, selling_price, stock_quantity
                FROM product_batches
                WHERE product_id = %s
                  AND stock_quantity > 0
                ORDER BY purchase_time ASC, batch_id ASC
                FOR UPDATE;
            """, (product_id,))

            batches = cur.fetchall()
            remaining_quantity = quantity

            for batch_id, purchase_price, selling_price, batch_stock in batches:
                if remaining_quantity == 0:
                    break

                sold_quantity = min(remaining_quantity, batch_stock)
                subtotal = selling_price * sold_quantity
                profit = (selling_price - purchase_price) * sold_quantity

                cur.execute("""
                    INSERT INTO sales_order_items
                    (order_id, product_id, batch_id, quantity, purchase_price, unit_price, subtotal, profit)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    order_id,
                    product_id,
                    batch_id,
                    sold_quantity,
                    purchase_price,
                    selling_price,
                    subtotal,
                    profit
                ))

                cur.execute("""
                    UPDATE product_batches
                    SET stock_quantity = stock_quantity - %s
                    WHERE batch_id = %s;
                """, (sold_quantity, batch_id))

                total_amount += subtotal
                total_profit += profit
                remaining_quantity -= sold_quantity

            if remaining_quantity > 0:
                raise ValueError(f"Not enough batch stock for {product_name}.")

            touched_product_ids.add(product_id)

        for product_id in touched_product_ids:
            _sync_product_stock(cur, product_id)

        cur.execute("""
            UPDATE sales_orders
            SET total_amount = %s,
                total_profit = %s
            WHERE order_id = %s;
        """, (total_amount, total_profit, order_id))

        conn.commit()
        return True, {
            "order_id": order_id,
            "total_amount": total_amount,
            "total_profit": total_profit
        }

    except Exception as e:
        conn.rollback()
        return False, str(e)

    finally:
        cur.close()
        conn.close()


def sell_product(cashier_id, product_id, quantity):
    success, result = create_order(cashier_id, [
        {
            "product_id": product_id,
            "quantity": quantity
        }
    ])

    if not success:
        return False, f"Sale failed: {result}"

    return True, (
        f"Sale successful. Order ID: {result['order_id']}, "
        f"Total: {result['total_amount']}, Profit: {result['total_profit']}"
    )


def get_my_orders(cashier_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            so.order_id,
            so.total_amount,
            so.total_profit,
            so.sale_time
        FROM sales_orders so
        WHERE so.cashier_id = %s
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
