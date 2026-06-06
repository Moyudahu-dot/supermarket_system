
from services.product_service import (
    get_all_products,
    search_products,
    update_product,
    update_batch,
    delete_product,
    add_product,
    get_sales_statistics,
    add_batch
)
from services.user_service import (
    get_all_users,
    add_user,
    update_user,
    delete_user,
    change_password
)
from services.sales_service import (
    get_products_for_sales,
    search_products_for_sales,
    sell_product,
    create_order,
    get_my_orders,
    get_order_details
)
from services.auth_service import check_login
from services.audit_service import add_audit_log,get_audit_logs
from flask import Flask, render_template, request, redirect, flash, session, jsonify

app = Flask(__name__)
app.secret_key = "supermarket_secret_key"
def login_required():
    return 'user_id' in session

def role_required(role):
    return 'user_id' in session and session.get('role') == role

def roles_required(*roles):
    return 'user_id' in session and session.get('role') in roles
@app.route("/")
def index():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        user = check_login(username, password)

        if user is None:
            flash("Incorrect username or password.")
            return redirect("/login")

        user_id, username, role, status = user

        if status != "active":
            flash("This account is inactive.")
            return redirect("/login")

        session["user_id"] = user_id
        session["username"] = username
        session["role"] = role

        add_audit_log(
            user_id,
            username,
            role,
            "LOGIN",
            "users",
            user_id,
            f"User {username} logged in"
        )

        if role == "admin":
            return redirect("/users")
        elif role == "manager":
            return redirect("/products")
        elif role == "cashier":
            return redirect("/sales")
        else:
            flash("Unknown role.")
            return redirect("/login")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/products")
def products():
    if not role_required('manager'):
        return redirect('/login')
    keyword = request.args.get("keyword", "").strip()

    if keyword:
        product_list = search_products(keyword)

        if product_list:
            search_message = f"Found {len(product_list)} matching products for '{keyword}'."
        else:
            search_message = f"No products found for '{keyword}'."

    else:
        product_list = get_all_products()
        search_message = ""

    return render_template(
        "products.html",
        products=product_list,
        keyword=keyword,
        search_message=search_message
    )

@app.route("/products/update", methods=["POST"])
def update_product_route():
    if not role_required('manager'):
        return redirect('/login')

    product_id = request.form.get("product_id")
    product_name = request.form.get("product_name")
    price = request.form.get("price")

    update_product(product_id, product_name, price)

    add_audit_log(
        session['user_id'],
        session['username'],
        session['role'],
        "UPDATE_PRODUCT",
        "products",
        product_id,
        f"Updated product {product_id}"
    )

    return redirect("/products")


@app.route("/products/batches/update", methods=["POST"])
def update_batch_route():
    if not role_required('manager'):
        return redirect('/login')

    batch_id = request.form.get("batch_id")
    purchase_price = float(request.form.get("purchase_price"))
    selling_price = float(request.form.get("selling_price"))
    stock_quantity = int(request.form.get("stock_quantity"))

    update_batch(batch_id, purchase_price, selling_price, stock_quantity)

    add_audit_log(
        session['user_id'],
        session['username'],
        session['role'],
        "UPDATE_BATCH",
        "product_batches",
        batch_id,
        f"Updated batch {batch_id}"
    )

    return redirect("/products")


@app.route("/products/delete/<int:product_id>")
def delete_product_route(product_id):
    if not role_required('manager'):
        return redirect('/login')

    delete_product(product_id)

    add_audit_log(
        session['user_id'],
        session['username'],
        session['role'],
        "DELETE_PRODUCT",
        "products",
        product_id,
        f"Marked product {product_id} unavailable"
    )

    return redirect("/products")


@app.route("/products/add", methods=["POST"])
def add_product_route():
    if not role_required('manager'):
        return redirect('/login')

    product_name = request.form.get("product_name")
    product_code = request.form.get("product_code")
    category_id = int(request.form.get("category_id"))
    purchase_price = float(request.form.get("purchase_price"))
    selling_price = float(request.form.get("selling_price"))
    stock_quantity = int(request.form.get("stock_quantity"))
    manufacturer = request.form.get("manufacturer")

    product_id = add_product(
        product_name,
        product_code,
        category_id,
        purchase_price,
        selling_price,
        stock_quantity,
        manufacturer
    )

    add_audit_log(
        session['user_id'],
        session['username'],
        session['role'],
        "ADD_PRODUCT",
        "products",
        product_id,
        f"Added product {product_id} with initial batch"
    )

    return redirect("/products")


@app.route("/products/add_batch", methods=["POST"])
def add_batch_route():
    if not role_required('manager'):
        return redirect('/login')

    product_id = int(request.form.get("product_id"))
    purchase_price = float(request.form.get("purchase_price"))
    selling_price = float(request.form.get("selling_price"))
    stock_quantity = int(request.form.get("stock_quantity"))

    add_batch(product_id, purchase_price, selling_price, stock_quantity)

    add_audit_log(
        session['user_id'],
        session['username'],
        session['role'],
        "ADD_BATCH",
        "product_batches",
        product_id,
        f"Added batch for product {product_id}"
    )

    return redirect("/products")
@app.route("/users")
def users():
    user_list = get_all_users()
    if not role_required('admin'):
        return redirect('/login')
    return render_template("users.html", users=user_list)


@app.route("/users/add", methods=["POST"])
def add_user_route():
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")
    full_name = request.form.get("full_name")
    phone = request.form.get("phone")

    add_user(username, password, role, full_name, phone)

    return redirect("/users")


@app.route("/users/update", methods=["POST"])
def update_user_route():
    user_id = request.form.get("user_id")
    role = request.form.get("role")
    status = request.form.get("status")

    update_user(user_id, role, status)

    return redirect("/users")


@app.route("/users/delete/<int:user_id>")
def delete_user_route(user_id):
    delete_user(user_id)
    return redirect("/users")


@app.route("/sales")
def sales():
    if not role_required('cashier'):
        return redirect('/login')
    keyword = request.args.get("keyword", "").strip()

    if keyword:
        product_list = search_products_for_sales(keyword)

        if product_list:
            search_message = f"Found {len(product_list)} matching products for '{keyword}'."
        else:
            search_message = f"No products found for '{keyword}'."

    else:
        product_list = get_products_for_sales()
        search_message = ""

    return render_template(
        "sales.html",
        products=product_list,
        keyword=keyword,
        search_message=search_message
    )


@app.route("/sales/sell", methods=["POST"])
def sell_product_route():
    if not role_required('cashier'):
        return redirect('/login')

    product_id = int(request.form.get("product_id"))
    quantity = int(request.form.get("quantity"))
    cashier_id = session["user_id"]

    success, message = sell_product(cashier_id, product_id, quantity)
    flash(message)

    return redirect("/sales")


@app.route("/sales/orders")
def my_orders():
    if not role_required('cashier'):
        return redirect('/login')

    cashier_id = session["user_id"]
    orders = get_my_orders(cashier_id)
    return render_template("orders.html", orders=orders)

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    if not role_required('cashier'):
        return jsonify({'success': False, 'message': 'Please log in as a cashier.'})

    data = request.get_json() or {}
    items = data.get('items', [])

    if not items:
        return jsonify({'success': False, 'message': 'Order is empty.'})

    cashier_id = session.get('user_id')
    success, result = create_order(cashier_id, items)

    if not success:
        return jsonify({'success': False, 'message': result})

    add_audit_log(
        session.get('user_id'),
        session.get('username'),
        session.get('role'),
        "CREATE_ORDER",
        "sales_orders",
        result['order_id'],
        f"Created order {result['order_id']}, total amount {result['total_amount']}"
    )

    return jsonify({'success': True, 'message': 'Order created successfully.'})

@app.route('/cashier/order/<int:order_id>')
def cashier_order_detail(order_id):
    if 'user_id' not in session or session.get('role') != 'cashier':
        return redirect('/login')

    details = get_order_details(order_id, session['user_id'])

    return render_template(
        'cashier_order_detail.html',
        details=details
    )

@app.route('/manager/statistics')
def manager_statistics():
    if 'user_id' not in session or session.get('role') != 'manager':
        return redirect('/login')

    summary, product_stats = get_sales_statistics()

    return render_template(
        'manager_statistics.html',
        summary=summary,
        product_stats=product_stats
    )

@app.route('/users/logs')
def audit_logs():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    logs = get_audit_logs()
    return render_template('audit_logs.html', logs=logs)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password_page():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        old_password = request.form.get('old_password').strip()
        new_password = request.form.get('new_password').strip()
        confirm_password = request.form.get('confirm_password').strip()

        if new_password != confirm_password:
            flash("New passwords do not match.")
            return redirect('/change_password')

        success, message = change_password(
            session['user_id'],
            old_password,
            new_password
        )

        flash(message)

        if success:
            return redirect('/login')

        return redirect('/change_password')

    return render_template('change_password.html')

if __name__ == "__main__":
    app.run(debug=True)