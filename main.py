from flask import Flask, render_template, url_for, request, jsonify, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime
from pathlib import Path

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SECRET_KEY'] = 'dev-secret-key'
db = SQLAlchemy(app)


# MySQL connection for admin data
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="tcg_store"
    )


# Password hashing helper
def hash_password(password):
    ph = PasswordHasher()
    return ph.hash(password)


# Placeholder cart count until cart logic is implemented
def get_cart_count():
    cart = session.get('cart', {})
    return sum(cart.values())


def get_cart_items():
    cart = session.get('cart', {})
    if not cart:
        return [], 0

    product_ids = [int(product_id) for product_id in cart.keys()]
    placeholders = ', '.join(['%s'] * len(product_ids))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        f"""
        SELECT ProductID, title, selling_price, image_url
        FROM Products
        WHERE ProductID IN ({placeholders})
        """,
        product_ids,
    )
    product_rows = cursor.fetchall()
    cursor.close()
    connection.close()

    product_map = {row['ProductID']: row for row in product_rows}
    cart_items = []
    subtotal = 0

    for product_id_str in cart:
        product_id = int(product_id_str)
        row = product_map.get(product_id)
        if not row:
            continue

        image_url = row.get('image_url') or ''
        image_name = resolve_product_image_path(image_url).split('/')[-1]
        quantity = cart[product_id_str]
        price = float(row['selling_price'])
        line_total = price * quantity
        subtotal += line_total

        cart_items.append({
            'id': product_id,
            'title': row['title'],
            'image': image_name,
            'price': price,
            'quantity': quantity,
            'line_total': line_total,
        })

    return cart_items, subtotal


def upsert_customer(cursor, first_name, last_name, email, phone, address):
    cursor.execute(
        'SELECT CustomerID FROM Customers WHERE email = %s',
        (email,)
    )
    customer_row = cursor.fetchone()

    if customer_row:
        customer_id = customer_row['CustomerID']
        cursor.execute(
            '''
            UPDATE Customers
            SET first_name = %s,
                last_name = %s,
                phone_number = %s,
                address = %s
            WHERE CustomerID = %s
            ''',
            (first_name, last_name, phone, address, customer_id)
        )
        return customer_id

    cursor.execute(
        '''
        INSERT INTO Customers (first_name, last_name, email, phone_number, address)
        VALUES (%s, %s, %s, %s, %s)
        ''',
        (first_name, last_name, email, phone, address)
    )
    return cursor.lastrowid


def get_product_stock(product_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        '''
        SELECT Products.title, COALESCE(Inventory.quantity, 0) AS quantity
        FROM Products
        LEFT JOIN Inventory ON Inventory.ProductID = Products.ProductID
        WHERE Products.ProductID = %s
        ''',
        (product_id,)
    )
    product_row = cursor.fetchone()
    cursor.close()
    connection.close()
    return product_row


PRODUCT_IMAGE_DIR = Path(app.static_folder) / 'images' / 'products'
AVAILABLE_PRODUCT_IMAGES = sorted(
    [path.name for path in PRODUCT_IMAGE_DIR.iterdir() if path.is_file()],
    key=len,
    reverse=True,
)


def resolve_product_image_path(image_url):
    if not image_url:
        return ''

    cleaned_path = image_url.replace('\\', '/').replace('static/', '').strip('/')

    for file_name in AVAILABLE_PRODUCT_IMAGES:
        if cleaned_path.endswith(file_name):
            return f'images/products/{file_name}'

    fallback_name = cleaned_path.split('/')[-1]
    return f'images/products/{fallback_name}' if fallback_name else ''


def build_products_query(selected_game, sort_option):
    where_clauses = []
    parameters = []

    if selected_game:
        where_clauses.append('game = %s')
        parameters.append(selected_game)

    sort_clauses = {
        'title': 'title ASC',
        'price_asc': 'selling_price ASC, title ASC',
        'price_desc': 'selling_price DESC, title ASC',
        'rarity_asc': 'rarity ASC, title ASC',
        'rarity_desc': 'rarity DESC, title ASC',
    }

    order_by = sort_clauses.get(sort_option, 'title ASC')

    query = [
        'SELECT ProductID, game, title, rarity, selling_price, image_url',
        'FROM Products',
    ]

    if where_clauses:
        query.append('WHERE ' + ' AND '.join(where_clauses))

    query.append(f'ORDER BY {order_by}')
    return '\n'.join(query), parameters


def get_featured_products(limit=8):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT ProductID, title, selling_price, image_url
        FROM Products
        ORDER BY selling_price DESC, title ASC
        LIMIT %s
        """,
        (limit,)
    )
    product_rows = cursor.fetchall()
    cursor.close()
    connection.close()

    featured_products = []
    for row in product_rows:
        image_url = row.get('image_url') or ''
        featured_products.append({
            'id': row['ProductID'],
            'title': row['title'],
            'price': row['selling_price'],
            'image_path': resolve_product_image_path(image_url),
        })

    return featured_products


def get_admin_dashboard_data():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        '''
        SELECT COALESCE(SUM(total_amount), 0) AS total_sales,
               COUNT(*) AS total_orders
        FROM Orders
        '''
    )
    order_totals = cursor.fetchone() or {}

    cursor.execute(
        '''
        SELECT COALESCE(SUM((OrderItems.price - Products.cost_price) * OrderItems.quantity), 0) AS total_profit
        FROM OrderItems
        INNER JOIN Products ON Products.ProductID = OrderItems.ProductID
        '''
    )
    profit_totals = cursor.fetchone() or {}

    cursor.execute(
        '''
        SELECT CONCAT(Customers.first_name, ' ', Customers.last_name) AS customer,
               Orders.total_amount AS total,
               Orders.order_date AS order_date
        FROM Orders
        INNER JOIN Customers ON Customers.CustomerID = Orders.CustomerID
        ORDER BY Orders.order_date DESC
        LIMIT 8
        '''
    )
    recent_order_rows = cursor.fetchall()

    cursor.close()
    connection.close()

    recent_orders = []
    for row in recent_order_rows:
        order_date = row.get('order_date')
        recent_orders.append({
            'customer': row.get('customer', 'Unknown'),
            'total': f"{float(row.get('total', 0)):.2f}",
            'date': order_date.strftime('%Y-%m-%d %I:%M %p') if order_date else '',
        })

    total_sales = float(order_totals.get('total_sales', 0) or 0)
    total_orders = int(order_totals.get('total_orders', 0) or 0)
    total_profit = float(profit_totals.get('total_profit', 0) or 0)

    return {
        'total_sales': f"{total_sales:.2f}",
        'total_orders': total_orders,
        'total_profit': f"{total_profit:.2f}",
        'recent_orders': recent_orders,
    }


def get_admin_inventory_products():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        '''
        SELECT Products.ProductID,
               Products.title,
               Products.cost_price,
               Products.selling_price,
               Products.image_url,
               COALESCE(SUM(Inventory.quantity), 0) AS quantity
        FROM Products
        LEFT JOIN Inventory ON Inventory.ProductID = Products.ProductID
        GROUP BY Products.ProductID, Products.title, Products.cost_price, Products.selling_price, Products.image_url
        ORDER BY Products.title ASC
        '''
    )
    product_rows = cursor.fetchall()
    cursor.close()
    connection.close()

    products = []
    for row in product_rows:
        image_url = row.get('image_url') or ''
        image_name = resolve_product_image_path(image_url).split('/')[-1]

        products.append({
            'id': row['ProductID'],
            'title': row['title'],
            'image': image_name,
            'cost_price': f"{float(row['cost_price']):.2f}",
            'sell_price': f"{float(row['selling_price']):.2f}",
            'quantity': int(row['quantity']),
        })

    return products


# ------------------------------
# CUSTOMER ROUTES
# ------------------------------

# Home page
@app.route('/')
def index():
    cart_count = get_cart_count()
    featured_products = get_featured_products()
    return render_template('index.html', cart_count=cart_count, featured_products=featured_products)


# Product listing page
@app.route('/products')
def products():
    cart_count = get_cart_count()
    selected_game = request.args.get('game', '').strip()
    sort_option = request.args.get('sort', 'title').strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('SELECT DISTINCT game FROM Products ORDER BY game')
    games = [row['game'] for row in cursor.fetchall()]

    query, parameters = build_products_query(selected_game, sort_option)
    cursor.execute(
        query,
        parameters
    )
    product_rows = cursor.fetchall()
    cursor.close()
    connection.close()

    products = []
    for row in product_rows:
        image_url = row.get('image_url') or ''
        image_name = resolve_product_image_path(image_url)

        products.append({
            'id': row['ProductID'],
            'game': row['game'],
            'title': row['title'],
            'rarity': row['rarity'],
            'sell_price': row['selling_price'],
            'image_path': image_name,
        })

    return render_template(
        'products.html',
        cart_count=cart_count,
        products=products,
        games=games,
        selected_game=selected_game,
        sort_option=sort_option,
    )


# Shopping cart page
@app.route('/cart')
def cart():
    cart_count = get_cart_count()
    cart_items, subtotal = get_cart_items()
    return render_template('cart.html', cart_count=cart_count, cart_items=cart_items, subtotal=subtotal)


# Checkout page
@app.route('/checkout')
def checkout():
    cart_count = get_cart_count()
    checkout_data = session.pop('checkout_form', {})
    return render_template('checkout.html', cart_count=cart_count, checkout_data=checkout_data)


@app.route('/success')
def success():
    cart_count = get_cart_count()
    order_details = session.get('last_order', {})
    return render_template('success.html', cart_count=cart_count, order_details=order_details)

# ------------------------------
# CART ACTION PLACEHOLDERS
# ------------------------------

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product_row = get_product_stock(product_id)
    if not product_row:
        flash('That product could not be found.', 'error')
        return redirect(request.referrer or url_for('products'))

    cart = session.get('cart', {})
    product_key = str(product_id)

    current_quantity = cart.get(product_key, 0)
    available_quantity = int(product_row['quantity'])

    if available_quantity <= 0 or current_quantity >= available_quantity:
        flash(f'{product_row["title"]} is out of stock.', 'error')
        return redirect(request.referrer or url_for('products'))

    cart[product_key] = current_quantity + 1
    session['cart'] = cart
    session.modified = True
    return redirect(request.referrer or url_for('cart'))

@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    cart = session.get('cart', {})
    product_key = str(product_id)
    action = request.form.get('action')

    if product_key in cart:
        if action == 'increase':
            cart[product_key] += 1
        elif action == 'decrease':
            cart[product_key] -= 1
            if cart[product_key] <= 0:
                cart.pop(product_key, None)

    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/complete_order', methods=['POST'])
def complete_order():
    cart_items, subtotal = get_cart_items()
    if not cart_items:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart'))

    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()

    session['checkout_form'] = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'phone': phone,
        'address': address,
    }

    if not all([first_name, last_name, email, phone, address]):
        flash('Please complete all checkout fields before placing your order.', 'error')
        return redirect(url_for('checkout'))

    connection = get_db_connection()

    try:
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        customer_id = upsert_customer(cursor, first_name, last_name, email, phone, address)

        for item in cart_items:
            cursor.execute(
                'SELECT quantity FROM Inventory WHERE ProductID = %s FOR UPDATE',
                (item['id'],)
            )
            inventory_row = cursor.fetchone()

            if not inventory_row:
                raise ValueError(f'Inventory record not found for product {item["id"]}.')

            available_quantity = int(inventory_row['quantity'])
            if available_quantity < item['quantity']:
                raise ValueError(f'Not enough stock for {item["title"]}.')

        cursor.execute(
            'INSERT INTO Orders (CustomerID, total_amount) VALUES (%s, %s)',
            (customer_id, subtotal)
        )
        order_id = cursor.lastrowid

        for item in cart_items:
            cursor.execute(
                '''
                INSERT INTO OrderItems (OrderID, ProductID, quantity, price)
                VALUES (%s, %s, %s, %s)
                ''',
                (order_id, item['id'], item['quantity'], item['price'])
            )

            cursor.execute(
                'UPDATE Inventory SET quantity = quantity - %s WHERE ProductID = %s',
                (item['quantity'], item['id'])
            )

        connection.commit()

    except ValueError as error:
        connection.rollback()
        flash(str(error), 'error')
        return redirect(url_for('checkout'))

    except Exception:
        connection.rollback()
        flash('We could not complete your order right now. Please try again.', 'error')
        return redirect(url_for('checkout'))

    finally:
        connection.close()

    order_details = {
        'order_id': order_id,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'phone': phone,
        'address': address,
        'item_count': sum(item['quantity'] for item in cart_items),
        'subtotal': subtotal,
        'items': cart_items,
    }

    session['last_order'] = order_details
    session['cart'] = {}
    session.pop('checkout_form', None)
    session.modified = True

    return redirect(url_for('success'))

# ------------------------------
# ADMIN PLACEHOLDERS
# ------------------------------

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_user_id'):
        return redirect(url_for('admin_login'))

    dashboard_data = get_admin_dashboard_data()
    return render_template(
        'admin-dashboard.html',
        active='dashboard',
        total_sales=dashboard_data['total_sales'],
        total_orders=dashboard_data['total_orders'],
        total_profit=dashboard_data['total_profit'],
        recent_orders=dashboard_data['recent_orders'],
    )

@app.route('/admin/inventory')
def admin_inventory():
    if not session.get('admin_user_id'):
        return redirect(url_for('admin_login'))

    products = get_admin_inventory_products()
    return render_template('admin-inventory.html', products=products, active='inventory')


@app.route('/admin/inventory/add-stock/<int:product_id>', methods=['POST'])
def admin_add_stock(product_id):
    if not session.get('admin_user_id'):
        return redirect(url_for('admin_login'))

    stock_to_add_raw = request.form.get('stock_to_add', '').strip()

    try:
        stock_to_add = int(stock_to_add_raw)
    except ValueError:
        flash('Please enter a valid whole number for stock.', 'error')
        return redirect(url_for('admin_inventory'))

    if stock_to_add <= 0:
        flash('Stock to add must be greater than 0.', 'error')
        return redirect(url_for('admin_inventory'))

    connection = get_db_connection()

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            'SELECT ProductID, title FROM Products WHERE ProductID = %s LIMIT 1',
            (product_id,)
        )
        product = cursor.fetchone()

        if not product:
            flash('Product not found.', 'error')
            return redirect(url_for('admin_inventory'))

        cursor.execute(
            'UPDATE Inventory SET quantity = quantity + %s WHERE ProductID = %s',
            (stock_to_add, product_id)
        )

        if cursor.rowcount == 0:
            cursor.execute(
                'INSERT INTO Inventory (ProductID, quantity) VALUES (%s, %s)',
                (product_id, stock_to_add)
            )

        connection.commit()
        flash(f'Added {stock_to_add} units to {product["title"]}.', 'success')

    except Exception:
        connection.rollback()
        flash('Could not update stock right now. Please try again.', 'error')

    finally:
        connection.close()

    return redirect(url_for('admin_inventory'))

@app.route('/admin/orders')
def admin_orders():
    if not session.get('admin_user_id'):
        return redirect(url_for('admin_login'))
    return render_template('admin-orders.html', active='orders')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_user_id'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('admin-login.html', error='Please enter both username and password.')

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            '''
            SELECT UserID, username, password_hash
            FROM Admin
            WHERE username = %s
            LIMIT 1
            ''',
            (username,)
        )
        admin_user = cursor.fetchone()
        cursor.close()
        connection.close()

        if admin_user:
            ph = PasswordHasher()
            try:
                ph.verify(admin_user['password_hash'], password)
                session['admin_user_id'] = admin_user['UserID']
                session['admin_username'] = admin_user['username']
                return redirect(url_for('admin_dashboard'))
            except VerifyMismatchError:
                pass

        return render_template('admin-login.html', error='Invalid username or password.')

    return render_template('admin-login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_user_id', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
