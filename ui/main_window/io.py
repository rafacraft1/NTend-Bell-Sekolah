# ui/main_window/io.py
import os, json, sqlite3, logging
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox
from ui.widgets import DBConnection, _load_jadwal_table, _load_today_schedule

def export_jadwal(parent):
    """Ekspor data jadwal ke file JSON"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Ekspor Jadwal",
        f"jadwal_bell_{timestamp}.json",
        "File JSON (*.json)"
    )
    if not file_path:
        return

    export_dir = os.path.dirname(file_path) or "export"
    os.makedirs(export_dir, exist_ok=True)

    try:
        with DBConnection() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM jadwal ORDER BY hari, waktu")
            data = [dict(row) for row in c.fetchall()]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        QMessageBox.information(parent, "Sukses", "Jadwal berhasil diekspor.")
        logging.info(f"Jadwal diekspor ke {file_path}")
    except Exception as e:
        logging.error(f"Gagal ekspor: {e}")
        QMessageBox.critical(parent, "Kesalahan", f"Ekspor gagal:\n{str(e)}")


def import_jadwal(parent):
    """Impor data jadwal dari file JSON"""
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        "Impor Jadwal",
        "",
        "File JSON (*.json)"
    )
    if not file_path:
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        required = {"hari", "waktu", "nama", "audio_file"}
        for item in data:
            if not required.issubset(item.keys()):
                raise ValueError("Format data tidak valid")
    except Exception as e:
        QMessageBox.critical(parent, "Kesalahan", f"File tidak valid:\n{str(e)}")
        logging.error(f"Impor gagal: {e}")
        return

    reply = QMessageBox.question(
        parent,
        "Konfirmasi",
        "Apakah Anda yakin ingin menimpa data jadwal yang ada?"
    )
    if reply != QMessageBox.Yes:
        return

    try:
        with DBConnection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM jadwal")
            for item in data:
                c.execute(
                    "INSERT INTO jadwal (hari, waktu, nama, audio_file) VALUES (?, ?, ?, ?)",
                    (item['hari'], item['waktu'], item['nama'], item['audio_file'])
                )

        QMessageBox.information(parent, "Sukses", "Impor jadwal berhasil.")
        _load_jadwal_table(parent)
        _load_today_schedule(parent)
        logging.info("Impor jadwal berhasil")
    except Exception as e:
        logging.error(f"Gagal impor: {e}")
        QMessageBox.critical(parent, "Kesalahan", f"Simpan data gagal:\n{str(e)}")
