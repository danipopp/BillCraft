import sqlite3
from database.db import get_connection

class CustomerRepository:
    @staticmethod
    def add_customer(customer_data):
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO customers (
                name, contact_name, email, phone,
                address, zip_code, city, country,
                tax_number, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_data.get("name"),
            customer_data.get("contact_name"),
            customer_data.get("email"),
            customer_data.get("phone"),
            customer_data.get("address"),
            customer_data.get("zip_code"),
            customer_data.get("city"),
            customer_data.get("country"),
            customer_data.get("tax_number"),
            customer_data.get("notes"),
        ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_customers():
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT id, name, contact_name, email, phone, city, country
            FROM customers
            ORDER BY id DESC
        """)
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_customer_by_id(customer_id):
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
