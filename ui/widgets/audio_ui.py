import os
import logging
from PySide6.QtWidgets import *
from .db_utils import DBConnection, _sync_audio_db
from .audio_utils import _is_valid_wav, _upload_with_conflict
from core.config import config

def create_kelola_audio(parent):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    title = QLabel("Kelola File Audio")
    title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px 0;")
    layout.addWidget(title)

    parent.table_audio = QTableWidget()
    parent.table_audio.setColumnCount(2)
    parent.table_audio.setHorizontalHeaderLabels(["Nama File", "Lokasi File"])
    parent.table_audio.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    parent.table_audio.setEditTriggers(QTableWidget.NoEditTriggers)
    layout.addWidget(parent.table_audio)

    btn_layout = QHBoxLayout()
    btn_tambah = QPushButton("➕ Tambah Audio")
    btn_hapus = QPushButton("🗑️ Hapus Audio")
    btn_rename = QPushButton("✏️ Ubah Nama")
    btn_refresh = QPushButton("🔄 Segarkan")
    btn_tambah.clicked.connect(lambda: _tambah_audio(parent))
    btn_hapus.clicked.connect(lambda: _hapus_audio(parent))
    btn_rename.clicked.connect(lambda: _rename_audio(parent))
    btn_refresh.clicked.connect(lambda: _refresh_audio_table(parent) or _sync_audio_db())
    for btn in [btn_tambah, btn_hapus, btn_rename, btn_refresh]:
        btn_layout.addWidget(btn)
    layout.addLayout(btn_layout)

    _refresh_audio_table(parent)
    return widget


def _refresh_audio_table(parent):
    parent.table_audio.setRowCount(0)
    try:
        with DBConnection() as conn:
            c = conn.cursor()
            c.execute("SELECT filename, filepath FROM audio_files")
            rows = c.fetchall()
        parent.table_audio.setRowCount(len(rows))
        for i, (name, path) in enumerate(rows):
            parent.table_audio.setItem(i, 0, QTableWidgetItem(name))
            parent.table_audio.setItem(i, 1, QTableWidgetItem(path))
    except Exception as e:
        logging.error(f"Gagal muat tabel audio: {e}")


def _tambah_audio(parent):
    file, _ = QFileDialog.getOpenFileName(parent, "Pilih File Audio .wav", "", "File Audio (*.wav)")
    if not file:
        return
    if not _is_valid_wav(file):
        QMessageBox.critical(parent, "Kesalahan", "File bukan format WAV yang valid.")
        return
    filename = os.path.basename(file)
    dest = f"{config['paths']['audio_folder']}/{filename}"
    if _upload_with_conflict(file, dest):
        base_name = os.path.splitext(filename)[0]
        try:
            with DBConnection() as conn:
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO audio_files (filename, filepath) VALUES (?, ?)",
                          (base_name, dest))
            _refresh_audio_table(parent)
            _sync_audio_db()
            QMessageBox.information(parent, "Sukses", f"Audio {base_name} ditambahkan.")
        except Exception as e:
            logging.error(f"Gagal tambah audio: {e}")
            QMessageBox.critical(parent, "Error", "Gagal menyimpan ke database.")


def _hapus_audio(parent):
    row = parent.table_audio.currentRow()
    if row < 0:
        QMessageBox.warning(parent, "Kesalahan", "Harap pilih file audio yang ingin dihapus.")
        return
    name = parent.table_audio.item(row, 0).text()
    reply = QMessageBox.question(parent, "Konfirmasi Hapus", f"Apakah Anda yakin ingin menghapus file audio '{name}'?")
    if reply != QMessageBox.Yes:
        return
    try:
        with DBConnection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM audio_files WHERE filename = ?", (name,))
        path = f"{config['paths']['audio_folder']}/{name}.wav"
        if os.path.exists(path):
            os.remove(path)
        _refresh_audio_table(parent)
        _sync_audio_db()
        QMessageBox.information(parent, "Sukses", "File audio berhasil dihapus.")
    except Exception as e:
        logging.error(f"Gagal hapus audio: {e}")
        QMessageBox.critical(parent, "Error", "Gagal menghapus file.")


def _rename_audio(parent):
    row = parent.table_audio.currentRow()
    if row < 0:
        QMessageBox.warning(parent, "Kesalahan", "Pilih file audio yang ingin diubah namanya.")
        return
    old_name = parent.table_audio.item(row, 0).text()
    filepath = parent.table_audio.item(row, 1).text()

    dialog = QInputDialog(parent)
    new_name, ok = QInputDialog.getText(dialog, "Ubah Nama", "Nama baru:", text=old_name)
    if not ok or not new_name or new_name == old_name:
        return
    if not new_name.replace(" ", "").isalnum():
        QMessageBox.warning(parent, "Kesalahan", "Nama hanya boleh huruf, angka, dan spasi.")
        return
    new_filepath = f"{config['paths']['audio_folder']}/{new_name}.wav"
    if os.path.exists(new_filepath):
        QMessageBox.warning(parent, "Kesalahan", f"File '{new_name}.wav' sudah ada.")
        return
    try:
        os.rename(filepath, new_filepath)
        with DBConnection() as conn:
            c = conn.cursor()
            c.execute("UPDATE audio_files SET filename = ?, filepath = ? WHERE filename = ?",
                      (new_name, new_filepath, old_name))
        _refresh_audio_table(parent)
        QMessageBox.information(parent, "Sukses", f"Nama diubah: {old_name} → {new_name}")
    except Exception as e:
        logging.error(f"Gagal rename {old_name}: {e}")
        QMessageBox.critical(parent, "Kesalahan", f"Gagal mengubah nama: {str(e)}")
