from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt
from database.db import get_connection


class BusinessInfoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Firmeninformationen")
        self.setFixedWidth(500)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.company_name = QLineEdit()
        self.address = QLineEdit()
        self.vat_id = QLineEdit()
        self.phone = QLineEdit()
        self.fax = QLineEdit()
        self.email = QLineEdit()
        self.website = QLineEdit()
        self.bank_name = QLineEdit()
        self.iban = QLineEdit()
        self.bic = QLineEdit()
        self.account_holder = QLineEdit()

        form.addRow("Firmenname:", self.company_name)
        form.addRow("Adresse:", self.address)
        form.addRow("USt-IdNr:", self.vat_id)
        form.addRow("Telefon:", self.phone)
        form.addRow("Fax:", self.fax)
        form.addRow("E-Mail:", self.email)
        form.addRow("Webseite:", self.website)
        form.addRow("Bankname:", self.bank_name)
        form.addRow("IBAN:", self.iban)
        form.addRow("BIC:", self.bic)
        form.addRow("Kontoinhaber:", self.account_holder)

        layout.addLayout(form)

        self.save_button = QPushButton("Speichern")
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_button, alignment=Qt.AlignRight)

        self.load_data()

    # -----------------------------
    # LOAD EXISTING DATA
    # -----------------------------
    def load_data(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM business_info WHERE id = 1")
        row = c.fetchone()
        conn.close()

        if row:
            (_, company_name, address, vat_id, phone, fax, email,
             website, bank_name, iban, bic, account_holder) = row

            self.company_name.setText(company_name or "")
            self.address.setText(address or "")
            self.vat_id.setText(vat_id or "")
            self.phone.setText(phone or "")
            self.fax.setText(fax or "")
            self.email.setText(email or "")
            self.website.setText(website or "")
            self.bank_name.setText(bank_name or "")
            self.iban.setText(iban or "")
            self.bic.setText(bic or "")
            self.account_holder.setText(account_holder or "")

    # -----------------------------
    # SAVE DATA
    # -----------------------------
    def save_data(self):
        conn = get_connection()
        c = conn.cursor()

        c.execute("""
            INSERT OR REPLACE INTO business_info (
                id, company_name, address, vat_id, phone, fax, email,
                website, bank_name, iban, bic, account_holder
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.company_name.text(),
            self.address.text(),
            self.vat_id.text(),
            self.phone.text(),
            self.fax.text(),
            self.email.text(),
            self.website.text(),
            self.bank_name.text(),
            self.iban.text(),
            self.bic.text(),
            self.account_holder.text()
        ))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Gespeichert", "Firmendaten erfolgreich gespeichert!")
