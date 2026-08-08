"""Entry point: builds the QApplication, loads fonts, shows MainWindow."""
from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .fonts import load_embedded_fonts
from .main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ZetDoList")
    app.setQuitOnLastWindowClosed(False)
    load_embedded_fonts()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())