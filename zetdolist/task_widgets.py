"""The checkbox, the collapse/expand arrow, and the task row that combines
them with the label and optional due-date line."""
from __future__ import annotations

from datetime import date

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .chrome_widgets import PixelBox
from .markdown_sync import TodoItem
from .theme import SHADOW_OFFSET, THEME

# ============================================================================
# Widgets - pixel checkbox + collapse arrow + task row
# ============================================================================

class CheckBox(QWidget):
    toggled = pyqtSignal(bool)
    SIZE = 22

    def __init__(self, checked: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self._checked = checked
        self._hover = False
        self._locked = False
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, value: bool, emit: bool = False) -> None:
        if self._checked == value:
            return
        self._checked = value
        self.update()
        if emit:
            self.toggled.emit(self._checked)

    def set_locked(self, value: bool) -> None:
        """A locked checkbox shows a computed value (e.g. derived from
        sub-items) and can't be toggled directly by clicking it."""
        self._locked = value
        self.setCursor(Qt.CursorShape.ArrowCursor if value else Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):  # noqa: N802
        if self._locked:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_checked(not self._checked, emit=True)

    def enterEvent(self, event):  # noqa: N802
        self._hover = True
        self.update()

    def leaveEvent(self, event):  # noqa: N802
        self._hover = False
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        border = QColor(THEME["accent"])
        pen = QPen(border, 3)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)

        if self._checked:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(border)
            painter.drawRect(1, 1, self.SIZE - 2, self.SIZE - 2)
            painter.setBrush(QColor("#ffffff"))
            u = max(2, self.SIZE // 8)
            cells = [(2, 4), (3, 5), (4, 6), (5, 5), (6, 4), (7, 3), (8, 2)]
            for col, row in cells:
                painter.drawRect(col * u, row * u, u, u)
        else:
            bg = QColor("#f0f0ff") if self._hover else QColor("#ffffff")
            painter.setPen(pen)
            painter.setBrush(bg)
            painter.drawRect(2, 2, self.SIZE - 4, self.SIZE - 4)


class CollapseToggle(QWidget):
    """A small blocky triangle - points right when collapsed, down when
    expanded - used to hide/show a parent task's sub-items."""

    toggled = pyqtSignal()
    SIZE = 18

    def __init__(self, collapsed: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self._collapsed = collapsed
        self._hover = False
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggled.emit()

    def enterEvent(self, event):  # noqa: N802
        self._hover = True
        self.update()

    def leaveEvent(self, event):  # noqa: N802
        self._hover = False
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(THEME["sparkle"] if self._hover else THEME["accent"]))

        cx, cy = self.SIZE / 2, self.SIZE / 2
        s = 5.0
        if self._collapsed:
            points = [QPointF(cx - s * 0.5, cy - s), QPointF(cx - s * 0.5, cy + s), QPointF(cx + s, cy)]
        else:
            points = [QPointF(cx - s, cy - s * 0.5), QPointF(cx + s, cy - s * 0.5), QPointF(cx, cy + s)]
        painter.drawPolygon(QPolygonF(points))


class TaskRow(QWidget):
    toggled = pyqtSignal(int, bool)
    collapse_requested = pyqtSignal(str)

    def __init__(self, item: TodoItem, has_children: bool = False, collapsed: bool = False, parent=None):
        super().__init__(parent)
        self.line_index = item.line_index

        outer = QHBoxLayout(self)
        outer.setContentsMargins(item.indent_level * 24, 0, 0, 0)

        self.box = PixelBox(bg=THEME["row_bg"], border=THEME["row_border"], shadow=THEME["shadow"])
        inner = QHBoxLayout(self.box)
        inner.setContentsMargins(14, 8, 14, 8 + SHADOW_OFFSET)
        inner.setSpacing(12)

        if has_children:
            arrow = CollapseToggle(collapsed=collapsed)
            arrow.toggled.connect(lambda: self.collapse_requested.emit(item.text))
            inner.addWidget(arrow)
        else:
            slot = QWidget()
            slot.setFixedSize(CollapseToggle.SIZE, CollapseToggle.SIZE)
            inner.addWidget(slot)

        self.checkbox = CheckBox(checked=item.checked)
        self.checkbox.set_locked(has_children)
        self.checkbox.toggled.connect(self._on_toggled)
        inner.addWidget(self.checkbox)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        self.label = QLabel(item.text)
        self.label.setObjectName("TaskLabel")
        self.label.setWordWrap(True)
        text_col.addWidget(self.label)

        due = item.due_date
        if due is not None:
            overdue = due < date.today() and not item.checked
            due_text = f"{'OVERDUE' if overdue else 'DUE'} {due.isoformat()}"
            due_label = QLabel(due_text)
            due_label.setObjectName("DueLabel")
            text_col.addWidget(due_label)

        self._apply_label_style(item.checked)
        inner.addLayout(text_col, 1)
        outer.addWidget(self.box)

    def _apply_label_style(self, checked: bool) -> None:
        font = QFont(self.label.font())
        font.setStrikeOut(checked)
        self.label.setFont(font)
        self.label.setProperty("done", "true" if checked else "false")
        self.label.style().unpolish(self.label)
        self.label.style().polish(self.label)

    def _on_toggled(self, checked: bool) -> None:
        self._apply_label_style(checked)
        self.toggled.emit(self.line_index, checked)
