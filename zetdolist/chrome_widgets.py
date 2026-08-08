"""Window chrome: night-sky background, the blocky panel + banner, the
custom title bar (replacing the OS one), and the invisible resize grips."""
from __future__ import annotations

import random

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .icons import _render_pixel_icon
from .theme import BORDER_W, SHADOW_OFFSET, THEME, TITLEBAR_H

# ============================================================================
# Background - navy night sky with blocky pixel sparkles
# ============================================================================

class BackgroundWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        rng = random.Random(7)
        self._stars = [
            (rng.random(), rng.random(), rng.choice([2, 2, 3]), rng.random() < 0.16)
            for _ in range(40)
        ]

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        rect = self.rect()
        grad = QLinearGradient(0, 0, 0, rect.height())
        grad.setColorAt(0.0, QColor(THEME["bg_top"]))
        grad.setColorAt(1.0, QColor(THEME["bg_bottom"]))
        painter.fillRect(rect, grad)

        sparkle = QColor(THEME["sparkle"])
        painter.setPen(Qt.PenStyle.NoPen)
        for x_ratio, y_ratio, size, is_big in self._stars:
            x = int(x_ratio * rect.width())
            y = int(y_ratio * rect.height())
            if is_big:
                self._draw_pixel_sparkle(painter, x, y, size * 2, sparkle)
            else:
                painter.setBrush(sparkle)
                painter.drawRect(x, y, size, size)

        # Faint CRT-style scanlines for extra retro texture
        scan = QColor(THEME["scanline"])
        scan.setAlpha(28)
        painter.setBrush(scan)
        for y in range(0, rect.height(), 3):
            painter.drawRect(0, y, rect.width(), 1)

        self._draw_edge_glow(painter, rect.width(), rect.height())

    def _draw_edge_glow(self, painter: QPainter, w: int, h: int) -> None:
        """A layered purple glow along the left, right, and bottom edges
        only - deliberately skipped at the top, which already has the
        horns anchoring it and doesn't need competing decoration."""
        glow = QColor(THEME["glow"])
        painter.setBrush(Qt.BrushStyle.NoBrush)
        bands = 4
        for i in range(bands):
            pen_color = QColor(glow)
            pen_color.setAlpha(max(10, 95 - i * 24))
            painter.setPen(QPen(pen_color, 2))
            inset = i * 3
            painter.drawLine(inset, 0, inset, h - inset)
            painter.drawLine(w - 1 - inset, 0, w - 1 - inset, h - inset)
            painter.drawLine(inset, h - 1 - inset, w - 1 - inset, h - 1 - inset)

        # A few small sparkle accents tracing the glow for extra flair
        accent = QColor(glow).lighter(140)
        for x_ratio, y in ((0.12, h - 14), (0.5, h - 10), (0.88, h - 14)):
            self._draw_pixel_sparkle(painter, int(w * x_ratio), y, 3, accent)

    @staticmethod
    def _draw_pixel_sparkle(painter: QPainter, cx: int, cy: int, unit: int, color: QColor) -> None:
        painter.setBrush(color)
        painter.drawRect(cx - unit // 2, cy - int(unit * 1.8), unit, unit)
        painter.drawRect(cx - unit // 2, cy + int(unit * 0.8), unit, unit)
        painter.drawRect(cx - int(unit * 1.8), cy - unit // 2, unit, unit)
        painter.drawRect(cx + int(unit * 0.8), cy - unit // 2, unit, unit)
        painter.drawRect(cx - unit // 2, cy - unit // 2, unit, unit)


# ============================================================================
# PixelBox - blocky rectangle with a solid drop shadow
# ============================================================================

class PixelBox(QWidget):
    def __init__(self, bg: str, border: str, shadow: str | None = None,
                 border_width: int = BORDER_W, shadow_offset: int = SHADOW_OFFSET,
                 corner_dots: bool = False, parent=None):
        super().__init__(parent)
        self.bg = QColor(bg)
        self.border = QColor(border)
        self.shadow = QColor(shadow) if shadow else None
        self.border_width = border_width
        self.shadow_offset = shadow_offset if shadow else 0
        self.corner_dots = corner_dots

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()
        bw = self.border_width
        so = self.shadow_offset

        if self.shadow is not None:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.shadow)
            painter.drawRect(QRectF(so, so, w - so, h - so))

        painter.setBrush(self.bg)
        pen = QPen(self.border, bw)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        inset = bw / 2
        painter.drawRect(QRectF(0, 0, w - so, h - so).adjusted(inset, inset, -inset, -inset))

        if self.corner_dots and w - so > 12 and h - so > 12:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(THEME["corner_dot"]))
            dot = max(3, bw)
            pad = bw
            for cx, cy in (
                (pad, pad),
                (w - so - pad - dot, pad),
                (pad, h - so - pad - dot),
                (w - so - pad - dot, h - so - pad - dot),
            ):
                painter.drawRect(int(cx), int(cy), dot, dot)


# ============================================================================
# PixelPanel - the card that holds a note's banner + task list
# ============================================================================

class PixelPanel(QWidget):
    """Blocky panel holding the task list, with a banner overlapping the top."""

    def __init__(self, title: str = "TO DO LIST", parent=None):
        super().__init__(parent)
        self.body = PixelBox(bg=THEME["panel_bg"], border=THEME["panel_border"], border_width=4,
                              corner_dots=True, parent=self)

        self.banner = PixelBox(bg=THEME["banner_bg"], border=THEME["banner_border"],
                                corner_dots=True, parent=self)
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(16, 10, 16, 10 + BORDER_W)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("AppTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.addWidget(self.title_label)
        self.banner.raise_()

        self.content = QWidget(self.body)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)
        self.resizeEvent(None)

    def resizeEvent(self, event):  # noqa: N802
        w, h = self.width(), self.height()
        self.banner.adjustSize()
        banner_h = max(self.banner.sizeHint().height(), 40)
        banner_w = max(self.banner.sizeHint().width(), 170)
        overlap = banner_h // 2

        self.body.setGeometry(0, overlap, w, h - overlap)
        self.banner.setGeometry((w - banner_w) // 2, 0, banner_w, banner_h)
        self.banner.raise_()
        self.content.setGeometry(0, overlap, w, h - overlap)
        if event is not None:
            super().resizeEvent(event)


# ============================================================================
# Custom title bar + resize grips (frameless window chrome)
# ============================================================================

class TitleBarButton(QWidget):
    """A tiny blocky button (minimize / close) drawn to match the rest of
    the pixel-art chrome, instead of the OS's native caption buttons."""

    clicked = pyqtSignal()

    def __init__(self, glyph: str, bg: str, hover_bg: str, press_bg: str,
                 glyph_color: str = "#ffffff", parent=None):
        super().__init__(parent)
        self.glyph = glyph
        self.bg = QColor(bg)
        self.hover_bg = QColor(hover_bg)
        self.press_bg = QColor(press_bg)
        self.glyph_color = QColor(glyph_color)
        self._hover = False
        self._pressed = False
        self.setFixedSize(28, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, event):  # noqa: N802
        self._hover = True
        self.update()

    def leaveEvent(self, event):  # noqa: N802
        self._hover = False
        self._pressed = False
        self.update()

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, event):  # noqa: N802
        was_pressed = self._pressed
        self._pressed = False
        self.update()
        if was_pressed and event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        color = self.press_bg if self._pressed else (self.hover_bg if self._hover else self.bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

        pen = QPen(self.glyph_color, 2)
        painter.setPen(pen)
        cx, cy = self.width() // 2, self.height() // 2
        if self.glyph == "minimize":
            painter.drawLine(cx - 6, cy + 5, cx + 6, cy + 5)
        else:  # close: pixel-blocky X
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.glyph_color)
            u = 2
            for i in range(-5, 6, u):
                painter.drawRect(cx + i, cy + i, u, u)
                painter.drawRect(cx + i, cy - i - u, u, u)


class PixelTitleBar(QWidget):
    """Replaces the native OS title bar with a blocky, on-brand one: app
    icon, pixel-font title, and hand-drawn minimize/close buttons. Dragging
    it moves the window via the OS's own window manager (startSystemMove),
    so it still snaps/behaves like a normal title bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(TITLEBAR_H)
        self.setAutoFillBackground(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(_render_pixel_icon(18))
        layout.addWidget(self.icon_label)

        self.title_label = QLabel("ZETDOLIST")
        self.title_label.setObjectName("TitleBarText")
        layout.addWidget(self.title_label)
        layout.addStretch(1)

        self.min_btn = TitleBarButton("minimize", THEME["titlebar_bg"], THEME["titlebar_btn_hover"],
                                       THEME["titlebar_btn_press"], THEME["titlebar_text"])
        self.min_btn.clicked.connect(self._minimize)
        layout.addWidget(self.min_btn)

        self.close_btn = TitleBarButton("close", THEME["titlebar_bg"], THEME["close_bg"],
                                         THEME["close_hover"], "#ffffff")
        self.close_btn.clicked.connect(self._close)
        layout.addWidget(self.close_btn)

        self._drag_pos = None

    def _minimize(self) -> None:
        self.window().showMinimized()

    def _close(self) -> None:
        self.window().close()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(THEME["titlebar_bg"]))
        painter.drawRect(self.rect())
        pen = QPen(QColor(THEME["titlebar_border"]), BORDER_W)
        painter.setPen(pen)
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()

    def mouseDoubleClickEvent(self, event):  # noqa: N802
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()


class ResizeGrip(QWidget):
    """An invisible strip along a window edge/corner that hands off to the
    OS's native resize behavior, so the frameless window can still be
    resized by dragging its borders like any normal window."""

    THICKNESS = 6

    _CURSORS = {
        Qt.Edge.TopEdge: Qt.CursorShape.SizeVerCursor,
        Qt.Edge.BottomEdge: Qt.CursorShape.SizeVerCursor,
        Qt.Edge.LeftEdge: Qt.CursorShape.SizeHorCursor,
        Qt.Edge.RightEdge: Qt.CursorShape.SizeHorCursor,
    }

    def __init__(self, edges: Qt.Edge, parent=None):
        super().__init__(parent)
        self.edges = edges
        cursor = self._cursor_for(edges)
        if cursor is not None:
            self.setCursor(cursor)

    def _cursor_for(self, edges: Qt.Edge):
        has_top = bool(edges & Qt.Edge.TopEdge)
        has_bottom = bool(edges & Qt.Edge.BottomEdge)
        has_left = bool(edges & Qt.Edge.LeftEdge)
        has_right = bool(edges & Qt.Edge.RightEdge)
        if (has_top and has_left) or (has_bottom and has_right):
            return Qt.CursorShape.SizeFDiagCursor
        if (has_top and has_right) or (has_bottom and has_left):
            return Qt.CursorShape.SizeBDiagCursor
        if has_top or has_bottom:
            return Qt.CursorShape.SizeVerCursor
        if has_left or has_right:
            return Qt.CursorShape.SizeHorCursor
        return None

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemResize(self.edges)


class DecorationOverlay(QWidget):
    """A separate, genuinely transparent top-level window that floats one
    piece of decorative art (horns, tail, ...) and follows the main
    window around - lets that art have a real see-through background
    without making the whole app window translucent.

    Click-through by design (WA_TransparentForMouseEvents): clicking
    where the art is should always reach whatever's beneath it, never
    the overlay itself.

    This widget never positions itself - the main window computes where
    each piece of decoration belongs (they don't all anchor the same
    way) and calls move()/set_pixmap() from its own moveEvent /
    resizeEvent / showEvent / hideEvent.
    """

    def __init__(self, pixmap: QPixmap, parent: QWidget | None = None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.natural_pixmap = pixmap
        self._label = QLabel(self)
        self.set_pixmap(pixmap)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        if pixmap.size() == self._label.size() and self._label.pixmap() is not None:
            return
        self._label.setPixmap(pixmap)
        self._label.resize(pixmap.size())
        self.resize(pixmap.size())

    def scaled_to_width(self, max_w: int) -> QPixmap:
        """Returns natural_pixmap scaled down to fit max_w - never
        upscaled past native resolution, so it never looks blurry."""
        if self.natural_pixmap.width() <= max_w:
            return self.natural_pixmap
        return self.natural_pixmap.scaledToWidth(max(1, max_w), Qt.TransformationMode.FastTransformation)
