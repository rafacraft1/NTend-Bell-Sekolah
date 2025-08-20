import sqlite3
import os
import logging
from core.config import config

class DBConnection:
    def __enter__(self):
        self.conn = sqlite3.connect(config["paths"]["database"])
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()


def _sync_audio_db():
    """Sinkronisasi dua arah: tambahkan file baru, hapus yang sudah tidak ada."""
    try:
        wav_files = [f for f in os.listdir(config["paths"]["audio_folder"]) if f.lower().endswith('.wav')]
        existing_names = [os.path.splitext(f)[0] for f in wav_files]

        with DBConnection() as conn:
            c = conn.cursor()

            # Hapus dari DB jika file tidak ada di folder
            c.execute("SELECT filename FROM audio_files")
            db_files = [row[0] for row in c.fetchall()]
            for name in db_files:
                if name not in existing_names:
                    c.execute("DELETE FROM audio_files WHERE filename = ?", (name,))
                    logging.info(f"[SYNC] Hapus dari DB: {name}")

            # Tambahkan ke DB jika baru
            for f in wav_files:
                base = os.path.splitext(f)[0]
                c.execute(
                    "INSERT OR IGNORE INTO audio_files (filename, filepath) VALUES (?, ?)",
                    (base, os.path.join(config["paths"]["audio_folder"], f))
                )

        logging.info(f"[SYNC] Sinkronisasi audio selesai: {len(wav_files)} file.")
    except Exception as e:
        logging.error(f"[ERROR] Gagal sinkron DB: {e}")
