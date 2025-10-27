from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Qt, Signal
from .widgets import HoverDeleteButton

class ProductListItem(QWidget):
    """Custom widget for product list with editable right-aligned price and delete button."""
    price_changed = Signal(str, float)

    def __init__(self, name, price, delete_callback):
        super().__init__()
        self.name = name
        self.price = price
        self.delete_callback = delete_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        # Left: Product name
        self.name_label = QLabel(self.name)
        layout.addWidget(self.name_label, alignment=Qt.AlignVCenter | Qt.AlignLeft)

        # Center: Editable price field (right-aligned)
        layout.addStretch()
        self.price_input = QLineEdit(f"{self.price:.2f}")
        self.price_input.setFixedWidth(80)
        self.price_input.setAlignment(Qt.AlignRight)
        layout.addWidget(self.price_input, alignment=Qt.AlignVCenter | Qt.AlignRight)

        # Right: Delete button
        self.delete_btn = HoverDeleteButton()
        self.delete_btn.setFixedSize(22, 22)
        self.delete_btn.hide()
        layout.addWidget(self.delete_btn, alignment=Qt.AlignVCenter | Qt.AlignRight)

        self.price_input.editingFinished.connect(self.on_price_changed)
        self.delete_btn.clicked.connect(self.handle_delete)

    def enterEvent(self, event):
        self.delete_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.delete_btn.hide()
        super().leaveEvent(event)

    def handle_delete(self):
        self.delete_callback(self.name)

    def on_price_changed(self):
        """Emit signal when price is manually changed."""
        try:
            new_price = float(self.price_input.text().replace(",", "."))
        except ValueError:
            self.price_input.setText(f"{self.price:.2f}")
            return

        if abs(new_price - self.price) > 1e-9:
            self.price = new_price
            self.price_changed.emit(self.name, new_price)
