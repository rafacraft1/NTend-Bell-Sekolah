# ui/main_window/scheduler.py
import os, json, sqlite3, logging
from datetime import datetime as dt
from PySide6.QtCore import QTimer, QDate, QTime, QUrl
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QMessageBox
from ui.widgets import DBConnection, _load_today_schedule, _load_jadwal_table
from core.config import config

def setup_scheduler(parent):
    """Pasang timer cek jadwal & backup otomatis"""
    parent.timer = QTimer()
    parent.timer.timeout.connect(lambda: cek_jadwal(parent))
    parent.timer.start(1000)

    parent.timer_backup = QTimer()
    parent.timer_backup.timeout.connect(lambda: _schedule_backup_check(parent))
    parent.timer_backup.start(config["schedule"]["backup_interval_ms"])

    parent.last_played_time = None
    parent.last_checked_day = None


def cek_jadwal(parent):
    now = QTime.currentTime().toString("HH:mm")
    day = QDate.currentDate().dayOfWeek()

    if day == 7:  # Minggu = libur
        parent.next_schedule_label.setText("Jadwal berikutnya: - (Libur)")
        return

    hari_list = config["localization"]["days"][1:7]
    hari = hari_list[day]

    # reload jadwal kalau ganti hari
    if parent.last_checked_day is not None and parent.last_checked_day != day:
        _load_today_schedule(parent)
    parent.last_checked_day = day

    if parent.last_played_time == now:
        return

    try:
        with DBConnection() as conn:
            c = conn.cursor()
            c.execute("SELECT nama, audio_file FROM jadwal WHERE waktu = ? AND hari = ?", (now, hari))
            result = c.fetchone()

        if result:
            nama, audio_filename = result
            base_name = os.path.splitext(audio_filename)[0]
            audio_path = os.path.join(config["paths"]["audio_folder"], f"{base_name}.wav")

            if not os.path.exists(audio_path):
                parent.status_msg.setText(f"❌ File audio tidak ditemukan: {base_name}.wav")
                logging.warning(f"File audio tidak ditemukan: {audio_path}")
                return

            parent.sound.stop()
            parent.sound.setSource(QUrl.fromLocalFile(audio_path))
            parent.sound.play()

            parent.status_msg.setText(f"🔔 Bel berbunyi: {nama}")
            parent.last_played_time = now

            parent.notify("🔔 Bel Berbunyi", f"Kegiatan: {nama}\nWaktu: {now}", 5000)

            # highlight di tabel jadwal
            table = parent.table_jadwal
            for i in range(table.rowCount()):
                item = table.item(i, 0)
                if item and item.text() == now:
                    for j in range(3):
                        cell = table.item(i, j)
                        if cell:
                            cell.setBackground(QColor("#FFD700"))
                    QTimer.singleShot(5000, lambda r=i: _reset_highlight(parent, r))

    except Exception as e:
        logging.error(f"Gagal cek jadwal: {e}")

    # hitung next schedule
    try:
        with DBConnection() as conn:
            c = conn.cursor()
            c.execute("SELECT waktu, nama FROM jadwal WHERE hari = ? ORDER BY waktu", (hari,))
            rows = c.fetchall()

        now_dt = dt.strptime(now, "%H:%M")
        next_jadwal = None
        for w, n in rows:
            w_dt = dt.strptime(w, "%H:%M")
            if w_dt > now_dt:
                next_jadwal = (w, n, (w_dt - now_dt))
                break

        if next_jadwal:
            w, n, delta = next_jadwal
            menit = delta.seconds // 60
            parent.next_schedule_label.setText(f"Jadwal berikutnya: {n} ({w}, {menit} menit lagi)")
        else:
            parent.next_schedule_label.setText("Jadwal berikutnya: - (hari ini selesai)")
    except Exception as e:
        logging.error(f"Gagal hitung jadwal berikutnya: {e}")
        parent.next_schedule_label.setText("Jadwal berikutnya: -")


def _reset_highlight(parent, row):
    if row >= parent.table_jadwal.rowCount():
        return
    for j in range(3):
        cell = parent.table_jadwal.item(row, j)
        if cell:
            cell.setBackground(QColor("white"))


def _schedule_backup_check(parent):
    now = QTime.currentTime()
    if (now.hour() == config["schedule"]["backup_hour"]
        and now.minute() == config["schedule"]["backup_minute"]):
        _auto_backup(parent)


def _auto_backup(parent):
    timestamp = dt.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = config["paths"]["export"]
    os.makedirs(backup_dir, exist_ok=True)
    file_path = f"{backup_dir}/backup_{timestamp}.json"
    try:
        with DBConnection() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM jadwal ORDER BY hari, waktu")
            data = [dict(row) for row in c.fetchall()]
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Backup otomatis berhasil: {file_path}")
    except Exception as e:
        logging.error(f"Gagal backup: {e}")
