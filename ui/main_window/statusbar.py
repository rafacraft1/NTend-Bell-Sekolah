from PySide6.QtWidgets import QLabel, QFrame

def setup_statusbar(parent):
    sb = parent.statusBar()
    sb.setStyleSheet("QStatusBar::item { border: none; }")

    parent.status_msg = QLabel("Siap")
    parent.status = QLabel("• Status: Aktif")
    parent.next_schedule_label = QLabel("Jadwal berikutnya: -")

    sep = QFrame()
    sep.setFrameShape(QFrame.VLine)
    sep.setStyleSheet("color:#aaa;")

    sb.addPermanentWidget(parent.status_msg)
    sb.addPermanentWidget(sep)
    sb.addPermanentWidget(parent.status)
    sb.addPermanentWidget(parent.next_schedule_label)
