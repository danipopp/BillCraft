import json
import sqlite3
from PySide6.QtCore import Qt
from datetime import date
from PySide6.QtWidgets import QFileDialog, QMessageBox, QSpinBox, QDoubleSpinBox, QTableWidgetItem
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from functools import partial
from database.db import get_connection
import os   
import io

class InvoiceGenerator:
    def __init__(self, db_path="invoices.db"):
        self.last_folder = os.getcwd()
        self.logo_path = None
        self.logo_bytes = None
        self.db_path = db_path

    def set_logo(self, path):
        self.logo_path = path

    def set_logo_bytes(self, data):
        self.logo_bytes = data

    # ----------------------------------------------------------
    # GENERATE PDF INVOICE
    # ----------------------------------------------------------
    def generate_invoice(self, table, customer=None, parent=None, rabatt_mode=None, rabatt_value=0.0):
        file_path, _ = QFileDialog.getSaveFileName(
            parent, "Rechnung speichern", os.path.join(self.last_folder, "Rechnung.pdf"), "PDF-Dateien (*.pdf)"
        )
        if not file_path:
            return

        self.last_folder = os.path.dirname(file_path)
        pdf = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        y = height - 50 * mm

        buissiness = self.load_bussiness_info()

        # --- Company Header
        company_name = buissiness["company_name"]
        company_address = buissiness["address"]
        company_city_id = buissiness["city_id"]

        # --- Logo path
        logo_width = 35 * mm
        margin = 25 * mm

        def draw_logo(img_source):
            img = ImageReader(img_source)
            iw, ih = img.getSize()
            aspect = ih / iw
            logo_height = logo_width * aspect
            x_pos = A4[0] - logo_width - margin
            y_pos = A4[1] - logo_height - margin
            pdf.drawImage(img_source, x_pos, y_pos, width=logo_width, height=logo_height, mask='auto')

        try:
            if self.logo_bytes:
                draw_logo(ImageReader(io.BytesIO(self.logo_bytes)))
            elif self.logo_path and os.path.exists(self.logo_path):
                draw_logo(self.logo_path)
        except Exception as e:
            print(f"⚠️ Error loading logo from bytes: {e}")

        y -= 5 * mm

        # --- Company Info
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.grey)
        pdf.drawString(25 * mm, y, company_name + " | " + company_address + " | " + company_city_id)
        pdf.setFillColor(colors.black)

        y -= 15 * mm

        # --- Load Customer Data
        if customer and "id" in customer:
            full_customer = self.get_customer_by_id(customer["id"])
        else:
            full_customer = None

        if full_customer:
            client_company = full_customer["name"]
            client_name = full_customer["contact_name"]
            client_address = full_customer["address"]
            client_zip = full_customer["zip_code"]
            client_city = full_customer["city"]
            client_id = full_customer["id"]
        else:
            client_company = ""
            client_name = ""
            client_address = ""
            client_zip = ""
            client_city = ""
            client_id = ""

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(25 * mm, y, client_company)
        pdf.setFont("Helvetica", 10)
        pdf.drawString(25 * mm, y - 5 * mm, client_name)
        pdf.drawString(25 * mm, y - 10 * mm, client_address)
        pdf.drawString(25 * mm, y - 15 * mm, client_zip)
        pdf.drawString(25 * mm, y - 20 * mm, client_city)
        y -= 30 * mm

        customer_number = str(client_id).zfill(12) if client_id else "000000000000"

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(width - 95 * mm, y, f"Kundennummer: ")
        pdf.drawString(width - 45 * mm, y, f"Datum:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(width - 95 * mm, y - 5 * mm, f"{customer_number}")
        pdf.drawString(width - 45 * mm, y - 5 * mm, f"{date.today().strftime('%d.%m.%Y')}")
        y -= 20 * mm

        # --- Header
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(25 * mm, y, "Rechnung Nr. 1001")

        y -= 20 * mm

        # --- Table Header
        pdf.setFont("Helvetica-Bold", 10)
        col_positions = [25 * mm, 50 * mm, 110 * mm, 140 * mm, 170 * mm]
        headers = ["Pos", "Produkt", "Menge", "Einzel ( € )", "Gesamt ( € )"]
        for i, header in enumerate(headers):
            pdf.drawString(col_positions[i], y, header)
        y -= 5 * mm
        pdf.line(25 * mm, y, width - 25 * mm, y)
        y -= 8 * mm

        # --- Table Content
        pdf.setFont("Helvetica", 9)
        total_net = 0.0
        items = []

        for i in range(table.rowCount()):
            product = table.item(i, 0).text() if table.item(i, 0) else ""
            qty_widget = table.cellWidget(i, 1)
            price_widget = table.cellWidget(i, 2)
            sum_item = table.item(i, 3)

            qty = qty_widget.value() if isinstance(qty_widget, QSpinBox) else 0
            price = price_widget.value() if isinstance(price_widget, QDoubleSpinBox) else 0.0
            total = float(sum_item.text()) if sum_item else qty * price
            total_net += total

            pdf.drawString(col_positions[0], y, str(i + 1))
            pdf.drawString(col_positions[1], y, product)
            pdf.drawRightString(col_positions[2] + 15 * mm, y, str(qty))
            pdf.drawRightString(col_positions[3] + 15 * mm, y, f"{price:.2f}")
            pdf.drawRightString(col_positions[4] + 15 * mm, y, f"{total:.2f}")
            y -= 6 * mm

            items.append({
                "product": product,
                "quantity": qty,
                "price": price,
                "sum": total
            })

        if rabatt_mode and rabatt_value > 0:
            if "Rabattbetrag" in rabatt_mode:  # fixed amount €
                rabatt_applied = rabatt_value
            elif "Zielbetrag" in rabatt_mode:  # Zielbetrag brutto -> recalc netto
                ziel_netto = rabatt_value / 1.19
                rabatt_applied = max(0, total_net - ziel_netto)
            else:
                rabatt_applied = 0.0

            if rabatt_applied > 0:
                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawString(col_positions[1], y, "Rabatt")
                pdf.drawRightString(col_positions[4] + 15 * mm, y, f"-{rabatt_applied:.2f}")
                y -= 6 * mm
                total_net = max(0, total_net - rabatt_applied)
        else:
            rabatt_applied = 0.0

        # --- Totals
        y -= 4 * mm
        pdf.line(25 * mm, y, width - 25 * mm, y)
        y -= 8 * mm

        tax = total_net * 0.19
        total_gross = total_net + tax

        pdf.setFont("Helvetica", 10)
        pdf.drawRightString(width - 55 * mm, y, "Summe Netto:")
        pdf.drawRightString(width - 25 * mm, y, f"{total_net:.2f}")
        y -= 6 * mm

        pdf.drawRightString(width - 55 * mm, y, "MwSt (19%):")
        pdf.drawRightString(width - 25 * mm, y, f"{tax:.2f}")
        y -= 6 * mm

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawRightString(width - 55 * mm, y, "Gesamtbetrag:")
        pdf.drawRightString(width - 25 * mm, y, f"{total_gross:.2f}")
        y -= 10 * mm

        pdf.setFont("Helvetica", 9)
        pdf.setFillColor(colors.grey)
        pdf.drawString(25 * mm, y, "Vielen Dank für Ihren Einkauf!")
        pdf.setFillColor(colors.black)

        self.draw_footer(pdf, buissiness)

        pdf.showPage()
        pdf.save()

        json_data = json.dumps({
            "date": date.today().isoformat(),
            "items": items,
            "rabatt": {
                "mode": rabatt_mode,
                "value": rabatt_applied
            },
            "customer": customer
        })

        with open(file_path, "ab") as f:
            f.write(b"\n%%INVOICE_JSON_START%%")
            f.write(json_data.encode("utf-8"))
            f.write(b"%%INVOICE_JSON_END%%")

        QMessageBox.information(parent, "Erfolg", f"Rechnung gespeichert unter:\n{file_path}")

    # ----------------------------------------------------------
    # LOAD PDF WITH EMBEDDED JSON
    # ----------------------------------------------------------
    def load_invoice(self, table, parent=None):
        file_path, _ = QFileDialog.getOpenFileName(parent, "Rechnung laden", self.last_folder, "PDF-Dateien (*.pdf)")
        if not file_path:
            return

        self.last_folder = os.path.dirname(file_path)

        with open(file_path, "rb") as f:
            content = f.read()

        start = content.find(b"%%INVOICE_JSON_START%%")
        end = content.find(b"%%INVOICE_JSON_END%%")

        if start == -1 or end == -1:
            QMessageBox.warning(parent, "Fehler", "Keine eingebetteten Daten gefunden.")
            return

        json_data = content[start + len(b"%%INVOICE_JSON_START%%"): end]
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            QMessageBox.warning(parent, "Fehler", "Ungültige JSON-Daten.")
            return

        # --- Load into Table
        table.setRowCount(0)
        for item in data["items"]:
            name = item["product"]
            qty = int(item["quantity"])
            price = float(item["price"])
            table.add_product(name, price)

            # Set correct quantity (since add_product defaults to 1)
            last_row = table.rowCount() - 1
            qty_box = table.cellWidget(last_row, 1)
            if qty_box:
                qty_box.setValue(qty)


        rabatt_info = data.get("rabatt")
        #if rabatt_info and rabatt_info.get("value", 0) > 0:
        #    row = table.rowCount()
        #    table.insertRow(row)
        #    table.setItem(row, 0, QTableWidgetItem("Rabatt"))
        #    table.setItem(row, 1, QTableWidgetItem(""))
        #    table.setItem(row, 2, QTableWidgetItem(""))
        #    table.setItem(row, 3, QTableWidgetItem(f"-{rabatt_info['value']:.2f}"))

        # Return Rabatt and Customer info for main window
        self.loaded_rabatt = rabatt_info
        self.loaded_customer = data.get("customer")

    def _update_row_sum(self, table, row):
        """Recalculate a single row's total and update the Gesamtsumme label if available."""
        qty_widget = table.cellWidget(row, 1)
        price_widget = table.cellWidget(row, 2)
        if qty_widget and price_widget:
            total = qty_widget.value() * price_widget.value()
            table.item(row, 3).setText(f"{total:.2f}")
        
        # If your table has a method to update total sum (like table.update_totals), call it
        if hasattr(table, "update_totals"):
            table.update_totals()

    def get_customer_by_id(self, customer_id):
        """Fetch full customer data from the database by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, contact_name, address, zip_code, city 
                FROM customers WHERE id = ?
            """, (customer_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "contact_name": row[2] or "",
                    "address": row[3] or "",
                    "zip_code": row[4] or "",
                    "city": row[5] or ""
                }
            return None
        except Exception as e:
            print(f"⚠️ Error loading customer: {e}")
            return None
        
    def load_bussiness_info(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT company_name, address, city_id, vat_id, phone, fax, email, website, bank_name, iban, bic, account_holder FROM business_info WHERE id = 1")
        row = c.fetchone()
        conn.close()

        if row:
            return {
                "company_name": row[0] or "",
                "address": row[1] or "",
                "city_id": row[2] or "",
                "vat_id": row[3] or "",
                "phone": row[4] or "",
                "fax": row[5] or "",
                "email": row[6] or "",
                "website": row[7] or "",
                "bank_name": row[8] or "",
                "iban": row[9] or "",
                "bic": row[10] or "",
                "account_holder": row[11] or "",
            }
        
        return {
            "company_name": "",
            "address": "",
            "city_id": "",
            "vat_id": "",
            "phone": "",
            "fax": "",
            "email": "",
            "website": "",
            "bank_name": "",
            "iban": "",
            "bic": "",
            "account_holder": "",
        }

    def draw_footer(self, pdf, business_info):
        """
        Draw footer with company info in multiple columns, only on the last page.
        """
        width, height = A4
        footer_y = 20 * mm  # distance from bottom
        col1_x = 25 * mm
        col2_x = 75 * mm
        col3_x = 125 * mm
        col4_x = 175 * mm

        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.grey)

        # Column 1
        pdf.drawString(col1_x, footer_y + 30, business_info["company_name"])
        pdf.drawString(col1_x, footer_y + 20, business_info["address"])
        pdf.drawString(col1_x, footer_y + 10, business_info["city_id"])
        pdf.drawString(col1_x, footer_y, f"Ust-IdNr.: {business_info['vat_id']}")

        # Column 2
        pdf.drawString(col2_x, footer_y + 30, f"Tel.: {business_info['phone']}")
        pdf.drawString(col2_x, footer_y + 20, f"Fax: {business_info['fax']}")
        pdf.drawString(col2_x, footer_y + 10, f"E-Mail: {business_info['email']}")
        pdf.drawString(col2_x, footer_y, f"Web: {business_info['website']}")

        # Column 3
        pdf.drawString(col3_x, footer_y + 30, business_info["bank_name"])
        pdf.drawString(col3_x, footer_y + 20, f"IBAN: {business_info['iban']}")
        pdf.drawString(col3_x, footer_y + 10, f"BIC: {business_info['bic']}")
        pdf.drawString(col3_x, footer_y, f"Kto. Inh.: {business_info['account_holder']}")

        # Column 4 (optional)
        pdf.drawString(col4_x, footer_y + 30, "Powered by YourAppName")

        pdf.setFillColor(colors.black)
