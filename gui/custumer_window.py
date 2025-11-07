from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
    QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QMessageBox
)
from database.custumer_repository import CustomerRepository

class CustomerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kundenverwaltung")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        # --- FORM SECTION ---
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.contact_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()
        self.zip_input = QLineEdit()
        self.city_input = QLineEdit()
        self.country_input = QLineEdit()
        self.tax_input = QLineEdit()
        self.notes_input = QTextEdit()

        form_layout.addRow("Name*", self.name_input)
        form_layout.addRow("Ansprechpartner", self.contact_input)
        form_layout.addRow("E-Mail", self.email_input)
        form_layout.addRow("Telefon", self.phone_input)
        form_layout.addRow("Adresse", self.address_input)
        form_layout.addRow("PLZ", self.zip_input)
        form_layout.addRow("Stadt", self.city_input)
        form_layout.addRow("Land", self.country_input)
        form_layout.addRow("Steuernummer", self.tax_input)
        form_layout.addRow("Notizen", self.notes_input)

        layout.addLayout(form_layout)

        # --- BUTTONS ---
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Kunden hinzufügen")
        refresh_btn = QPushButton("Aktualisieren")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        add_btn.clicked.connect(self.add_customer)
        refresh_btn.clicked.connect(self.load_customers)

        # --- TABLE SECTION ---
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Kontaktperson", "E-Mail", "Telefon", "Stadt", "Land"
        ])
        layout.addWidget(self.table)

        self.load_customers()

    # --- METHODS ---
    def add_customer(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehler", "Der Name darf nicht leer sein.")
            return

        customer_data = {
            "name": name,
            "contact_name": self.contact_input.text().strip(),
            "email": self.email_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.text().strip(),
            "zip_code": self.zip_input.text().strip(),
            "city": self.city_input.text().strip(),
            "country": self.country_input.text().strip(),
            "tax_number": self.tax_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
        }

        CustomerRepository.add_customer(customer_data)
        QMessageBox.information(self, "Erfolg", f"Kunde '{name}' wurde hinzugefügt.")
        self.load_customers()
        self.clear_form()

    def load_customers(self):
        customers = CustomerRepository.get_all_customers()
        self.table.setRowCount(0)
        for cust in customers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(cust["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(cust["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(cust.get("contact_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(cust["email"]))
            self.table.setItem(row, 4, QTableWidgetItem(cust["phone"]))
            self.table.setItem(row, 5, QTableWidgetItem(cust["city"]))
            self.table.setItem(row, 6, QTableWidgetItem(cust["country"]))

    def clear_form(self):
        """Reset all input fields."""
        for widget in [
            self.name_input, self.contact_input, self.email_input, self.phone_input,
            self.address_input, self.zip_input, self.city_input, self.country_input,
            self.tax_input
        ]:
            widget.clear()
        self.notes_input.clear()
