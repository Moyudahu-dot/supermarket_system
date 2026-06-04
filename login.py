import tkinter as tk
from tkinter import messagebox
import psycopg2


# 1. 数据库连接函数
def get_connection():
    try:
        conn = psycopg2.connect(
            dbname="supermarket",
            user="gaussdb",
            password="Enmo@123",
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to connect to database:\n{e}")
        return None


# 2. 登录验证函数
def login():
    username = entry_username.get().strip()
    password = entry_password.get().strip()

    if username == "" or password == "":
        messagebox.showwarning("Input Error", "Username and password cannot be empty.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        sql = """
        SELECT user_id, username, role, status
        FROM users
        WHERE username = %s AND password = %s;
        """
        cur.execute(sql, (username, password))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user is None:
            messagebox.showerror("Login Failed", "Incorrect username or password.")
            return

        user_id, username, role, status = user
        global current_user_id, current_username, current_role

        current_user_id = user_id
        current_username = username
        current_role = role
        if status != "active":
            messagebox.showerror("Login Failed", "This account is inactive.")
            return

        if role == "admin":
            open_admin_window()
        elif role == "manager":
            open_product_window()
        elif role == "cashier":
            open_sales_window()
        else:
            messagebox.showerror("Role Error", "Unknown role.")

    except Exception as e:
        messagebox.showerror("Login Error", f"An error occurred during login:\n{e}")



#4.1  商品管理窗口
def open_product_window():
    window = tk.Toplevel()
    window.title("Product Management")
    window.geometry("900x930")

    # 标题
    tk.Label(window, text="Product List", font=("Arial", 16, "bold")).pack(pady=10)

    # Load Products 按钮
    btn_load = tk.Button(window, text="Load Products", command=load_products, width=15)
    btn_load.pack(pady=5)

    # 商品列表显示区 —— 放到最上面
    global text_area
    text_area = tk.Text(window, width=95, height=15)
    text_area.pack(pady=10)

    # =========================
    # Add Product
    # =========================
    add_frame = tk.LabelFrame(window, text="Add Product", padx=10, pady=10)
    add_frame.pack(pady=10, fill="x", padx=10)

    global entry_name, entry_code, entry_category, entry_price, entry_stock

    tk.Label(add_frame, text="Product Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_name = tk.Entry(add_frame, width=25)
    entry_name.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="Product Code:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_code = tk.Entry(add_frame, width=25)
    entry_code.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="Category ID:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    entry_category = tk.Entry(add_frame, width=25)
    entry_category.grid(row=2, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="Price:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
    entry_price = tk.Entry(add_frame, width=25)
    entry_price.grid(row=3, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="Stock Quantity:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
    entry_stock = tk.Entry(add_frame, width=25)
    entry_stock.grid(row=4, column=1, padx=5, pady=5)

    btn_add = tk.Button(add_frame, text="Add Product", command=add_product, width=15)
    btn_add.grid(row=5, column=0, columnspan=2, pady=10)

    # =========================
    # Update Product
    # =========================
    update_frame = tk.LabelFrame(window, text="Update Product", padx=10, pady=10)
    update_frame.pack(pady=10, fill="x", padx=10)

    global entry_update_id, entry_update_price, entry_update_stock

    tk.Label(update_frame, text="Product ID to Update:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_update_id = tk.Entry(update_frame, width=25)
    entry_update_id.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(update_frame, text="New Price:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_update_price = tk.Entry(update_frame, width=25)
    entry_update_price.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(update_frame, text="New Stock Quantity:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    entry_update_stock = tk.Entry(update_frame, width=25)
    entry_update_stock.grid(row=2, column=1, padx=5, pady=5)

    btn_update = tk.Button(update_frame, text="Update Product", command=update_product, width=15)
    btn_update.grid(row=3, column=0, columnspan=2, pady=10)

    # =========================
    # Delete Product
    # =========================
    delete_frame = tk.LabelFrame(window, text="Delete Product", padx=10, pady=10)
    delete_frame.pack(pady=10, fill="x", padx=10)

    global entry_delete_id

    tk.Label(delete_frame, text="Product ID to Delete:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_delete_id = tk.Entry(delete_frame, width=25)
    entry_delete_id.grid(row=0, column=1, padx=5, pady=5)

    btn_delete = tk.Button(delete_frame, text="Delete Product", command=delete_product, width=15)
    btn_delete.grid(row=1, column=0, columnspan=2, pady=10)


# -------------------------
 # 全部查询
# -------------------------
def load_products():
    conn = get_connection()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("SELECT product_id, product_name, price, stock_quantity FROM products;")
    rows = cur.fetchall()

    text_area.delete(1.0, tk.END)

    for row in rows:
        product_id, product_name, price, stock_quantity = row
        text_area.insert(
            tk.END,
            f"ID: {product_id} | Name: {product_name} | Price: {price} | Stock: {stock_quantity}\n"
        )

    cur.close()
    conn.close()

# -------------------------
#添加商品
# -------------------------
def add_product():
    name = entry_name.get().strip()
    code = entry_code.get().strip()
    category = entry_category.get().strip()
    price = entry_price.get().strip()
    stock = entry_stock.get().strip()

    # 1. 基本判空
    if not name or not code or not category or not price or not stock:
        messagebox.showwarning("Input Error", "Please fill in all fields.")
        return

    # 2. 数据类型检查
    try:
        category = int(category)
        price = float(price)
        stock = int(stock)
    except ValueError:
        messagebox.showerror("Format Error", "Category ID and Stock must be integers, Price must be a number.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO products (product_name, product_code, category_id, price, stock_quantity)
        VALUES (%s, %s, %s, %s, %s);
        """

        cur.execute(sql, (name, code, category, price, stock))
        conn.commit()

        messagebox.showinfo("Success", "Product added successfully.")

        # 清空输入框
        entry_name.delete(0, tk.END)
        entry_code.delete(0, tk.END)
        entry_category.delete(0, tk.END)
        entry_price.delete(0, tk.END)
        entry_stock.delete(0, tk.END)

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Failed to add product:\n{e}")

    finally:
        cur.close()
        conn.close()

# -------------------------
# 修改商品区域
# -------------------------
def update_product():
    product_id = entry_update_id.get().strip()
    new_price = entry_update_price.get().strip()
    new_stock = entry_update_stock.get().strip()

    # 1. 判空
    if not product_id or not new_price or not new_stock:
        messagebox.showwarning("Input Error", "Please fill in all update fields.")
        return

    # 2. 类型检查
    try:
        product_id = int(product_id)
        new_price = float(new_price)
        new_stock = int(new_stock)
    except ValueError:
        messagebox.showerror("Format Error", "Product ID and Stock must be integers, Price must be a number.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        # 3. 先检查商品是否存在
        check_sql = "SELECT * FROM products WHERE product_id = %s;"
        cur.execute(check_sql, (product_id,))
        product = cur.fetchone()

        if product is None:
            messagebox.showerror("Update Failed", "Product ID does not exist.")
            return

        # 4. 执行更新
        update_sql = """
        UPDATE products
        SET price = %s, stock_quantity = %s
        WHERE product_id = %s;
        """
        cur.execute(update_sql, (new_price, new_stock, product_id))
        conn.commit()

        messagebox.showinfo("Success", "Product updated successfully.")

        # 5. 清空输入框
        entry_update_id.delete(0, tk.END)
        entry_update_price.delete(0, tk.END)
        entry_update_stock.delete(0, tk.END)


    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Failed to update product:\n{e}")

    finally:
        cur.close()
        conn.close()
# -------------------------
#删除商品
# -------------------------
def delete_product():
    product_id = entry_delete_id.get().strip()

    # 1. 判空
    if not product_id:
        messagebox.showwarning("Input Error", "Please enter a product ID.")
        return

    # 2. 类型检查
    try:
        product_id = int(product_id)
    except ValueError:
        messagebox.showerror("Format Error", "Product ID must be an integer.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        # 3. 先检查这个商品是否存在
        check_sql = "SELECT * FROM products WHERE product_id = %s;"
        cur.execute(check_sql, (product_id,))
        product = cur.fetchone()

        if product is None:
            messagebox.showerror("Delete Failed", "Product ID does not exist.")
            cur.close()
            conn.close()
            return

        # 4. 执行删除
        delete_sql = "DELETE FROM products WHERE product_id = %s;"
        cur.execute(delete_sql, (product_id,))
        conn.commit()

        messagebox.showinfo("Success", "Product deleted successfully.")

        # 5. 清空删除输入框
        entry_delete_id.delete(0, tk.END)

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Failed to delete product:\n{e}")

    finally:
        cur.close()
        conn.close()

# 4.2 销售窗口
def open_sales_window():
    window = tk.Toplevel()
    window.title("Sales System")
    window.geometry("850x650")

    # 标题
    tk.Label(window, text="Sales Module", font=("Arial", 16, "bold")).pack(pady=10)

    # =========================
    # 结果显示区（放最上面）
    # =========================
    global sales_text_area
    sales_text_area = tk.Text(window, width=95, height=16)
    sales_text_area.pack(pady=10)

    # =========================
    # Search Product
    # =========================
    search_frame = tk.LabelFrame(window, text="Search Product", padx=10, pady=10)
    search_frame.pack(padx=10, pady=8, fill="x")

    global entry_sales_search

    tk.Label(search_frame, text="Keyword (Name / Code / Manufacturer):").grid(
        row=0, column=0, padx=5, pady=5, sticky="e"
    )

    entry_sales_search = tk.Entry(search_frame, width=30)
    entry_sales_search.grid(row=0, column=1, padx=5, pady=5)

    btn_load_products = tk.Button(
        search_frame, text="View Products", command=load_products_for_sales, width=15
    )
    btn_load_products.grid(row=0, column=2, padx=10, pady=5)

    btn_search_products = tk.Button(
        search_frame, text="Search", command=search_products_for_sales, width=12
    )
    btn_search_products.grid(row=0, column=3, padx=10, pady=5)

    # =========================
    # Sell Product
    # =========================
    sell_frame = tk.LabelFrame(window, text="Sell Product", padx=10, pady=10)
    sell_frame.pack(padx=10, pady=8, fill="x")

    global entry_sale_product_id, entry_sale_quantity

    tk.Label(sell_frame, text="Product ID:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_sale_product_id = tk.Entry(sell_frame, width=20)
    entry_sale_product_id.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(sell_frame, text="Quantity:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    entry_sale_quantity = tk.Entry(sell_frame, width=20)
    entry_sale_quantity.grid(row=0, column=3, padx=5, pady=5)

    btn_sell = tk.Button(sell_frame, text="Sell Product", command=sell_product, width=15)
    btn_sell.grid(row=0, column=4, padx=10, pady=5)

    # =========================
    # Orders
    # =========================
    order_frame = tk.LabelFrame(window, text="Orders", padx=10, pady=10)
    order_frame.pack(padx=10, pady=8, fill="x")

    global entry_order_detail_id

    btn_view_orders = tk.Button(
        order_frame, text="View My Orders", command=view_my_orders, width=15
    )
    btn_view_orders.grid(row=0, column=0, padx=10, pady=5)

    tk.Label(order_frame, text="Order ID:").grid(row=0, column=1, padx=5, pady=5, sticky="e")
    entry_order_detail_id = tk.Entry(order_frame, width=20)
    entry_order_detail_id.grid(row=0, column=2, padx=5, pady=5)

    btn_view_details = tk.Button(
        order_frame, text="View Order Details", command=view_order_details, width=18
    )
    btn_view_details.grid(row=0, column=3, padx=10, pady=5)

#查看全部商品（给收银员用）
def load_products_for_sales():
    conn = get_connection()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
        SELECT product_id, product_name, price, stock_quantity
        FROM products;
    """)

    rows = cur.fetchall()

    sales_text_area.delete(1.0, tk.END)

    for row in rows:
        product_id, name, price, stock = row
        sales_text_area.insert(
            tk.END,
            f"ID: {product_id} | Name: {name} | Price: {price} | Stock: {stock}\n"
        )

    cur.close()
    conn.close()
#模糊查询（给收银员用）
def search_products_for_sales():
    keyword = entry_sales_search.get().strip()

    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        sql = """
        SELECT product_id, product_name, product_code, manufacturer, price, stock_quantity
        FROM products
        WHERE product_name LIKE %s
           OR product_code LIKE %s
           OR manufacturer LIKE %s;
        """

        like_keyword = '%' + keyword + '%'
        cur.execute(sql, (like_keyword, like_keyword, like_keyword))

        rows = cur.fetchall()

        sales_text_area.delete(1.0, tk.END)

        if not rows:
            sales_text_area.insert(tk.END, "No products found.\n")
        else:
            sales_text_area.insert(tk.END, "=== Product Search Results ===\n\n")
            for row in rows:
                product_id, product_name, product_code, manufacturer, price, stock_quantity = row
                sales_text_area.insert(
                    tk.END,
                    f"ID: {product_id} | Name: {product_name} | Code: {product_code} | "
                    f"Manufacturer: {manufacturer} | Price: {price} | Stock: {stock_quantity}\n"
                )

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to search products:\n{e}")

    finally:
        cur.close()
        conn.close()

#买商品
def sell_product():
    product_id = entry_sale_product_id.get().strip()
    quantity = entry_sale_quantity.get().strip()

    # 1. 判空
    if not product_id or not quantity:
        messagebox.showwarning("Input Error", "Please enter product ID and quantity.")
        return

    # 2. 类型检查
    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except ValueError:
        messagebox.showerror("Format Error", "Product ID and quantity must be integers.")
        return

    if quantity <= 0:
        messagebox.showerror("Input Error", "Quantity must be greater than 0.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        # 3. 查询商品是否存在，并取价格和库存
        sql_product = """
        SELECT product_name, price, stock_quantity
        FROM products
        WHERE product_id = %s;
        """
        cur.execute(sql_product, (product_id,))
        product = cur.fetchone()

        if product is None:
            sales_text_area.delete(1.0, tk.END)
            sales_text_area.insert(tk.END, "Product does not exist.\n")
            return

        product_name, price, stock_quantity = product

        # 4. 检查库存
        if stock_quantity < quantity:
            sales_text_area.delete(1.0, tk.END)
            sales_text_area.insert(
                tk.END,
                f"Insufficient stock. Current stock: {stock_quantity}, requested: {quantity}\n"
            )
            return

        # 5. 计算金额
        subtotal = price * quantity

        # 6. 插入订单主表
        sql_order = """
        INSERT INTO sales_orders (cashier_id, total_amount)
        VALUES (%s, %s)
        RETURNING order_id;
        """
        cur.execute(sql_order, (current_user_id, subtotal))
        order_id = cur.fetchone()[0]

        # 7. 插入订单明细表
        sql_item = """
        INSERT INTO sales_order_items (order_id, product_id, quantity, unit_price, subtotal)
        VALUES (%s, %s, %s, %s, %s);
        """
        cur.execute(sql_item, (order_id, product_id, quantity, price, subtotal))

        # 8. 更新库存
        sql_update_stock = """
        UPDATE products
        SET stock_quantity = stock_quantity - %s
        WHERE product_id = %s;
        """
        cur.execute(sql_update_stock, (quantity, product_id))

        # 9. 提交事务
        conn.commit()

        # 10. 显示成功结果
        sales_text_area.delete(1.0, tk.END)
        sales_text_area.insert(
            tk.END,
            f"Sale successful!\n"
            f"Order ID: {order_id}\n"
            f"Product: {product_name}\n"
            f"Quantity: {quantity}\n"
            f"Unit Price: {price}\n"
            f"Total Amount: {subtotal}\n"
        )

        # 11. 清空输入框
        entry_sale_product_id.delete(0, tk.END)
        entry_sale_quantity.delete(0, tk.END)

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Failed to sell product:\n{e}")

    finally:
        cur.close()
        conn.close()

#查看商品订单
def view_my_orders():
    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        sql = """
        SELECT so.order_id, u.username, so.total_amount, so.sale_time
        FROM sales_orders so
        JOIN users u ON so.cashier_id = u.user_id
        WHERE so.cashier_id = %s
        ORDER BY so.sale_time DESC;
        """

        cur.execute(sql, (current_user_id,))
        rows = cur.fetchall()

        sales_text_area.delete(1.0, tk.END)

        if not rows:
            sales_text_area.insert(tk.END, "No orders found.\n")
        else:
            sales_text_area.insert(tk.END, "=== My Orders ===\n\n")
            for row in rows:
                order_id, username, total_amount, sale_time = row
                sales_text_area.insert(
                    tk.END,
                    f"Order ID: {order_id} | Cashier: {username} | Total: {total_amount} | Time: {sale_time}\n"
                )

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load orders:\n{e}")

    finally:
        cur.close()
        conn.close()
#查看订单明细
def view_order_details():
    order_id = entry_order_detail_id.get().strip()

    # 1. 判空
    if not order_id:
        messagebox.showwarning("Input Error", "Please enter an order ID.")
        return

    # 2. 类型检查
    try:
        order_id = int(order_id)
    except ValueError:
        messagebox.showerror("Format Error", "Order ID must be an integer.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        sql = """
        SELECT soi.order_id, p.product_name, soi.quantity, soi.unit_price, soi.subtotal
        FROM sales_order_items soi
        JOIN products p ON soi.product_id = p.product_id
        WHERE soi.order_id = %s;
        """

        cur.execute(sql, (order_id,))
        rows = cur.fetchall()

        sales_text_area.delete(1.0, tk.END)

        if not rows:
            sales_text_area.insert(tk.END, "No order details found for this order ID.\n")
        else:
            sales_text_area.insert(tk.END, f"=== Order Details for Order ID: {order_id} ===\n\n")
            for row in rows:
                _, product_name, quantity, unit_price, subtotal = row
                sales_text_area.insert(
                    tk.END,
                    f"Product: {product_name} | Quantity: {quantity} | Unit Price: {unit_price} | Subtotal: {subtotal}\n"
                )

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load order details:\n{e}")

    finally:
        cur.close()
        conn.close()
# 4.3 管理用户窗口
def open_admin_window():
    window = tk.Toplevel()
    window.title("Admin System")
    window.geometry("765x800")

    # 标题
    tk.Label(window, text="User Management", font=("Arial", 16, "bold")).pack(pady=10)
    # =========================
    # 滚动区域
    # =========================
    container = tk.Frame(window)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # 鼠标滚轮支持
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-int(e.delta / 120), "units"))
    # =========================
    # 结果显示区（放最上面）
    # =========================
    global admin_text_area
    admin_text_area = tk.Text(scrollable_frame,  width=105, height=15)
    admin_text_area.pack(pady=10)

    # =========================
    # View Users
    # =========================
    view_frame = tk.LabelFrame(scrollable_frame, text="View Users", padx=10, pady=10)
    view_frame.pack(padx=10, pady=8, fill="x")

    btn_view_users = tk.Button(view_frame, text="View All Users", command=load_users, width=15)
    btn_view_users.pack(pady=5)

    # =========================
    # Add User
    # =========================
    add_frame = tk.LabelFrame(scrollable_frame,  text="Add User", padx=10, pady=10)
    add_frame.pack(padx=10, pady=8, fill="x")

    global entry_user_username, entry_user_password, entry_user_role, entry_user_fullname, entry_user_phone

    tk.Label(add_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_user_username = tk.Entry(add_frame, width=25)
    entry_user_username.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="Password:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    entry_user_password = tk.Entry(add_frame, width=25)
    entry_user_password.grid(row=0, column=3, padx=5, pady=5)

    tk.Label(add_frame, text="Role (admin/manager/cashier):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_user_role = tk.Entry(add_frame, width=25)
    entry_user_role.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="Full Name:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
    entry_user_fullname = tk.Entry(add_frame, width=25)
    entry_user_fullname.grid(row=1, column=3, padx=5, pady=5)

    tk.Label(add_frame, text="Phone:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    entry_user_phone = tk.Entry(add_frame, width=25)
    entry_user_phone.grid(row=2, column=1, padx=5, pady=5)

    btn_add_user = tk.Button(add_frame, text="Add User", command=add_user, width=15)
    btn_add_user.grid(row=2, column=3, padx=10, pady=5)

    # =========================
    # Update User
    # =========================
    update_frame = tk.LabelFrame(scrollable_frame, text="Update User", padx=10, pady=10)
    update_frame.pack(padx=10, pady=8, fill="x")

    global entry_update_user_id, entry_update_user_role, entry_update_user_status

    tk.Label(update_frame, text="User ID:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_update_user_id = tk.Entry(update_frame, width=20)
    entry_update_user_id.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(update_frame, text="New Role:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    entry_update_user_role = tk.Entry(update_frame, width=20)
    entry_update_user_role.grid(row=0, column=3, padx=5, pady=5)

    tk.Label(update_frame, text="New Status (active/inactive):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_update_user_status = tk.Entry(update_frame, width=20)
    entry_update_user_status.grid(row=1, column=1, padx=5, pady=5)

    btn_update_user = tk.Button(update_frame, text="Update User", command=update_user, width=15)
    btn_update_user.grid(row=1, column=3, padx=10, pady=5)

    # =========================
    # Delete User
    # =========================
    delete_frame = tk.LabelFrame(scrollable_frame,text="Delete User", padx=10, pady=10)
    delete_frame.pack(padx=10, pady=8, fill="x")

    global entry_delete_user_id

    tk.Label(delete_frame, text="User ID to Delete:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_delete_user_id = tk.Entry(delete_frame, width=25)
    entry_delete_user_id.grid(row=0, column=1, padx=5, pady=5)

    btn_delete_user = tk.Button(delete_frame, text="Delete User", command=delete_user, width=15)
    btn_delete_user.grid(row=0, column=2, padx=10, pady=5)
#查看用户
def load_users():
    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        sql = """
        SELECT user_id, username, role, full_name, phone, status
        FROM users
        ORDER BY user_id;
        """
        cur.execute(sql)
        rows = cur.fetchall()

        admin_text_area.delete(1.0, tk.END)

        if not rows:
            admin_text_area.insert(tk.END, "No users found.\n")
        else:
            admin_text_area.insert(tk.END, "=== User List ===\n\n")
            for row in rows:
                user_id, username, role, full_name, phone, status = row
                admin_text_area.insert(
                    tk.END,
                    f"ID: {user_id} | Username: {username} | Role: {role} | Name: {full_name} | Phone: {phone} | Status: {status}\n"
                )

    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to load users:\n{e}")

    finally:
        cur.close()
        conn.close()

#添加用户
def add_user():
    username = entry_user_username.get().strip()
    password = entry_user_password.get().strip()
    role = entry_user_role.get().strip()
    full_name = entry_user_fullname.get().strip()
    phone = entry_user_phone.get().strip()

    if not username or not password or not role:
        messagebox.showwarning("Input Error", "Username, password, and role are required.")
        return

    if role not in ["admin", "manager", "cashier"]:
        messagebox.showerror("Role Error", "Role must be admin, manager, or cashier.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        sql = """
        INSERT INTO users (username, password, role, full_name, phone, status)
        VALUES (%s, %s, %s, %s, %s, 'active');
        """
        cur.execute(sql, (username, password, role, full_name, phone))
        conn.commit()

        messagebox.showinfo("Success", "User added successfully.")

        entry_user_username.delete(0, tk.END)
        entry_user_password.delete(0, tk.END)
        entry_user_role.delete(0, tk.END)
        entry_user_fullname.delete(0, tk.END)
        entry_user_phone.delete(0, tk.END)

        load_users()

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Failed to add user:\n{e}")

    finally:
        cur.close()
        conn.close()

#删除用户
def delete_user():
    user_id = entry_delete_user_id.get().strip()

    if not user_id:
        messagebox.showwarning("Input Error", "Please enter a user ID.")
        return

    try:
        user_id = int(user_id)
    except ValueError:
        messagebox.showerror("Format Error", "User ID must be an integer.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        check_sql = "SELECT * FROM users WHERE user_id = %s;"
        cur.execute(check_sql, (user_id,))
        user = cur.fetchone()

        if user is None:
            messagebox.showerror("Delete Failed", "User ID does not exist.")
            return

        delete_sql = "DELETE FROM users WHERE user_id = %s;"
        cur.execute(delete_sql, (user_id,))
        conn.commit()

        messagebox.showinfo("Success", "User deleted successfully.")
        entry_delete_user_id.delete(0, tk.END)

        load_users()

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Failed to delete user:\n{e}")

    finally:
        cur.close()
        conn.close()

#修改用户
def update_user():
    user_id = entry_update_user_id.get().strip()
    new_role = entry_update_user_role.get().strip()
    new_status = entry_update_user_status.get().strip()

    if not user_id or not new_role or not new_status:
        messagebox.showwarning("Input Error", "Please fill in all update fields.")
        return

    try:
        user_id = int(user_id)
    except ValueError:
        messagebox.showerror("Format Error", "User ID must be an integer.")
        return

    if new_role not in ["admin", "manager", "cashier"]:
        messagebox.showerror("Role Error", "Role must be admin, manager, or cashier.")
        return

    if new_status not in ["active", "inactive"]:
        messagebox.showerror("Status Error", "Status must be active or inactive.")
        return

    conn = get_connection()
    if conn is None:
        return

    try:
        cur = conn.cursor()

        check_sql = "SELECT * FROM users WHERE user_id = %s;"
        cur.execute(check_sql, (user_id,))
        user = cur.fetchone()

        if user is None:
            messagebox.showerror("Update Failed", "User ID does not exist.")
            return

        update_sql = """
        UPDATE users
        SET role = %s, status = %s
        WHERE user_id = %s;
        """
        cur.execute(update_sql, (new_role, new_status, user_id))
        conn.commit()

        messagebox.showinfo("Success", "User updated successfully.")

        entry_update_user_id.delete(0, tk.END)
        entry_update_user_role.delete(0, tk.END)
        entry_update_user_status.delete(0, tk.END)

        load_users()

    except Exception as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Failed to update user:\n{e}")

    finally:
        cur.close()
        conn.close()
# 5. 主界面
root = tk.Tk()
root.title("Supermarket Management System - Login")
root.geometry("400x250")

label_title = tk.Label(root, text="Login System", font=("Arial", 16))
label_title.pack(pady=10)

frame_form = tk.Frame(root)
frame_form.pack(pady=10)

label_username = tk.Label(frame_form, text="Username:", font=("Arial", 12))
label_username.grid(row=0, column=0, padx=10, pady=10)

entry_username = tk.Entry(frame_form, font=("Arial", 12))
entry_username.grid(row=0, column=1, padx=10, pady=10)

label_password = tk.Label(frame_form, text="Password:", font=("Arial", 12))
label_password.grid(row=1, column=0, padx=10, pady=10)

entry_password = tk.Entry(frame_form, font=("Arial", 12), show="*")
entry_password.grid(row=1, column=1, padx=10, pady=10)

btn_login = tk.Button(root, text="Login", font=("Arial", 12), width=12, command=login)
btn_login.pack(pady=20)

root.mainloop()