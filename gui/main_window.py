from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QMessageBox
from .product_list import ProductListItem
from .invoice_table import InvoiceTable
from database.db import get_connection

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local Invoicing App")
        self.setGeometry(200,200,950,550)

        main_layout = QHBoxLayout(self)

        # Left: Products
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Produkte:"))

        self.product_list = QListWidget()
        self.product_list.itemDoubleClicked.connect(self.add_product_to_table)
        left_layout.addWidget(self.product_list)

        left_layout.addWidget(QLabel("Neues Produkt hinzufügen:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Produktname")
        left_layout.addWidget(self.name_input)

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Preis (z.B. 19.99)")
        left_layout.addWidget(self.price_input)

        self.add_button = QPushButton("Produkt hinzufügen")
        self.add_button.clicked.connect(self.add_product)
        left_layout.addWidget(self.add_button)
        left_layout.addStretch()

        # Right: Invoice Table
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Rechnungstabelle:"))
        self.table = InvoiceTable()
        right_layout.addWidget(self.table)
        self.table.total_label = QLabel("Gesamtsumme: 0.00 €")
        right_layout.addWidget(self.table.total_label)

        main_layout.addLayout(left_layout,3)
        main_layout.addLayout(right_layout,5)

        self.load_products()

    # ---------- Products ----------
    def load_products(self):
        self.product_list.clear()
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, name, price FROM products ORDER BY id DESC")
        self.products = c.fetchall()
        conn.close()

        for prod in self.products:
            product_id, name, price = prod
            item = QListWidgetItem()
            widget = ProductListItem(name, price, self.delete_product)
            widget.price_changed.connect(self.update_product_price)
            item.setSizeHint(widget.sizeHint())
            self.product_list.addItem(item)
            self.product_list.setItemWidget(item, widget)

    def delete_product(self, name):
        confirm = QMessageBox.question(self, "Löschen bestätigen", f"Soll das Produkt '{name}' wirklich gelöscht werden?", QMessageBox.Yes|QMessageBox.No)
        if confirm==QMessageBox.No:
            return
        conn = get_connection()
        c=conn.cursor()
        c.execute("DELETE FROM products WHERE LOWER(name)=LOWER(?)",(name,))
        conn.commit()
        conn.close()
        self.load_products()

    def add_product(self):
        name = self.name_input.text().strip()
        price_text = self.price_input.text().strip()
        if not name or not price_text:
            QMessageBox.warning(self,"Fehler","Bitte beide Felder ausfüllen.")
            return
        try:
            price = float(price_text)
        except ValueError:
            QMessageBox.warning(self,"Fehler","Preis muss eine Zahl sein.")
            return
        conn = get_connection()
        c=conn.cursor()
        c.execute("SELECT COUNT(*) FROM products WHERE LOWER(name)=LOWER(?)",(name,))
        if c.fetchone()[0]>0:
            QMessageBox.warning(self,"Duplikat",f"'{name}' existiert bereits.")
            conn.close()
            return
        c.execute("INSERT INTO products (name, price) VALUES (?,?)",(name,price))
        conn.commit()
        conn.close()
        self.name_input.clear()
        self.price_input.clear()
        self.load_products()

    # ---------- Add product to table ----------
    def add_product_to_table(self, item):
        row_index = self.product_list.row(item)
        product_id,name,price=self.products[row_index]
        self.table.add_product(name,price)


    def update_product_price(self, name, new_price):
        """Update price in DB and invoice table when edited in product list."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE products SET price=? WHERE LOWER(name)=LOWER(?)", (new_price, name.lower()))
        conn.commit()
        conn.close()

        # Update price in table if product already there
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text().lower() == name.lower():
                self.table.item(row, 2).setText(f"{new_price:.2f}")

        # Recalculate totals
        self.table.update_totals()
