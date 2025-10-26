from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QSize, Qt

class HoverDeleteButton(QPushButton):
    """A red X button."""
    def __init__(self, parent=None):
        super().__init__("✕", parent)
        self.setFixedSize(QSize(22, 22))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                color: red;
                border: none;
                font-weight: bold;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.1);
                border-radius: 11px;
            }
        """)
        self.hide()
