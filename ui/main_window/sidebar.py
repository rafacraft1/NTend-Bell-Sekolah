from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import os
from core.config import config

def create_sidebar(parent):
    sidebar = QFrame()
    sidebar.setFixedWidth(200)
    sidebar.setStyleSheet("background: #2c3e50; color: white;")
    layout = QVBoxLayout(sidebar)

    logo = QLabel()
    pix = QPixmap(config["paths"]["logo"]) if os.path.exists(config["paths"]["logo"]) else QPixmap(120, 120)
    if pix.isNull(): pix.fill(Qt.gray)
    logo.setPixmap(pix.scaled(120, 120, Qt.KeepAspectRatio))
    logo.setAlignment(Qt.AlignCenter)
    layout.addWidget(logo)

    btns = {
        "Dashboard": 0,
        "Kelola Jadwal": 1,
        "Kelola Audio": 2,
    }
    for text, idx in btns.items():
        btn = QPushButton(f"  {text}")
        btn.setStyleSheet("QPushButton{text-align:left;padding:12px;font-size:14px;} QPushButton:hover{background:#34495e;}")
        btn.clicked.connect(lambda _, i=idx: parent.content.setCurrentIndex(i))
        layout.addWidget(btn)

    layout.addStretch()
    footer = QLabel(f"{config['app']['name']} V{config['app']['version']}")
    footer.setAlignment(Qt.AlignCenter)
    layout.addWidget(footer)

    return sidebar
