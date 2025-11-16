from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QCheckBox, QScrollArea,
    QLineEdit, QMessageBox, QButtonGroup, QRadioButton, QComboBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from .product_list import ProductListItem
from .invoice_table import InvoiceTable
from .app_menu_bar import AppMenuBar
from pdf.invoice_generator import InvoiceGenerator
from database.db import get_connection
from gui.custumer_window import CustomerWindow
from gui.business_info_window import BusinessInfoWindow
import csv


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
        self.table.parent_window = self
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.table)

        scroll.setWidget(container)

        right_layout.addWidget(scroll)

        # ---- Total summary labels ----
        self.sum_netto_label = QLabel("Zwischensumme (Netto): 0.00 €")
        self.sum_netto_label.setAlignment(Qt.AlignRight)

        self.sum_tax_label = QLabel("MwSt (19%): 0.00 €")
        self.sum_tax_label.setAlignment(Qt.AlignRight)

        self.sum_brutto_label = QLabel("Gesamtsumme (Brutto): 0.00 €")
        self.sum_brutto_label.setAlignment(Qt.AlignRight)

        right_layout.addWidget(self.sum_netto_label)
        right_layout.addWidget(self.sum_tax_label)
        right_layout.addWidget(self.sum_brutto_label)

        # ---- Customer selection ----
        customer_select_layout = QVBoxLayout()
        customer_label = QLabel("Kunde auswählen:")
        customer_select_layout.addWidget(customer_label)

        self.customer_sort_group = QButtonGroup(self)
        self.sort_by_id = QRadioButton("Sortieren nach ID")
        self.sort_by_name = QRadioButton("Sortieren nach Name")
        self.sort_by_name.setChecked(True)

        self.customer_sort_group.addButton(self.sort_by_id)
        self.customer_sort_group.addButton(self.sort_by_name)

        sort_buttons_layout = QHBoxLayout()
        sort_buttons_layout.addWidget(self.sort_by_id)
        sort_buttons_layout.addWidget(self.sort_by_name)

        self.customer_combo = QComboBox()
        self.customer_combo.setPlaceholderText("Kunde auswählen...")

        customer_select_layout.addLayout(sort_buttons_layout)
        customer_select_layout.addWidget(self.customer_combo)

        right_layout.addLayout(customer_select_layout)

        # ---- Rabatt (Discount) section ----
        rabatt_layout = QVBoxLayout()
        rabatt_label = QLabel("Rabatt:")
        rabatt_layout.addWidget(rabatt_label)

        self.rabatt_checkbox = QCheckBox("Rabatt aktivieren")
        rabatt_layout.addWidget(self.rabatt_checkbox)

        self.rabatt_mode_combo = QComboBox()
        self.rabatt_mode_combo.addItems(["Rabattbetrag (€)", "Zielbetrag (€ inkl. MwSt)"])
        self.rabatt_mode_combo.setEnabled(False)
        rabatt_layout.addWidget(self.rabatt_mode_combo)

        self.rabatt_value_spin = QDoubleSpinBox()
        self.rabatt_value_spin.setPrefix("€ ")
        self.rabatt_value_spin.setMaximum(9999999.99)
        self.rabatt_value_spin.setDecimals(2)
        self.rabatt_value_spin.setValue(0.00)
        self.rabatt_value_spin.setEnabled(False)
        rabatt_layout.addWidget(self.rabatt_value_spin)

        # Enable/disable rabatt controls when checkbox toggled
        self.rabatt_checkbox.toggled.connect(self.rabatt_mode_combo.setEnabled)
        self.rabatt_checkbox.toggled.connect(self.rabatt_value_spin.setEnabled)

        right_layout.addLayout(rabatt_layout)

        # Connect sorting and selection
        self.sort_by_id.toggled.connect(self.load_customers)
        self.sort_by_name.toggled.connect(self.load_customers)
        self.customer_combo.currentIndexChanged.connect(self.on_customer_selected)

        # Combine layouts
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 5)

        # ---- Menu Bar ----
        self.menu_bar = AppMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self._connect_menu_signals()

        # ---- Load data ----
        self.load_products()
        self.load_customers()

        # ---- Invoice Generator ----
        self.invoice_generator = InvoiceGenerator()
        self._load_logo_from_db()

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
        self.menu_bar.select_logo.connect(self.choose_logo)
        self.menu_bar.import_products.connect(self.import_products_from_csv)
        self.menu_bar.business_info.connect(self.open_business_info_window)

    # -------------------------------------------------------------
    # MENU ACTION HANDLERS
    # -------------------------------------------------------------
    def new_invoice(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.update_totals()

    def save_invoice(self):
        if not hasattr(self, 'selected_customer') or self.selected_customer is None:
            QMessageBox.warning(self, "Fehler", "Bitte zuerst Kunde auswählen.")
            return
        
        rabatt_mode = "Kein Rabatt"
        rabatt_value = 0.0
        if self.rabatt_checkbox.isChecked():
            rabatt_mode = self.rabatt_mode_combo.currentText()
            rabatt_value = self.rabatt_value_spin.value()

        self.invoice_generator.generate_invoice(
            table = self.table, 
            customer = self.selected_customer,
            parent = self,
            rabatt_mode = rabatt_mode,
            rabatt_value = rabatt_value
        )

    def load_invoice(self):
        self.invoice_generator.load_invoice(self.table, self)

        # Remove any "Rabatt" line from the table (should not be treated as a product)
        for row in range(self.table.rowCount() - 1, -1, -1):
            item = self.table.item(row, 0)
            if item and "rabatt" in item.text().lower():
                self.table.removeRow(row)

        # Select the correct customer (if available)
        if getattr(self.invoice_generator, "loaded_customer", None):
            self.select_customer_in_combobox(self.invoice_generator.loaded_customer["id"])

        # Apply Rabatt (if any), but always in "Rabattbetrag (€)" mode
        if getattr(self.invoice_generator, "loaded_rabatt", None):
            self.apply_rabatt(self.invoice_generator.loaded_rabatt)
        else:
            # Ensure default Rabatt mode
            self.rabatt_checkbox.setChecked(False)
            self.rabatt_mode_combo.setCurrentText("Rabattbetrag (€)")
            self.rabatt_value_spin.setValue(0.00)

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

    def load_customers(self):
        """Loads customers into the combo box, sorted by ID or Name."""
        conn = get_connection()
        c = conn.cursor()

        if self.sort_by_id.isChecked():
            c.execute("SELECT id, name FROM customers ORDER BY id ASC")
        else:
            c.execute("SELECT id, name FROM customers ORDER BY name COLLATE NOCASE ASC")

        customers = c.fetchall()
        conn.close()

        self.customer_combo.blockSignals(True)
        self.customer_combo.clear()

        for cust_id, name in customers:
            display_text = f"{cust_id} – {name}"
            self.customer_combo.addItem(display_text, userData={"id": cust_id, "name": name})

        self.customer_combo.blockSignals(False)

    def on_customer_selected(self, index):
        """Triggered when a customer is selected."""
        data = self.customer_combo.itemData(index)
        if data:
            self.selected_customer = {
                "id": data["id"],
                "name": data["name"],
                "contact_name": data.get("contact_name", ""),
                "address": data.get("address", ""),
                "zip_city": data.get("zip_city", "")
            }
        else:
            self.selected_customer = None

    def choose_logo(self):
        """Let the user choose an image and store it in DB as bytes."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Logo auswählen", "", "Bilder (*.png *.jpg *.jpeg *.bmp)")
        if not file_path:
            return

        with open(file_path, "rb") as f:
            image_data = f.read()

        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('logo', ?)", (image_data,))
        conn.commit()
        conn.close()

        self.invoice_generator.set_logo_bytes(image_data)
        QMessageBox.information(self, "Gespeichert", "Das Logo wurde in der Datenbank gespeichert.")

    def _load_logo_from_db(self):
        """Load logo bytes from DB into memory on startup."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key='logo'")
        row = c.fetchone()
        conn.close()

        if row and row[0]:
            self.invoice_generator.set_logo_bytes(row[0])

    def select_customer_in_combobox(self, customer_id: int):
        """Selects the customer with the given ID in the combo box."""
        for index in range(self.customer_combo.count()):
            data = self.customer_combo.itemData(index)
            if data and data.get("id") == customer_id:
                self.customer_combo.setCurrentIndex(index)
                # Trigger the selection so self.selected_customer is updated
                self.on_customer_selected(index)
                return
        # If no matching ID is found
        QMessageBox.warning(self, "Kunde nicht gefunden", f"Kunde mit ID {customer_id} wurde nicht gefunden.")

    def apply_rabatt(self, rabatt_data: dict):
        """Applies the loaded discount data from the invoice file."""
        if not rabatt_data:
            self.rabatt_checkbox.setChecked(False)
            self.rabatt_value_spin.setValue(0.00)
            return

        # Always use "Rabattbetrag (€)" mode when loading
        self.rabatt_checkbox.setChecked(True)
        self.rabatt_mode_combo.setCurrentText("Rabattbetrag (€)")
        self.rabatt_value_spin.setValue(rabatt_data.get("value", 0.00))

    def import_products_from_csv(self):
        """Import products (name, price) from a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Produkte aus CSV importieren",
            "",
            "CSV-Dateien (*.csv)"
        )
        if not file_path:
            return

        added_count = 0
        try:
            conn = get_connection()
            c = conn.cursor()

            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if len(row) != 2:
                        continue
                    name, price_str = row
                    name = name.strip().strip('"')
                    try:
                        price = float(price_str)
                    except ValueError:
                        continue

                    # Skip duplicates
                    c.execute("SELECT COUNT(*) FROM products WHERE LOWER(name)=LOWER(?)", (name,))
                    if c.fetchone()[0] == 0:
                        c.execute("INSERT INTO products (name, price) VALUES (?, ?)", (name, price))
                        added_count += 1

            conn.commit()
            conn.close()

            self.load_products()
            QMessageBox.information(
                self,
                "Import abgeschlossen",
                f"{added_count} Produkte wurden erfolgreich hinzugefügt."
            )

        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Import", f"Es gab ein Problem:\n{e}")

    def open_business_info_window(self):
        self.business_window = BusinessInfoWindow()
        self.business_window.show()

