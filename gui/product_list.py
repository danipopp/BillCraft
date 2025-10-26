from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt  # <-- Add this line
from .widgets import HoverDeleteButton

class ProductListItem(QWidget):
    """Custom widget for product list with right-aligned delete button."""
    def __init__(self, name, price, delete_callback):
        super().__init__()
        self.name = name
        self.price = price
        self.delete_callback = delete_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(5)

        # Label on left
        self.label = QLabel(f"{name} - {price:.2f}€")
        layout.addWidget(self.label, alignment=Qt.AlignVCenter)

        # Delete button on right
        layout.addStretch()
        self.delete_btn = HoverDeleteButton()
        self.delete_btn.clicked.connect(self.handle_delete)
        layout.addWidget(self.delete_btn, alignment=Qt.AlignRight | Qt.AlignVCenter)

    def enterEvent(self, event):
        self.delete_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.delete_btn.hide()
        super().leaveEvent(event)

    def handle_delete(self):
        self.delete_callback(self.name)
