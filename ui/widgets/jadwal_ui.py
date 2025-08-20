import os
import logging
import sqlite3
from PySide6.QtWidgets import *
from PySide6.QtCore import QTime, QUrl
from .db_utils import DBConnection, _sync_audio_db
from core.config import config

def create_kelola_jadwal(parent):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    title = QLabel("Kelola Jadwal")
    title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px 0;")
    layout.addWidget(title)

    parent.table_jadwal_hari = QTableWidget()
    parent.table_jadwal_hari.setColumnCount(6)
    parent.table_jadwal_hari.setHorizontalHeaderLabels(config["localization"]["days"][1:7])
    _load_jadwal_table(parent)
    parent.table_jadwal_hari.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    parent.table_jadwal_hari.setEditTriggers(QTableWidget.NoEditTriggers)
    layout.addWidget(parent.table_jadwal_hari)

    btn_layout = QHBoxLayout()
    btn_tambah = QPushButton("➕ Tambah Jadwal")
    btn_edit = QPushButton("✏️ Edit Jadwal")
    btn_hapus = QPushButton("🗑️ Hapus Jadwal")
    btn_test = QPushButton("🔊 Uji Bel")
    btn_copy = QPushButton("📋 Salin Jadwal Harian")
    btn_tambah.clicked.connect(lambda: _tambah_jadwal(parent))
    btn_edit.clicked.connect(lambda: _edit_jadwal(parent))
    btn_hapus.clicked.connect(lambda: _hapus_jadwal(parent))
    btn_test.clicked.connect(lambda: _test_bell(parent))
    btn_copy.clicked.connect(lambda: _copy_jadwal_harian(parent))
    for btn in [btn_tambah, btn_edit, btn_hapus, btn_test, btn_copy]:
        btn_layout.addWidget(btn)
    layout.addLayout(btn_layout)
    return widget


def _load_jadwal_table(parent):
    parent.table_jadwal_hari.setRowCount(0)
    hari_list = config["localization"]["days"][1:7]

    with DBConnection() as conn:
        c = conn.cursor()
        c.execute("SELECT hari, waktu, nama FROM jadwal ORDER BY waktu")
        all_data = c.fetchall()

    data_per_hari = {h: [] for h in hari_list}
    for h, w, n in all_data:
        if h in data_per_hari:
            data_per_hari[h].append((w, n))

    for h in hari_list:
        data_per_hari[h].sort(key=lambda x: tuple(map(int, x[0].split(":"))))

    max_len = max((len(v) for v in data_per_hari.values()), default=0)
    parent.table_jadwal_hari.setRowCount(max_len)

    for col, h in enumerate(hari_list):
        for row in range(len(data_per_hari[h])):
            w, n = data_per_hari[h][row]
            parent.table_jadwal_hari.setItem(row, col, QTableWidgetItem(f"{w} - {n}"))


def _tambah_jadwal(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Tambah Jadwal Baru")
    layout = QFormLayout(dialog)
    nama = QLineEdit()
    layout.addRow("Nama Kegiatan:", nama)
    hari = QComboBox()
    hari.addItems(config["localization"]["days"][1:7])
    layout.addRow("Hari:", hari)
    waktu = QTimeEdit()
    waktu.setDisplayFormat("HH:mm")
    layout.addRow("Waktu:", waktu)
    audio_combo = QComboBox()
    with DBConnection() as conn:
        c = conn.cursor()
        c.execute("SELECT filename FROM audio_files")
        audio_list = [row[0] for row in c.fetchall()]
    audio_combo.addItems(audio_list)
    layout.addRow("Audio:", audio_combo)

    btn_test = QPushButton("▶️ Uji Audio")
    def test_audio():
        selected = audio_combo.currentText()
        if not selected:
            return
        path = f"{config['paths']['audio_folder']}/{selected}.wav"
        if os.path.exists(path):
            parent.sound.setSource(QUrl.fromLocalFile(path))
            parent.sound.play()
        else:
            QMessageBox.warning(dialog, "Kesalahan", "File audio .wav tidak ditemukan.")
    btn_test.clicked.connect(test_audio)
    layout.addRow("", btn_test)

    btn_upload = QPushButton("📁 Unggah Audio (.wav)")
    from .audio_utils import _upload_with_conflict
    def upload_audio():
        file, _ = QFileDialog.getOpenFileName(dialog, "Pilih File Audio", "", "File Audio (*.wav)")
        if file:
            filename = os.path.basename(file)
            dest = f"{config['paths']['audio_folder']}/{filename}"
            if _upload_with_conflict(file, dest):
                base_name = os.path.splitext(filename)[0]
                with DBConnection() as conn:
                    c = conn.cursor()
                    c.execute("INSERT OR IGNORE INTO audio_files (filename, filepath) VALUES (?, ?)",
                              (base_name, dest))
                audio_combo.clear()
                with DBConnection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT filename FROM audio_files")
                    files = [row[0] for row in c.fetchall()]
                audio_combo.addItems(files)
                audio_combo.setCurrentText(base_name)
                _sync_audio_db()
    btn_upload.clicked.connect(upload_audio)
    layout.addRow("", btn_upload)

    btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addRow(btn_box)
    def simpan():
        w = waktu.time()
        if not w.isValid():
            QMessageBox.warning(dialog, "Kesalahan", "Waktu yang dimasukkan tidak valid.")
            return
        waktu_str = w.toString("HH:mm")
        _simpan_jadwal(parent, nama.text(), hari.currentText(), waktu_str, audio_combo.currentText(), dialog)
    btn_box.accepted.connect(simpan)
    btn_box.rejected.connect(dialog.reject)
    dialog.exec_()


def _simpan_jadwal(parent, nama, hari, waktu, audio, dialog):
    if not nama or not waktu or not audio:
        QMessageBox.warning(dialog, "Kesalahan", "Semua kolom wajib diisi.")
        return
    audio_file = f"{audio}.wav"
    try:
        with DBConnection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO jadwal (hari, waktu, nama, audio_file) VALUES (?, ?, ?, ?)",
                      (hari, waktu, nama, audio_file))
        _load_jadwal_table(parent)
        from .schedule_loader import _load_today_schedule
        _load_today_schedule(parent)
        dialog.accept()
    except sqlite3.IntegrityError:
        QMessageBox.warning(dialog, "Duplikat", "Jadwal pada waktu ini sudah ada.")
    except Exception as e:
        logging.error(f"Gagal simpan jadwal: {e}")
        QMessageBox.critical(dialog, "Kesalahan", "Penyimpanan jadwal gagal.")

def _edit_jadwal(parent):
    row = parent.table_jadwal_hari.currentRow()
    if row < 0:
        QMessageBox.warning(parent, "Peringatan", "Harap pilih baris yang ingin diedit.")
        return

    col = -1
    for c in range(6):
        item = parent.table_jadwal_hari.item(row, c)
        if item and " - " in item.text():
            col = c
            break
    if col == -1:
        return

    text = parent.table_jadwal_hari.item(row, col).text()
    waktu_str, nama_str = text.split(" - ")
    hari_list = config["localization"]["days"][1:7]
    selected_hari = hari_list[col]

    dialog = QDialog(parent)
    dialog.setWindowTitle("Edit Jadwal")
    layout = QFormLayout(dialog)
    input_nama = QLineEdit(nama_str)
    layout.addRow("Nama:", input_nama)
    combo_hari = QComboBox()
    combo_hari.addItems(hari_list)
    combo_hari.setCurrentText(selected_hari)
    layout.addRow("Hari:", combo_hari)
    input_waktu = QTimeEdit()
    input_waktu.setDisplayFormat("HH:mm")
    h, m = map(int, waktu_str.split(":"))
    input_waktu.setTime(QTime(h, m))
    layout.addRow("Waktu:", input_waktu)

    audio_combo = QComboBox()
    with DBConnection() as conn:
        c = conn.cursor()
        c.execute("SELECT filename FROM audio_files")
        audio_list = [row[0] for row in c.fetchall()]
    audio_combo.addItems(audio_list)
    audio_combo.setCurrentText(os.path.splitext(nama_str)[0])
    layout.addRow("Audio:", audio_combo)

    btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addRow(btn_box)

    def save():
        w = input_waktu.time()
        if not w.isValid():
            QMessageBox.warning(dialog, "Error", "Waktu tidak valid!")
            return
        new_waktu = w.toString("HH:mm")
        new_nama = input_nama.text()
        new_audio = audio_combo.currentText()
        audio_file = f"{new_audio}.wav"
        try:
            with DBConnection() as conn:
                c = conn.cursor()
                c.execute("UPDATE jadwal SET waktu=?, nama=?, audio_file=? WHERE waktu=? AND hari=?",
                          (new_waktu, new_nama, audio_file, waktu_str, selected_hari))
            _load_jadwal_table(parent)
            from .schedule_loader import _load_today_schedule
            _load_today_schedule(parent)
            dialog.accept()
        except Exception as e:
            logging.error(f"Gagal edit jadwal: {e}")
            QMessageBox.critical(dialog, "Error", "Gagal menyimpan perubahan.")
    btn_box.accepted.connect(save)
    btn_box.rejected.connect(dialog.reject)
    dialog.exec_()


def _hapus_jadwal(parent):
    row = parent.table_jadwal_hari.currentRow()
    col = parent.table_jadwal_hari.currentColumn()
    if row < 0 or col < 0:
        QMessageBox.warning(parent, "Peringatan", "Harap pilih sel jadwal yang ingin dihapus.")
        return

    hari_list = config["localization"]["days"][1:7]
    selected_hari = hari_list[col]
    cell = parent.table_jadwal_hari.item(row, col)
    if not cell or not cell.text():
        QMessageBox.warning(parent, "Kesalahan", "Data tidak ditemukan di sel ini.")
        return

    waktu = cell.text().split(" - ")[0]
    reply = QMessageBox.question(
        parent,
        "Konfirmasi Hapus",
        f"Apakah Anda yakin ingin menghapus jadwal pada pukul {waktu} di hari {selected_hari}?"
    )
    if reply != QMessageBox.Yes:
        return

    try:
        with DBConnection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM jadwal WHERE hari = ? AND waktu = ?", (selected_hari, waktu))
        _load_jadwal_table(parent)
        from .schedule_loader import _load_today_schedule
        _load_today_schedule(parent)
        QMessageBox.information(parent, "Sukses", "Jadwal berhasil dihapus.")
    except Exception as e:
        logging.error(f"Gagal hapus jadwal: {e}")
        QMessageBox.critical(parent, "Error", "Gagal menghapus jadwal.")


def _test_bell(parent):
    row = parent.table_jadwal_hari.currentRow()
    col = parent.table_jadwal_hari.currentColumn()
    if row < 0 or col < 0:
        QMessageBox.warning(parent, "Peringatan", "Harap pilih sel jadwal terlebih dahulu.")
        return

    hari_list = config["localization"]["days"][1:7]
    selected_hari = hari_list[col]
    cell = parent.table_jadwal_hari.item(row, col)
    if not cell or not cell.text():
        QMessageBox.warning(parent, "Kesalahan", "Data tidak ditemukan di sel ini.")
        return

    waktu = cell.text().split(" - ")[0]
    try:
        with DBConnection() as conn:
            c = conn.cursor()
            c.execute("SELECT audio_file FROM jadwal WHERE hari = ? AND waktu = ?", (selected_hari, waktu))
            result = c.fetchone()
        if not result:
            QMessageBox.warning(parent, "Kesalahan", "Jadwal tidak ditemukan.")
            return

        audio_filename = result[0]
        base_name = os.path.splitext(audio_filename)[0]
        audio_path = os.path.join(config["paths"]["audio_folder"], f"{base_name}.wav")
        if not os.path.exists(audio_path):
            QMessageBox.warning(parent, "Kesalahan", f"File audio tidak ditemukan: {base_name}.wav")
            return

        parent.sound.stop()
        parent.sound.setSource(QUrl.fromLocalFile(audio_path))
        parent.sound.play()
        QMessageBox.information(parent, "Sukses", f"Memutar: {base_name}.wav")
    except Exception as e:
        logging.error(f"Gagal uji bel: {e}")
        QMessageBox.critical(parent, "Error", "Pemutaran gagal.")


def _copy_jadwal_harian(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Salin Jadwal Harian")
    dialog.resize(300, 150)
    layout = QFormLayout(dialog)
    combo_sumber = QComboBox()
    combo_sumber.addItems(config["localization"]["days"][1:7])
    combo_target = QComboBox()
    combo_target.addItems(config["localization"]["days"][1:7])
    combo_target.removeItem(0)
    layout.addRow("Salin dari:", combo_sumber)
    layout.addRow("Ke hari:", combo_target)

    btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addRow(btn_box)

    def proses_copy():
        sumber = combo_sumber.currentText()
        target = combo_target.currentText()
        if sumber == target:
            QMessageBox.warning(dialog, "Kesalahan", "Sumber dan tujuan tidak boleh sama.")
            return
        try:
            with DBConnection() as conn:
                c = conn.cursor()
                c.execute("SELECT waktu, nama, audio_file FROM jadwal WHERE hari = ?", (sumber,))
                jadwal = c.fetchall()
                if not jadwal:
                    reply = QMessageBox.question(dialog, "Konfirmasi", f"Tidak ada jadwal di {sumber}. Yakin kosongkan {target}?")
                    if reply == QMessageBox.Yes:
                        c.execute("DELETE FROM jadwal WHERE hari = ?", (target,))
                        QMessageBox.information(dialog, "Sukses", f"Jadwal {target} dikosongkan.")
                        _load_jadwal_table(parent)
                        from .schedule_loader import _load_today_schedule
                        _load_today_schedule(parent)
                    dialog.accept()
                    return
                reply = QMessageBox.question(dialog, "Konfirmasi", f"Apakah Anda yakin ingin menimpa jadwal {target} dengan jadwal dari {sumber}?")
                if reply != QMessageBox.Yes:
                    return
                c.execute("DELETE FROM jadwal WHERE hari = ?", (target,))
                for waktu, nama, audio in jadwal:
                    c.execute("INSERT INTO jadwal (hari, waktu, nama, audio_file) VALUES (?, ?, ?, ?)",
                              (target, waktu, nama, audio))
            QMessageBox.information(dialog, "Sukses", f"Jadwal berhasil disalin dari {sumber} ke {target}.")
            _load_jadwal_table(parent)
            from .schedule_loader import _load_today_schedule
            _load_today_schedule(parent)
            dialog.accept()
        except Exception as e:
            logging.error(f"Gagal salin jadwal: {e}")
            QMessageBox.critical(dialog, "Error", "Operasi gagal.")
    btn_box.accepted.connect(proses_copy)
    btn_box.rejected.connect(dialog.reject)
    dialog.exec_()
