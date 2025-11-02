from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt
from .product_list import ProductListItem
from .invoice_table import InvoiceTable
from .app_menu_bar import AppMenuBar
from pdf.invoice_generator import InvoiceGenerator
from database.db import get_connection
from gui.custumer_window import CustomerWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lokales Rechnungsprogramm")
        self.setGeometry(200, 200, 950, 550)

        # ---- Central Widget ----
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # ---- Left: Product List ----
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

        # ---- Right: Invoice Table ----
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Rechnungstabelle:"))
        self.table = InvoiceTable()
        right_layout.addWidget(self.table)

        self.table.total_label = QLabel("Gesamtsumme: 0.00 €")
        self.table.total_label.setAlignment(Qt.AlignRight)
        right_layout.addWidget(self.table.total_label)

        # Combine layouts
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 5)

        # ---- Menu Bar ----
        self.menu_bar = AppMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self._connect_menu_signals()

        # ---- Load data ----
        self.load_products()

        # ---- Invoice Generator ----
        self.invoice_generator = InvoiceGenerator()

    # -------------------------------------------------------------
    # MENU SIGNAL CONNECTIONS
    # -------------------------------------------------------------
    def _connect_menu_signals(self):
        self.menu_bar.new_invoice.connect(self.new_invoice)
        self.menu_bar.save_invoice.connect(self.save_invoice)
        self.menu_bar.load_invoice.connect(self.load_invoice)
        self.menu_bar.exit_app.connect(self.close)
        self.menu_bar.refresh_products.connect(self.load_products)
        self.menu_bar.import_products.connect(self.import_products)
        self.menu_bar.export_products.connect(self.export_products)
        self.menu_bar.customer_window.connect(self.open_customer_window)

    # -------------------------------------------------------------
    # MENU ACTION HANDLERS
    # -------------------------------------------------------------
    def new_invoice(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.update_totals()

    def save_invoice(self):
        self.invoice_generator.generate_invoice(self.table, self)

    def load_invoice(self):
        self.invoice_generator.load_invoice(self.table, self)

    def open_customer_window(self):
        self.customer_window = CustomerWindow()
        self.customer_window.show()

    def import_products(self):
        QMessageBox.information(self, "Importieren", "Produktimport folgt.")

    def export_products(self):
        QMessageBox.information(self, "Exportieren", "Produktexport folgt.")

    # -------------------------------------------------------------
    # PRODUCT MANAGEMENT
    # -------------------------------------------------------------
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
        confirm = QMessageBox.question(
            self, "Löschen bestätigen",
            f"Soll das Produkt '{name}' wirklich gelöscht werden?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.No:
            return

        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE LOWER(name)=LOWER(?)", (name,))
        conn.commit()
        conn.close()
        self.load_products()

    def add_product(self):
        name = self.name_input.text().strip()
        price_text = self.price_input.text().strip()
        if not name or not price_text:
            QMessageBox.warning(self, "Fehler", "Bitte beide Felder ausfüllen.")
            return
        try:
            price = float(price_text)
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Preis muss eine Zahl sein.")
            return

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM products WHERE LOWER(name)=LOWER(?)", (name,))
        if c.fetchone()[0] > 0:
            QMessageBox.warning(self, "Duplikat", f"'{name}' existiert bereits.")
            conn.close()
            return

        c.execute("INSERT INTO products (name, price) VALUES (?, ?)", (name, price))
        conn.commit()
        conn.close()

        self.name_input.clear()
        self.price_input.clear()
        self.load_products()

    def update_product_price(self, name, new_price):
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE products SET price=? WHERE LOWER(name)=LOWER(?)", (new_price, name.lower()))
        conn.commit()
        conn.close()

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text().lower() == name.lower():
                price_widget = self.table.cellWidget(row, 2)
                if price_widget:
                    price_widget.setValue(new_price)
                    break
        self.table.update_totals()

    def add_product_to_table(self, item):
        row_index = self.product_list.row(item)
        product_id, name, price = self.products[row_index]
        self.table.add_product(name, price)
