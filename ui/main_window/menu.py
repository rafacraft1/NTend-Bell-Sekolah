from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle
from PySide6.QtGui import QAction
from .io import export_jadwal, import_jadwal
from .about import show_tentang

def setup_menu(parent):
    menu_bar = parent.menuBar()
    file_menu = menu_bar.addMenu("File")
    export_action = QAction("Ekspor Jadwal", parent)
    import_action = QAction("Impor Jadwal", parent)
    export_action.triggered.connect(lambda: export_jadwal(parent))
    import_action.triggered.connect(lambda: import_jadwal(parent))
    file_menu.addAction(export_action)
    file_menu.addAction(import_action)

    tentang_menu = menu_bar.addMenu("Tentang")
    tentang_action = QAction("Tentang Aplikasi", parent)
    tentang_action.triggered.connect(lambda: show_tentang(parent))
    tentang_menu.addAction(tentang_action)
