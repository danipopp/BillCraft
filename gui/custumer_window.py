from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout, QInputDialog, QMessageBox
from database.custumer_repository import CustomerRepository

class CustomerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kundenverwaltung")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Id","Name", "E-Mail", "Telefon", "Stadt", "Land"])
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Kunden hinzufügen")
        refresh_btn = QPushButton("Aktualisieren")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        add_btn.clicked.connect(self.add_customer)
        refresh_btn.clicked.connect(self.load_customers)
        self.load_customers()

    def load_customers(self):
        customers = CustomerRepository.get_all_customers()
        self.table.setRowCount(0)
        for cust in customers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(cust["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(cust["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(cust["email"]))
            self.table.setItem(row, 3, QTableWidgetItem(cust["phone"]))
            self.table.setItem(row, 4, QTableWidgetItem(cust["city"]))
            self.table.setItem(row, 5, QTableWidgetItem(cust["country"]))

    def add_customer(self):
        name, ok = QInputDialog.getText(self, "Neuer Kunde", "Kundenname eingeben:")
        if not ok or not name.strip():
            return

        email, _ = QInputDialog.getText(self, "E-Mail", "E-Mail-Adresse eingeben:")
        phone, _ = QInputDialog.getText(self, "Telefon", "Telefonnummer eingeben:")
        city, _ = QInputDialog.getText(self, "Stadt", "Stadt eingeben:")
        country, _ = QInputDialog.getText(self, "Land", "Land eingeben:")

        CustomerRepository.add_customer({
            "name": name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "city": city.strip(),
            "country": country.strip()
        })

        QMessageBox.information(self, "Erfolg", f"Kunde '{name}' wurde hinzugefügt.")
        self.load_customers()
