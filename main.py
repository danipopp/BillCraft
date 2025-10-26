from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from database.db import create_tables

if __name__ == "__main__":
    create_tables()  # Ensure DB tables exist
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
