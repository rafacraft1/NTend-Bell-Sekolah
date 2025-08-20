import os
import logging
from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtCore import QDate
from .db_utils import DBConnection
from core.config import config

def _load_today_schedule(parent):
    parent.table_jadwal.blockSignals(True)
    parent.table_jadwal.setRowCount(0)
    day = QDate.currentDate().dayOfWeek()

    # Minggu = libur
    if day == 7:
        parent.table_jadwal.setRowCount(1)
        parent.table_jadwal.setItem(0, 0, QTableWidgetItem(config["messages"]["holiday"]))
        parent.table_jadwal.setItem(0, 1, QTableWidgetItem(config["messages"]["no_bell"]))
        parent.table_jadwal.setItem(0, 2, QTableWidgetItem("-"))
        parent.table_jadwal.blockSignals(False)
        return

    hari_list = config["localization"]["days"][:7]
    hari_ini = hari_list[day]
    try:
        with DBConnection() as conn:
            c = conn.cursor()
            c.execute("SELECT waktu, nama, audio_file FROM jadwal WHERE hari = ? ORDER BY waktu", (hari_ini,))
            rows = c.fetchall()
    except Exception as e:
        logging.error(f"Gagal muat jadwal harian: {e}")
        rows = []

    if not rows:
        parent.table_jadwal.setRowCount(1)
        parent.table_jadwal.setItem(0, 0, QTableWidgetItem(config["messages"]["no_schedule"]))
        parent.table_jadwal.setItem(0, 1, QTableWidgetItem(config["messages"]["no_schedule"]))
        parent.table_jadwal.setItem(0, 2, QTableWidgetItem("-"))
    else:
        parent.table_jadwal.setRowCount(len(rows))
        for i, (w, n, a) in enumerate(rows):
            parent.table_jadwal.setItem(i, 0, QTableWidgetItem(w))
            parent.table_jadwal.setItem(i, 1, QTableWidgetItem(n))
            parent.table_jadwal.setItem(i, 2, QTableWidgetItem(os.path.splitext(a)[0]))
    parent.table_jadwal.blockSignals(False)
