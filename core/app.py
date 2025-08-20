# core/app.py
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.splash import SplashScreen
from ui.main_window import MainWindow
import sys
import logging
import os
from datetime import datetime
from core.config import config


# --- Setup logging harian ---
def setup_logging():
    os.makedirs(config["paths"]["logs"], exist_ok=True)
    log_filename = datetime.now().strftime(f"{config['paths']['logs']}/app_%Y-%m-%d.log")
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8"
    )
    logging.info("=== Aplikasi SchoolBell dimulai ===")

import ctypes
myappid = 'nurindra.schoolbell.app'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class SchoolBellApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

        # ✅ aktifkan logging harian
        setup_logging()

        from core.database import init_db
        init_db()

        self.splash = SplashScreen()
        self.splash.show()

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show_main)
        self.timer.start(config["schedule"]["splash_duration_ms"])

    def show_main(self):
        self.splash.close()
        self.main = MainWindow()
        self.main.show()


if __name__ == "__main__":
    app = SchoolBellApp()
    app.exec()
