from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox, QVBoxLayout, QAbstractScrollArea,
    QWidget, QHBoxLayout, QLabel, QAbstractItemView, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt
from .widgets import HoverDeleteButton

class InvoiceTable(QTableWidget):
    def __init__(self):
        super().__init__(0, 4)
        self.setHorizontalHeaderLabels(["Produkt", "Menge", "Einzelpreis (€)", "Summe (€)"])

        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)  # Produkt
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Menge
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Einzelpreis
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)  # Summe

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)


        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.setMinimumWidth(800)

        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setMouseTracking(True)
        self.cellEntered.connect(self.on_table_hover)

        self._sum_labels = {}
        self._delete_buttons = {}

        self.setWordWrap(True)

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

        product_item = QTableWidgetItem(name)
        product_item.setFlags(product_item.flags() & ~Qt.ItemIsEditable)
        product_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        product_item.setToolTip(name)
        product_item.setFont(self.font())
        product_item.setSizeHint(product_item.sizeHint())
        self.setItem(row, 0, product_item)
        self.resizeRowToContents(row)

        # Quantity
        qty_widget = QSpinBox()
        qty_widget.setValue(1)
        qty_widget.setMinimum(1)

        qty_widget.setMinimumWidth(100)
        qty_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        qty_widget.valueChanged.connect(lambda _: self.update_row_sum(row)) 
        self.setCellWidget(row, 1, qty_widget)

        # Single price
        price_widget = QDoubleSpinBox() 
        price_widget.setDecimals(2)
        price_widget.setMinimum(0)
        price_widget.setMaximum(float("inf"))
        price_widget.setValue(price)

        price_widget.setMinimumWidth(100)
        price_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        price_widget.valueChanged.connect(lambda _: self.update_row_sum(row))
        self.setCellWidget(row, 2, price_widget)

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

        self.resizeRowsToContents()
        self.resizeColumnsToContents()

        header = self.horizontalHeader()
        for col in range(self.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Interactive)

        self.viewport().update()

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
        self._rebuild_refs()
        self.update_totals()

    def _rebuild_refs(self):
        """Fix references after deletion."""
        new_sums = {}
        new_btns = {}
        for row in range(self.rowCount()):
            widget = self.cellWidget(row, 3)
            if widget:
                layout = widget.layout()
                new_sums[row] = layout.itemAt(0).widget()
                new_btns[row] = layout.itemAt(layout.count() - 1).widget()
        self._sum_labels = new_sums
        self._delete_buttons = new_btns

    def update_row_sum(self, row):
        """Recalculate a single row when quantity or price changes."""
        qty_widget = self.cellWidget(row, 1)
        price_widget = self.cellWidget(row, 2)
        sum_label = self._sum_labels.get(row)

        if not qty_widget or not price_widget or not sum_label:
            return

        qty = qty_widget.value()
        price = price_widget.value()
        total = qty * price
        sum_label.setText(f"{total:.2f}")
        self.update_totals()

    def update_totals(self):
        """Sum all rows."""
        total = 0.0
        for row, label in self._sum_labels.items():
            try:
                total += float(label.text())
            except ValueError:
                pass
        if hasattr(self, 'total_label'):
            self.total_label.setText(f"Gesamtsumme: {total:.2f} €")

    def on_table_hover(self, row, column):
        # Hide all buttons first
        for btn in self._delete_buttons.values():
            btn.hide()
        # Show only hovered row button
        if row in self._delete_buttons:
            self._delete_buttons[row].show()
