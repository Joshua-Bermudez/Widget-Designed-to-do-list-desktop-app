"""Loads optional decorative pixel-art assets (horns, tail, button skins,
...) from the assets/ folder next to ZetDoList.pyw.

Missing files are skipped gracefully - a filename typo or an asset you
haven't drawn yet never crashes the app, it just doesn't render."""
from __future__ import annotations

import os
import sys

from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QPushButton


def resource_path(relative_path: str) -> str:
    """Resolves a path both when running from source and when frozen into
    a PyInstaller .exe (which unpacks bundled files into a temp folder
    referenced by sys._MEIPASS instead of your normal project folder)."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


def load_asset(filename: str) -> QPixmap | None:
    """Loads assets/<filename>. Returns None instead of raising if the
    file is missing or fails to decode."""
    path = resource_path(os.path.join("assets", filename))
    if not os.path.exists(path):
        return None
    pixmap = QPixmap(path)
    return pixmap if not pixmap.isNull() else None


def apply_button_image(button: QPushButton, filename: str) -> bool:
    """Skins a button with a pixel-art image instead of the drawn
    rectangle style. The image should already be sized/shaped exactly
    like you want the finished button to look. Returns True if it found
    and applied the file, False if it skipped (missing file)."""
    pixmap = load_asset(filename)
    if pixmap is None:
        return False
    button.setText("")
    button.setIcon(QIcon(pixmap))
    button.setIconSize(pixmap.size())
    button.setFixedSize(pixmap.size())
    button.setStyleSheet("QPushButton { border: none; background: transparent; padding: 0px; }")
    return True
