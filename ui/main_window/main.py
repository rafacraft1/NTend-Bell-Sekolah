# ui/main_window/main.py
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QMessageBox, QSystemTrayIcon
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import os, logging
from core.config import config
from ui.widgets import create_dashboard, create_kelola_jadwal, create_kelola_audio

# modular import
from .tray import setup_tray
from .menu import setup_menu
from .sidebar import create_sidebar
from .statusbar import setup_statusbar
from .scheduler import setup_scheduler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config['app']['name']} V{config['app']['version']}")
        self.resize(1000, 600)
        self.setStyleSheet("font-family: Segoe UI;")

        # icon
        logo_path = config["paths"]["logo"]
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        else:
            logging.warning(f"Icon aplikasi tidak ditemukan: {logo_path}")

        # modular setup
        self.tray_icon = setup_tray(self)
        setup_menu(self)
        sidebar = create_sidebar(self)

        self.content = QStackedWidget()
        self.content.addWidget(create_dashboard(self))
        self.content.addWidget(create_kelola_jadwal(self))
        self.content.addWidget(create_kelola_audio(self))

        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)
        layout.addWidget(sidebar)
        layout.addWidget(self.content)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(main_widget)

        setup_statusbar(self)
        setup_scheduler(self)
    
    def show_window(self):
        """Tampilkan kembali window kalau minimize/hidden ke tray"""
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.show()
        self.raise_()
        self.activateWindow()
        
    def notify(self, title, message, msec=4000, icon=QSystemTrayIcon.Information):
        """Tampilkan notifikasi tray (jika tersedia & aktif)"""
        try:
            if (
                self.tray_icon.isSystemTrayAvailable()
                and self.tray_icon.supportsMessages()
                and self.notifications_enabled
            ):
                logging.info(f"ShowMessage: {title} - {message}")
                self.tray_icon.showMessage(title, message, icon, msec)
            else:
                logging.warning("Notifikasi tidak didukung / dinonaktifkan")
        except Exception as e:
            logging.error(f"Gagal menampilkan notifikasi: {e}")
        
    def changeEvent(self, event):
        """Otomatis minimize ke tray saat klik tombol minimize"""
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized() and self.tray_icon.isSystemTrayAvailable():
                event.ignore()
                self.hide()
                self.notify("SchoolBell", "Aplikasi berjalan di tray. Klik ikon tray untuk membuka kembali.", 3000)
        super().changeEvent(event)
        
    def closeEvent(self, event):
        if self.tray_icon.isSystemTrayAvailable():
            reply = QMessageBox.question(
                self,
                "Tutup Aplikasi",
                "Anda yakin ingin menutup aplikasi? (yes), minimize ke tray (no)",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.No
            )
            # Yes = keluar aplikasi sepenuhnya
            if reply == QMessageBox.Yes:
                event.accept()
            # No = minimize ke tray
            elif reply == QMessageBox.No:
                event.ignore()
                self.hide()
                self.notify(
                    "SchoolBell",
                    "Aplikasi berjalan di tray. Klik ikon tray untuk membuka kembali.",
                    3000
                )
            # Cancel = tetap terbuka
            else:
                event.ignore()
        else:
            event.accept()
