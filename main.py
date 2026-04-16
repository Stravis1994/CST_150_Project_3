from flask import Flask, render_template, url_for, request, jsonify, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime

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
    return 0


# ------------------------------
# CUSTOMER ROUTES
# ------------------------------

# Home page
@app.route('/')
def index():
    cart_count = get_cart_count()
    return render_template('index.html', cart_count=cart_count)


# Product listing page
@app.route('/products')
def products():
    cart_count = get_cart_count()
    return render_template('products.html', cart_count=cart_count)


# Shopping cart page
@app.route('/cart')
def cart():
    cart_count = get_cart_count()
    return render_template('cart.html', cart_count=cart_count)


# Checkout page
@app.route('/checkout')
def checkout():
    cart_count = get_cart_count()
    return render_template('checkout.html', cart_count=cart_count)

# ------------------------------
# CART ACTION PLACEHOLDERS
# ------------------------------

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    return redirect(url_for('cart'))

@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    return redirect(url_for('cart'))

@app.route('/complete_order', methods=['POST'])
def complete_order():
    return redirect(url_for('index'))

# ------------------------------
# ADMIN PLACEHOLDERS
# ------------------------------

@app.route('/admin')
def admin_dashboard():
    return render_template('admin-dashboard.html')

@app.route('/admin/inventory')
def admin_inventory():
    return render_template('admin-inventory.html')

@app.route('/admin/orders')
def admin_orders():
    return render_template('admin-orders.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return render_template('admin-login.html')

@app.route('/admin/logout')
def admin_logout():
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
