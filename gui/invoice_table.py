from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QSpinBox,
    QWidget, QHBoxLayout, QLabel, QAbstractItemView, QHeaderView
)
from PySide6.QtCore import Qt
from .widgets import HoverDeleteButton

class InvoiceTable(QTableWidget):
    def __init__(self):
        super().__init__(0, 4)
        self.setHorizontalHeaderLabels(["Produkt", "Menge", "Einzelpreis (€)", "Summe (€)"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setMouseTracking(True)
        self.cellEntered.connect(self.on_table_hover)

        self._sum_labels = {}
        self._delete_buttons = {}

    def add_product(self, name, price):
        # Check for duplicates
        for row in range(self.rowCount()):
            if self.item(row, 0).text().lower() == name.lower():
                qty_widget = self.cellWidget(row, 1)
                qty_widget.setValue(qty_widget.value() + 1)
                self.update_totals()
                return

        # Add new row
        row = self.rowCount()
        self.insertRow(row)

        # Product name
        self.setItem(row, 0, QTableWidgetItem(name))

        # Quantity
        qty_widget = QSpinBox()
        qty_widget.setValue(1)
        qty_widget.setMinimum(1)
        qty_widget.valueChanged.connect(self.update_totals)
        self.setCellWidget(row, 1, qty_widget)

        # Single price
        price_item = QTableWidgetItem(f"{price:.2f}")
        price_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setItem(row, 2, price_item)

        # Sum + delete button
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        sum_label = QLabel(f"{price:.2f}")
        sum_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        delete_btn = HoverDeleteButton()
        delete_btn.clicked.connect(lambda _, btn=delete_btn: self.delete_row(self.get_button_row(btn)))

        layout.addWidget(sum_label)
        layout.addStretch()
        layout.addWidget(delete_btn, alignment=Qt.AlignRight | Qt.AlignVCenter)
        self.setCellWidget(row, 3, container)

        self._sum_labels[row] = sum_label
        self._delete_buttons[row] = delete_btn
        self.update_totals()

    def get_button_row(self, btn):
        """Return the row index of a given delete button."""
        for row in range(self.rowCount()):
            widget = self.cellWidget(row, 3)
            if widget:
                layout = widget.layout()
                if layout.itemAt(layout.count() - 1).widget() == btn:
                    return row
        return -1

    def delete_row(self, row_index):
        if row_index == -1:
            return
        self.removeRow(row_index)
        if row_index in self._sum_labels:
            del self._sum_labels[row_index]
        if row_index in self._delete_buttons:
            del self._delete_buttons[row_index]
        self.update_totals()
        self._rebuild_refs()

    def _rebuild_refs(self):
        """Fix references after deletion."""
        new_sums = {}
        new_btns = {}
        for row in range(self.rowCount()):
            widget = self.cellWidget(row, 3)
            if widget:
                new_sums[row] = widget.layout().itemAt(0).widget()
                new_btns[row] = widget.layout().itemAt(2).widget()
        self._sum_labels = new_sums
        self._delete_buttons = new_btns

    def update_totals(self):
        total = 0.0
        for row in range(self.rowCount()):
            # --- Quantity ---
            qty_widget = self.cellWidget(row, 1)
            qty = qty_widget.value() if qty_widget else 0

            # --- Single price ---
            price_widget = self.cellWidget(row,2)
            price = price_widget.value() if price_widget else 0
            
            # --- Sum ---
            sum_value = qty * price
            sum_item = self.item(row,3)
            if sum_item:
                sum_item.setText(f"{sum_value:.2f}")
            total += sum_value
        if hasattr(self, 'total_label'):
            self.total_label.setText(f"Gesamtsumme: {total:.2f} €")

    def on_table_hover(self, row, column):
        # Hide all buttons first
        for btn in self._delete_buttons.values():
            btn.hide()
        # Show only hovered row button
        if row in self._delete_buttons:
            self._delete_buttons[row].show()
