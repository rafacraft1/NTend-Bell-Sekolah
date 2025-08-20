# ui/splash.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QScreen, QPainter
import os
import logging
from core.config import config

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        label = QLabel(self)
        logo_path = config["paths"]["logo"]
        pixmap = QPixmap()

        if os.path.exists(logo_path):
            pixmap.load(logo_path)
        else:
            logging.warning(f"File logo tidak ditemukan: {logo_path}")

        if pixmap.isNull():
            # Buat placeholder
            logging.info("Membuat placeholder logo.")
            pixmap = QPixmap(200, 200)
            pixmap.fill(Qt.lightGray)
            painter = QPainter(pixmap)
            painter.setPen(Qt.darkGray)
            painter.setFont(painter.font())
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "SchoolBell")
            painter.end()
        else:
            pixmap = pixmap.scaled(
                200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

        label.setPixmap(pixmap)

        layout = QVBoxLayout(self)
        layout.addWidget(label, 0, Qt.AlignCenter)

        self.resize(300, 300)
        self.move_to_center()

    def move_to_center(self):
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)