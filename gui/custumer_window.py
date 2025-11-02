# gui/customer_window.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout
from database.custumer_repository import CustomerRepository

class CustomerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kundenverwaltung")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "E-Mail", "Telefon", "Stadt", "Land"])
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Kunden hinzufügen")
        refresh_btn = QPushButton("Aktualisieren")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        refresh_btn.clicked.connect(self.load_customers)
        self.load_customers()

    def load_customers(self):
        customers = CustomerRepository.get_all_customers()
        self.table.setRowCount(0)
        for cust in customers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(cust["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(cust["email"]))
            self.table.setItem(row, 2, QTableWidgetItem(cust["phone"]))
            self.table.setItem(row, 3, QTableWidgetItem(cust["city"]))
            self.table.setItem(row, 4, QTableWidgetItem(cust["country"]))
