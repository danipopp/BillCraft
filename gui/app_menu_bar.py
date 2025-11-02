from PySide6.QtWidgets import QMenuBar, QMenu, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal


class AppMenuBar(QMenuBar):
    """Reusable top menu bar with signals for actions."""

    # Define signals so MainWindow can react
    new_invoice = Signal()
    save_invoice = Signal()
    load_invoice = Signal()
    exit_app = Signal()
    refresh_products = Signal()
    import_products = Signal()
    export_products = Signal()
    customer_window = Signal()
    select_logo = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_menus()

    def _build_menus(self):
        # ---- Datei menu ----
        file_menu = QMenu("Datei", self)

        new_invoice_action = QAction("Neue Rechnung", self)
        new_invoice_action.triggered.connect(self.new_invoice.emit)
        file_menu.addAction(new_invoice_action)

        save_invoice_action = QAction("Speichern", self)
        save_invoice_action.triggered.connect(self.save_invoice.emit)
        file_menu.addAction(save_invoice_action)

        load_invoice_action = QAction("Load Invoice", self)
        load_invoice_action.triggered.connect(self.load_invoice.emit)
        file_menu.addAction(load_invoice_action)

        file_menu.addSeparator()

        exit_action = QAction("Beenden", self)
        exit_action.triggered.connect(self.exit_app.emit)
        file_menu.addAction(exit_action)

        self.addMenu(file_menu)

        # ---- Produkte menu ----
        product_menu = QMenu("Produkte", self)

        refresh_action = QAction("Aktualisieren", self)
        refresh_action.triggered.connect(self.refresh_products.emit)
        product_menu.addAction(refresh_action)

        import_action = QAction("Importieren...", self)
        import_action.triggered.connect(self.import_products.emit)
        product_menu.addAction(import_action)

        export_action = QAction("Exportieren...", self)
        export_action.triggered.connect(self.export_products.emit)
        product_menu.addAction(export_action)

        logo_action = QAction("Select Logo", self)
        logo_action.triggered.connect(self.select_logo.emit)
        product_menu.addAction(logo_action)

        self.addMenu(product_menu)

        # --- Customer menu ---
        customer_menu = QMenu("Customer", self)

        custumer_action = QAction("CustomerWindow",self)
        custumer_action.triggered.connect(self.customer_window.emit)
        customer_menu.addAction(custumer_action)

        self.addMenu(customer_menu)