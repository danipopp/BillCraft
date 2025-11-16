from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox, QAbstractScrollArea,
    QWidget, QHBoxLayout, QLabel, QAbstractItemView, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from .widgets import HoverDeleteButton


class InvoiceTable(QTableWidget):
    def __init__(self):
        super().__init__(0, 4)

        self.setHorizontalHeaderLabels(["Produkt", "Menge", "Einzelpreis (€)", "Summe (€)"])

        # Initial resize modes (later switched to Interactive)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)


        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.setMinimumWidth(800)

        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setMouseTracking(True)
        self.cellEntered.connect(self.on_table_hover)

        self.setWordWrap(True)

        self._sum_labels = {}
        self._delete_buttons = {}

        # Default max width for product column (updated on window resize)
        self._product_max_width = 250

    # ---------------------------------------------------------
    # CALCULATE TEXT WIDTH (PIXELS)
    # ---------------------------------------------------------
    def calculate_text_width(self, text: str) -> int:
        metrics = QFontMetrics(self.font())
        return metrics.horizontalAdvance(text) + 20  # padding

    # ---------------------------------------------------------
    # ADJUST PRODUCT COLUMN WIDTH (clamped to max width)
    # ---------------------------------------------------------
    def adjust_product_column_width(self):
        widest = 0

        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item:
                w = self.calculate_text_width(item.text())
                widest = max(widest, w)

        # Apply max width protection
        self.setColumnWidth(0, min(widest, self._product_max_width))

    # ---------------------------------------------------------
    # RESIZE EVENT → updates max width + fixes table live
    # ---------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)

        viewport_width = self.viewport().width()

        used_by_other_cols = (
            self.columnWidth(1) +
            self.columnWidth(2) +
            self.columnWidth(3) +
            40
        )

        self._product_max_width = max(150, viewport_width - used_by_other_cols)

        # Re-apply the limit
        self.adjust_product_column_width()

    # --------------------------
    # ADD PRODUCT
    # --------------------------
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

        # PRODUCT NAME (with wrapping)
        product_item = QTableWidgetItem(name)
        product_item.setFlags(product_item.flags() & ~Qt.ItemIsEditable)
        product_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        product_item.setToolTip(name)
        product_item.setFont(self.font())
        product_item.setSizeHint(product_item.sizeHint())
        self.setItem(row, 0, product_item)

        # Resize to fit content first
        self.resizeColumnToContents(0)

        # Then cap to max width
        self.setColumnWidth(0, min(self.columnWidth(0), self._product_max_width))

        # --------------------------
        # QUANTITY
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

        self.resizeRowsToContents()
        self.resizeColumnsToContents()

        # Reapply max width constraint after auto-resize
        self.setColumnWidth(0, min(self.columnWidth(0), self._product_max_width))

        # Set all columns interactive afterwards
        header = self.horizontalHeader()
        for col in range(self.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Interactive)

        self.viewport().update()
        self.update_totals()

    def get_button_row(self, btn):
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

        total = qty_widget.value() * price_widget.value()
        sum_label.setText(f"{total:.2f}")
        self.update_totals()

    def update_totals(self):
        """Sum all rows."""
        netto = 0.0
        for row, label in self._sum_labels.items():
            try:
                netto += float(label.text())
            except ValueError:
                pass
        mwst = netto * 0.19
        brutto = netto + mwst

        if hasattr(self.parent_window, 'sum_netto_label'):
            self.parent_window.sum_netto_label.setText(f"Zwischensumme (Netto): {netto:.2f} €")
        if hasattr(self.parent_window, 'sum_tax_label'):
            self.parent_window.sum_tax_label.setText(f"MwSt (19%): {mwst:.2f} €")
        if hasattr(self.parent_window, 'sum_brutto_label'):
            self.parent_window.sum_brutto_label.setText(f"Gesamtsumme (Brutto): {brutto:.2f} €")


    def on_table_hover(self, row, column):
        # Hide all buttons first
        for btn in self._delete_buttons.values():
            btn.hide()
        # Show only hovered row button
        if row in self._delete_buttons:
            self._delete_buttons[row].show()
