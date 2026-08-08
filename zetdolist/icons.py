"""Generates the app's pixel-art checkmark icon at crisp sizes, used for
both the window/taskbar icon and the system tray icon."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap

from .theme import THEME

def _render_pixel_icon(size: int) -> QPixmap:
    """Renders the checkmark glyph directly at `size`, on an 8x8 logical
    pixel grid, so every size stays crisp instead of being blurrily scaled
    from one base image."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    cell = max(1, size // 8)
    grid = cell * 8
    offset = (size - grid) // 2

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(THEME["accent"]))
    painter.drawRect(offset, offset, grid, grid)

    painter.setBrush(QColor("#ffffff"))
    for col, row in [(2, 4), (3, 5), (4, 6), (5, 5), (6, 4), (7, 3)]:
        painter.drawRect(offset + col * cell, offset + row * cell, cell, cell)
    painter.end()
    return pix


def make_tray_icon() -> QIcon:
    """Builds a pixel-art checkmark QIcon with several crisp sizes baked in
    (rather than one image stretched), so it looks blocky everywhere: the
    window title bar, the taskbar, and the system tray."""
    icon = QIcon()
    for size in (16, 20, 24, 32, 40, 48, 64, 128, 256):
        icon.addPixmap(_render_pixel_icon(size))
    return icon
