import json
from PySide6.QtCore import Qt
from datetime import date
from PySide6.QtWidgets import QFileDialog, QMessageBox, QSpinBox, QDoubleSpinBox, QTableWidgetItem
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import os
import io

class InvoiceGenerator:
    def __init__(self):
        self.last_folder = os.getcwd()
        self.logo_path = None
        self.logo_bytes = None

    def set_logo(self, path):
        self.logo_path = path

    def set_logo_bytes(self, data):
        self.logo_bytes = data

    # ----------------------------------------------------------
    # GENERATE PDF INVOICE
    # ----------------------------------------------------------
    def generate_invoice(self, table, customer=None, parent=None):
        file_path, _ = QFileDialog.getSaveFileName(
            parent, "Rechnung speichern", os.path.join(self.last_folder, "Rechnung.pdf"), "PDF-Dateien (*.pdf)"
        )
        if not file_path:
            return

        self.last_folder = os.path.dirname(file_path)
        pdf = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        y = height - 50 * mm

        # --- Company Header
        company_name = "Musterfirma GmbH"
        company_address = "Hauptstraße 12, 12345 Musterstadt"
        logo_width = 35 * mm

        # --- Logo path
        if self.logo_bytes:
            try:
                # Wrap bytes in a buffer and create ImageReader
                buffer = io.BytesIO(self.logo_bytes)
                img = ImageReader(buffer)

                # Force consistent size and Y coordinate
                img_width = logo_width
                img_height = img_width  # square or adjust later if you want
                x_pos = width - img_width - 25 * mm
                y_pos = height - img_height - 25 * mm

                pdf.drawImage(
                    img,
                    x_pos,
                    y_pos,
                    width=img_width,
                    height=img_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )

            except Exception as e:
                print(f"⚠️ Error loading logo from bytes: {e}")
        elif self.logo_path and os.path.exists(self.logo_path):
            pdf.drawImage(self.logo_path, width - logo_width - 25 * mm, y - 10 * mm, width=logo_width, preserveAspectRatio=True)

        # --- Comapny Info (Top left)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(25 * mm, y, company_name)
        pdf.setFont("Helvetica", 10)
        pdf.drawString(25 * mm, y - 5 * mm, company_address)
        y -= 20 * mm

        # --- Client Info ---
        client_company = "Kunde GmbH"
        client_name = "Max Mustermann"
        client_address = "Beispielstraße 45"
        client_zip_city = "54321 Beispielstadt"
        client_id = "C-1024"

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(25 * mm, y, client_company)
        pdf.setFont("Helvetica", 10)
        pdf.drawString(25 * mm, y - 5 * mm, client_name)
        pdf.drawString(25 * mm, y - 10 * mm, client_address)
        pdf.drawString(25 * mm, y - 15 * mm, client_zip_city)

        pdf.setFont("Helvetica", 10)
        pdf.drawRightString(width - 25 * mm, y, f"Kundennr.: {client_id}")
        pdf.drawRightString(width - 25 * mm, y - 6 * mm, f"Datum: {date.today().strftime('%d.%m.%Y')}")

        y -= 35 * mm

        # --- Header ---
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(25 * mm, y, "Rechnung Nr. 1001")
        y -= 15 * mm

        pdf.setFont("Helvetica", 10)
        pdf.drawString(25 * mm, y, f"Datum: {date.today().strftime('%d.%m.%Y')}")
        y -= 15 * mm

        # Table Header
        pdf.setFont("Helvetica-Bold", 10)
        col_positions = [25 * mm, 50 * mm, 110 * mm, 140 * mm, 170 * mm]
        headers = ["Pos", "Produkt", "Menge", "Einzel ( € )", "Gesamt ( € )"]
        for i, header in enumerate(headers):
            pdf.drawString(col_positions[i], y, header)
        y -= 5 * mm
        pdf.line(25 * mm, y, width - 25 * mm, y)
        y -= 8 * mm

        # Table Content
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

        # Totals
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

        pdf.showPage()
        pdf.save()

        # Embed JSON Data
        json_data = json.dumps({
            "date": date.today().isoformat(),
            "items": items
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

        # Load into table
        table.setRowCount(0)
        for item in data["items"]:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(item["product"]))

            qty_box = QSpinBox()
            qty_box.setMinimum(0)
            qty_box.setValue(int(item["quantity"]))
            table.setCellWidget(row, 1, qty_box)

            price_box = QDoubleSpinBox()
            price_box.setDecimals(2)
            price_box.setMinimum(0)
            price_box.setValue(float(item["price"]))
            table.setCellWidget(row, 2, price_box)

            sum_item = QTableWidgetItem(f"{item['sum']:.2f}")
            sum_item.setFlags(sum_item.flags() & ~Qt.ItemIsEditable)  # non-editable
            table.setItem(row, 3, sum_item)

            qty_box.valueChanged.connect(lambda _: self._update_row_sum(table, row))
            price_box.valueChanged.connect(lambda _: self._update_row_sum(table, row))

        QMessageBox.information(parent, "Geladen", f"Rechnung erfolgreich geladen:\n{file_path}")

    def _update_row_sum(self, table, row):
        qty_widget = table.cellWidget(row, 1)
        price_widget = table.cellWidget(row, 2)
        if qty_widget and price_widget:
            total = qty_widget.value() * price_widget.value()
            table.item(row, 3).setText(f"{total:.2f}")
