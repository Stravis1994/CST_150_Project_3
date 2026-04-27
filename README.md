# CST 150 - Project 3 (TCG Store)

Flask web app for a trading card store with:
- Customer storefront (browse products, cart, checkout)
- Admin area (dashboard, inventory, orders)
- MySQL-backed product/order data

## Tech Stack

- Python 3.13+
- Flask
- MySQL Server 8+
- mysql-connector-python
- argon2-cffi

## 1. Clone and Open

1. Clone the repository.
2. Open the project folder in VS Code.

## 2. Create and Activate a Virtual Environment

From the project root:

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Python Dependencies

Use either approach below.

Using pip:

```bash
pip install flask flask-sqlalchemy mysql-connector-python argon2-cffi
```

Using pyproject (if you use uv):

```bash
uv sync
```

## 4. Set Up MySQL

This project expects a local MySQL database named tcg_store.

Code defaults in main.py are:
- host: localhost
- user: root
- password: (empty string)
- database: tcg_store

If your local MySQL credentials are different, update the get_db_connection function in main.py before starting the app.

## 5. Create and Seed the Database

Run these SQL files in this order:

1. Database/Create_Database.sql
2. Database/Products.sql
3. Database/Inventory.sql
4. Database/Customers.sql
5. Database/Orders.sql
6. Database/OrderItems.sql
7. Database/Admin.sql

Example (MySQL CLI):

```bash
mysql -u root -p < Database/Create_Database.sql
mysql -u root -p tcg_store < Database/Products.sql
mysql -u root -p tcg_store < Database/Inventory.sql
mysql -u root -p tcg_store < Database/Customers.sql
mysql -u root -p tcg_store < Database/Orders.sql
mysql -u root -p tcg_store < Database/OrderItems.sql
mysql -u root -p tcg_store < Database/Admin.sql
```

Notes:
- Create_Database.sql drops and recreates the database.
- If you run it again, you will lose seeded data and need to re-run all seed scripts.

## 6. Run the Application

From the project root:

```bash
python main.py
```

Then open:
- Storefront: http://127.0.0.1:5000/
- Admin Login: http://127.0.0.1:5000/admin/login

## 7. Admin Login

The seed script creates username admin1 in the Admin table.

The password is stored as an Argon2 hash in Database/Admin.sql. If you do not know the original plain-text password, generate a new hash and update the row directly.

Example hash generation:

```bash
python -c "from argon2 import PasswordHasher; print(PasswordHasher().hash('ChangeMe123!'))"
```

Then in MySQL:

```sql
UPDATE Admin
SET password_hash = 'paste_generated_hash_here'
WHERE username = 'admin1';
```

## 8. Common Issues

MySQL connection error:
- Confirm MySQL server is running.
- Confirm username/password/host/database in main.py match your local setup.

Module import errors:
- Re-activate your virtual environment.
- Re-run dependency install.

No products showing:
- Verify all SQL seed scripts ran successfully and in order.

## Project Structure

Key paths:
- main.py: Flask app and routes
- templates/: Jinja templates for storefront/admin pages
- static/: CSS, JS, and product images
- Database/: schema and seed scripts

## Development Notes

- Flask runs in debug mode by default in main.py.
- A local SQLite file may appear under instance/store.db due to Flask-SQLAlchemy config, but primary app data here is read from MySQL.
