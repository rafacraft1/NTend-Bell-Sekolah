from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle, QMessageBox
from PySide6.QtGui import QAction, QIcon
import os, logging
from core.config import config

def setup_tray(parent):
    tray = QSystemTrayIcon(parent)

    logo_path = config["paths"]["logo"]
    if os.path.exists(logo_path):
        tray.setIcon(QIcon(logo_path))
    else:
        tray.setIcon(parent.style().standardIcon(QStyle.SP_ComputerIcon))
        logging.warning(f"Icon tray tidak ditemukan: {logo_path}")

    tray_menu = QMenu()

    # Aksi buka aplikasi
    show_action = tray_menu.addAction("Buka Aplikasi")
    show_action.triggered.connect(parent.show_window)

    # Aksi keluar aplikasi (dengan konfirmasi)
    quit_action = tray_menu.addAction("Keluar")
    def confirm_exit():
        reply = QMessageBox.question(
            parent,
            "Konfirmasi Keluar",
            "Apakah Anda yakin ingin keluar dari aplikasi?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QApplication.quit()
    quit_action.triggered.connect(confirm_exit)

    # Toggle notifikasi
    toggle_notif = QAction("Notifikasi: ON", parent, checkable=True, checked=True)
    def _toggle(checked):
        parent.notifications_enabled = checked
        toggle_notif.setText("Notifikasi: ON" if checked else "Notifikasi: OFF")
    toggle_notif.toggled.connect(_toggle)
    tray_menu.addAction(toggle_notif)

    tray.setContextMenu(tray_menu)

    if tray.isSystemTrayAvailable():
        tray.show()
    else:
        logging.warning("System tray tidak tersedia.")

    parent.notifications_enabled = True
    return tray
