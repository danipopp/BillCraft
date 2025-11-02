import sqlite3

DB_FILE = "invoices.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def create_tables():
    conn = get_connection()
    c = conn.cursor()

    # Customers (final version)
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            zip_code TEXT,
            city TEXT,
            country TEXT,
            tax_number TEXT,
            notes TEXT
        )
    ''')

    # Products
    c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        tax_rate REAL DEFAULT 0.19
    )
    ''')

    # Invoices
    c.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        total REAL NOT NULL,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )
    ''')

    # Invoice lines
    c.execute('''
    CREATE TABLE IF NOT EXISTS invoice_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    ''')

    conn.commit()
    conn.close()
