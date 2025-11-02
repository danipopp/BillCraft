from database.db import get_connection

class CustomerRepository:
    @staticmethod
    def add_customer(name, email="", phone="", address="", zip_code="", city="", country="", tax_number="", notes=""):
        conn = get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO customers (name, email, phone, address, zip_code, city, country, tax_number, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, address, zip_code, city, country, tax_number, notes))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_customers():
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM customers ORDER BY name ASC")
        rows = c.fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_customer_by_name(name):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM customers WHERE LOWER(name)=LOWER(?)", (name,))
        customer = c.fetchone()
        conn.close()
        return customer
