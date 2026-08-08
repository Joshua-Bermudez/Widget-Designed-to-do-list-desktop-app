"""The "times completed" bar chart shown above a daily-reset note's list."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .theme import THEME

# ============================================================================
# Completion chart - horizontal bar chart of "times completed" per task,
# shown only above a daily-reset note's task list
# ============================================================================

def _truncate(text: str, max_len: int = 18) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


class HistoryBar(QWidget):
    """A single blocky bar filled to `fraction` of its width (0-1)."""

    HEIGHT = 14

    def __init__(self, fraction: float, parent=None):
        super().__init__(parent)
        self._fraction = max(0.0, min(1.0, fraction))
        self.setFixedHeight(self.HEIGHT)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()

        painter.setPen(QPen(QColor(THEME["row_border"]), 2))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(QRectF(0, 0, w - 1, h - 1))

        fill_w = max(0.0, w - 4) * self._fraction
        if fill_w >= 1:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(THEME["streak"]))
            painter.drawRect(QRectF(2, 2, fill_w, h - 4))


class TaskHistoryChart(QWidget):
    """Lists every task in the active daily note with a bar showing how
    many times it's been checked off at reset time, all-time, ranked
    highest-first."""

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        header = QLabel("TIMES COMPLETED")
        header.setObjectName("ChartHeader")
        outer.addWidget(header)

        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(6)
        outer.addWidget(self.rows_container)

        self._row_widgets: list[QWidget] = []

    def set_data(self, data: list[tuple[str, int]]) -> None:
        for w in self._row_widgets:
            self.rows_layout.removeWidget(w)
            w.deleteLater()
        self._row_widgets = []

        if not data:
            empty = QLabel("No completions logged yet - finish a daily reset to start tracking.")
            empty.setObjectName("ChartEmpty")
            empty.setWordWrap(True)
            self.rows_layout.addWidget(empty)
            self._row_widgets.append(empty)
            return

        max_count = max(count for _, count in data) or 1
        for text, count in data:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            label = QLabel(_truncate(text))
            label.setObjectName("ChartTaskLabel")
            label.setFixedWidth(130)
            row_layout.addWidget(label)

            row_layout.addWidget(
                HistoryBar(count / max_count), stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter
            )

            count_label = QLabel(str(count))
            count_label.setObjectName("ChartCountLabel")
            count_label.setFixedWidth(26)
            count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(count_label)

            self.rows_layout.addWidget(row)
            self._row_widgets.append(row)
