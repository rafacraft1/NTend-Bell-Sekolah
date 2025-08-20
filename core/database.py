# core/database.py
import sqlite3
import os
import logging
from core.config import config
DB_NAME = config["paths"]["database"]
AUDIO_FOLDER = config["paths"]["audio_folder"]
default_audio = config["defaults"]["audio_file"]
def init_db():
    if not os.path.exists(AUDIO_FOLDER):
        os.makedirs(AUDIO_FOLDER)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabel jadwal dengan UNIQUE constraint
    c.execute('''
        CREATE TABLE IF NOT EXISTS jadwal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hari TEXT NOT NULL,
            waktu TEXT NOT NULL,
            nama TEXT NOT NULL,
            audio_file TEXT DEFAULT '{default_audio}',
            UNIQUE(hari, waktu) ON CONFLICT ROLLBACK
        )
    ''')
    # Tabel audio_files
    c.execute('''
        CREATE TABLE IF NOT EXISTS audio_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            filepath TEXT NOT NULL
        )
    ''')
    # Kosongkan dulu untuk sinkronisasi ulang
    c.execute("DELETE FROM audio_files")
    # Baca semua file .wav dari folder
    try:
        wav_files = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith('.wav')]
    except Exception as e:
        logging.error(f"Gagal baca folder audio: {e}")
        wav_files = []
    # Masukkan ke database
    for filename in wav_files:
        base_name = os.path.splitext(filename)[0]
        filepath = f"{AUDIO_FOLDER}/{filename}"
        c.execute("INSERT OR IGNORE INTO audio_files (filename, filepath) VALUES (?, ?)",
                  (base_name, filepath))
    # Tambahkan default jika tidak ada
    if not wav_files:
        c.execute("INSERT OR IGNORE INTO audio_files (filename, filepath) VALUES (?, ?)",
                  ("bell", f"{AUDIO_FOLDER}/bell.wav"))
    conn.commit()
    conn.close()
    logging.info(f"Database audio disinkronisasi dari {len(wav_files)} file di {AUDIO_FOLDER}/")