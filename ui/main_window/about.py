from PySide6.QtWidgets import QMessageBox

def show_tentang(parent):
    msg = QMessageBox(parent)
    msg.setWindowTitle("Tentang SchoolBell")
    msg.setText("""
        <h3>🏫 SchoolBell V1.0</h3>
        <p>Aplikasi penjadwal bel sekolah otomatis.</p>
        <p><b>Dikembangkan dengan Python & PySide6</b></p>
        <p>Versi: 1.0<br>© 2025 Nurindra</p>
    """)
    msg.exec_()
