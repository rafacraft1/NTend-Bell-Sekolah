import os
import shutil
import wave
import logging
from PySide6.QtWidgets import QMessageBox, QInputDialog
from core.config import config

def _is_valid_wav(file_path):
    """Cek apakah file adalah WAV yang valid."""
    try:
        with wave.open(file_path, 'r') as f:
            return True
    except Exception:
        return False


def _upload_with_conflict(file, dest):
    """Upload file WAV dengan handling konflik nama."""
    if not os.path.exists(dest):
        if not _is_valid_wav(file):
            QMessageBox.critical(None, "Kesalahan", "File bukan format WAV yang valid.")
            return False
        shutil.copy(file, dest)
        return True

    msg = QMessageBox()
    msg.setWindowTitle("File Sudah Ada")
    msg.setText(f"File '{os.path.basename(dest)}' sudah tersedia.")
    msg.setInformativeText("Silakan pilih tindakan:")
    rename_btn = msg.addButton("Ubah Nama", QMessageBox.AcceptRole)
    overwrite_btn = msg.addButton("Timpa", QMessageBox.DestructiveRole)
    cancel_btn = msg.addButton("Batal", QMessageBox.RejectRole)
    msg.setIcon(QMessageBox.Warning)
    msg.exec_()
    clicked = msg.clickedButton()

    if clicked == cancel_btn:
        return False
    elif clicked == overwrite_btn:
        if not _is_valid_wav(file):
            QMessageBox.critical(None, "Kesalahan", "File sumber tidak valid.")
            return False
        shutil.copy(file, dest)
        return True
    else:
        dialog = QInputDialog()
        filename, ext = os.path.splitext(os.path.basename(dest))
        new_name, ok = QInputDialog.getText(dialog, "Ubah Nama", "Nama baru:", text=filename)
        if ok and new_name:
            new_dest = f"{config['paths']['audio_folder']}/{new_name}{ext}"
            if os.path.exists(new_dest):
                QMessageBox.warning(None, "Kesalahan", "Nama file baru sudah digunakan.")
                return False
            if not _is_valid_wav(file):
                QMessageBox.critical(None, "Kesalahan", "File sumber tidak valid.")
                return False
            shutil.copy(file, new_dest)
            return True
        return False
