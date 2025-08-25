from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QHeaderView
from PySide6.QtCore import Qt, QTimer, QDateTime
from .schedule_loader import _load_today_schedule
from core.config import config

def create_dashboard(parent):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    title = QLabel("Dashboard")
    title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px 0;")
    layout.addWidget(title)

    parent.analog = QLabel()
    parent.analog.setStyleSheet("font-size: 40px; font-weight: bold;")
    parent.analog.setAlignment(Qt.AlignCenter)
    parent.date_label = QLabel()
    parent.date_label.setStyleSheet("font-size: 16px;")
    parent.date_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(parent.analog)
    layout.addWidget(parent.date_label)

    parent.table_jadwal = QTableWidget()
    parent.table_jadwal.setColumnCount(3)
    parent.table_jadwal.setHorizontalHeaderLabels(["Waktu", "Kegiatan", "Audio"])
    parent.table_jadwal.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    parent.table_jadwal.setEditTriggers(QTableWidget.NoEditTriggers)
    parent.table_jadwal.setStyleSheet("""
        QTableWidget {
            background-color: white;
            alternate-background-color: #f8f8f8;
            gridline-color: #ddd;
            selection-background-color: #4CAF50;
            selection-color: white;
            font-size: 12px;
        }
        QHeaderView::section {
            background-color: #2c3e50;
            color: white;
            font-weight: bold;
            padding: 8px;
            border: 1px solid #444;
        }
        QTableWidget::item {
            padding: 5px;
        }
    """)
    layout.addWidget(parent.table_jadwal)

    parent.update_datetime = lambda: _update_datetime(parent)
    parent.timer_clock = QTimer()
    parent.timer_clock.timeout.connect(parent.update_datetime)
    parent.timer_clock.start(1000)

    _load_today_schedule(parent)
    return widget


def _update_datetime(parent):
    now = QDateTime.currentDateTime()
    hour, minute, second = now.time().hour(), now.time().minute(), now.time().second()
    parent.analog.setText(f"{hour:02d}:{minute:02d}:{second:02d}")
    hari_list = config["localization"]["days"]
    bulan_list = config["localization"]["months"]

    day_of_week = now.date().dayOfWeek()
    day_name = hari_list[day_of_week]

    # 🔧 FIX: convert month index ke string biar cocok dengan JSON
    bulan = bulan_list[str(now.date().month())]

    date_str = f"{day_name}, {now.date().day()} {bulan} {now.date().year()}"
    parent.date_label.setText(date_str)
