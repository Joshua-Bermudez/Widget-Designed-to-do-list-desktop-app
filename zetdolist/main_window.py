"""MainWindow - wires the config, markdown sync, history, and every widget
together into the running app."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from PyQt6.QtCore import QEvent, QFileSystemWatcher, Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from .assets import load_asset
from .chart_widgets import TaskHistoryChart
from .chrome_widgets import BackgroundWidget, DecorationOverlay, PixelBox, PixelPanel, PixelTitleBar, ResizeGrip
from .config import (
    get_active_index,
    get_notes,
    get_setting,
    set_active_index,
    set_notes,
    set_setting,
)
from .history import get_completion_counts, record_completions
from .icons import make_tray_icon
from .markdown_sync import (
    TodoItem,
    append_task,
    collapsed_hidden_line_indices,
    effective_checked,
    parse_todo_file,
    reset_all_checkboxes,
    set_checked,
)
from .task_widgets import TaskRow
from .theme import SHADOW_OFFSET, STYLESHEET, THEME

# ============================================================================
# Main window
# ============================================================================

SORT_MODES = ["default", "az", "incomplete_first"]


SORT_LABELS = {"default": "SORT: FILE", "az": "SORT: A-Z", "incomplete_first": "SORT: TODO FIRST"}


FILTER_MODES = ["all", "active", "done"]


FILTER_LABELS = {"all": "SHOW: ALL", "active": "SHOW: ACTIVE", "done": "SHOW: DONE"}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._app_active = True
        self.setWindowTitle("ZetDoList")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.resize(480, 700)
        self.setStyleSheet(STYLESHEET)
        self.setWindowIcon(make_tray_icon())
        self._resize_grips: list[ResizeGrip] = []

        self.notes: list[dict] = get_notes()
        self.active_index: int = min(get_active_index(), max(0, len(self.notes) - 1))
        self.sort_mode: str = get_setting("sort_mode", "default")
        self.filter_mode: str = get_setting("filter_mode", "all")
        self.always_on_top: bool = get_setting("always_on_top", False)
        self.show_chart: bool = get_setting("show_chart", True)

        self.rows: list[QWidget] = []
        self._notified_today: set[tuple] = set()

        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self._on_file_changed)

        self._build_ui()
        self._setup_resize_grips()
        self._setup_tray()
        QApplication.instance().applicationStateChanged.connect(self._on_app_state_changed)

        if self.always_on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        if not self.notes:
            self._add_note()
        else:
            self._watch_all_notes()
            self._check_daily_resets()
            self._rebuild_tabs()
            self.reload_tasks()

        self.reset_timer = QTimer(self)
        self.reset_timer.timeout.connect(self._check_daily_resets)
        self.reset_timer.start(60_000)

        self.notify_timer = QTimer(self)
        self.notify_timer.timeout.connect(self._check_due_notifications)
        self.notify_timer.start(5 * 60_000)
        QTimer.singleShot(2000, self._check_due_notifications)

    # ---------- UI construction ----------

    def _build_ui(self) -> None:
        self.window_frame = QWidget()
        self.window_frame.setObjectName("WindowFrame")
        frame_layout = QVBoxLayout(self.window_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # --- Optional decorative pixel-art assets (skipped gracefully if
        # the files aren't in assets/ yet) ---
        self._horns_pixmap = load_asset("horns.png")
        self._tail_pixmap = load_asset("tail.png")
        self._horns_overlap = 20  # how many px of the horns sink into the title bar
        self._tail_edge_overlap = 14  # how many px of the tail sink into the right edge

        self.horns_overlay = DecorationOverlay(self._horns_pixmap) if self._horns_pixmap is not None else None
        self.tail_overlay = DecorationOverlay(self._tail_pixmap) if self._tail_pixmap is not None else None

        self.title_bar = PixelTitleBar()
        frame_layout.addWidget(self.title_bar)

        background = BackgroundWidget()
        frame_layout.addWidget(background, stretch=1)
        outer = QVBoxLayout(background)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(8)

        # Tabs row
        self.tabs_row = QWidget()
        self.tabs_layout = QHBoxLayout(self.tabs_row)
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs_layout.setSpacing(2)
        outer.addWidget(self.tabs_row)

        # Controls row
        controls = QWidget()
        c_layout = QHBoxLayout(controls)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(4)

        self.streak_label = QLabel("")
        self.streak_label.setObjectName("StreakLabel")
        c_layout.addWidget(self.streak_label, stretch=1)

        self.sort_btn = QPushButton(SORT_LABELS[self.sort_mode])
        self.sort_btn.setObjectName("IconButton")
        self.sort_btn.clicked.connect(self._cycle_sort)
        c_layout.addWidget(self.sort_btn)

        self.filter_btn = QPushButton(FILTER_LABELS[self.filter_mode])
        self.filter_btn.setObjectName("IconButton")
        self.filter_btn.clicked.connect(self._cycle_filter)
        c_layout.addWidget(self.filter_btn)

        self.daily_btn = QPushButton("DAILY: OFF")
        self.daily_btn.setObjectName("IconButton")
        self.daily_btn.clicked.connect(self._toggle_daily_reset)
        c_layout.addWidget(self.daily_btn)

        outer.addWidget(controls)

        controls2 = QWidget()
        c2_layout = QHBoxLayout(controls2)
        c2_layout.setContentsMargins(0, 0, 0, 0)
        c2_layout.setSpacing(4)

        self.file_label = QLabel("No file linked")
        self.file_label.setObjectName("FileLabel")
        c2_layout.addWidget(self.file_label, stretch=1)

        self.pin_btn = QPushButton("PIN: OFF")
        self.pin_btn.setObjectName("IconButton")
        self.pin_btn.clicked.connect(self._toggle_pin)
        c2_layout.addWidget(self.pin_btn)

        self.chart_btn = QPushButton("CHART: ON" if self.show_chart else "CHART: OFF")
        self.chart_btn.setObjectName("IconButtonOn" if self.show_chart else "IconButton")
        self.chart_btn.clicked.connect(self._toggle_chart_visible)
        c2_layout.addWidget(self.chart_btn)

        refresh_btn = QPushButton("REFRESH")
        refresh_btn.setObjectName("IconButton")
        refresh_btn.clicked.connect(self.reload_tasks)
        c2_layout.addWidget(refresh_btn)

        outer.addWidget(controls2)

        self.panel = PixelPanel()
        outer.addWidget(self.panel, stretch=1)

        # Completion chart - only shown on notes with daily reset turned on
        self.chart_wrap = QWidget(self.panel.content)
        chart_wrap_layout = QVBoxLayout(self.chart_wrap)
        chart_wrap_layout.setContentsMargins(20, 16, 20, 0)
        self.chart_box = PixelBox(bg=THEME["row_bg"], border=THEME["row_border"], shadow=THEME["shadow"])
        chart_box_layout = QVBoxLayout(self.chart_box)
        chart_box_layout.setContentsMargins(14, 10, 14, 10 + SHADOW_OFFSET)
        self.history_chart = TaskHistoryChart()
        chart_box_layout.addWidget(self.history_chart)
        chart_wrap_layout.addWidget(self.chart_box)
        self.chart_wrap.hide()
        self.panel.content_layout.addWidget(self.chart_wrap)

        self.scroll = QScrollArea(self.panel.content)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent;")
        self.list_container = QWidget()
        self.list_container.setObjectName("ListContainer")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(20, 24, 20, 12)
        self.list_layout.setSpacing(14)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.list_container)
        self.panel.content_layout.addWidget(self.scroll, stretch=1)

        # Quick-add row, pinned at the bottom of the panel
        quick_add = QWidget()
        qa_layout = QHBoxLayout(quick_add)
        qa_layout.setContentsMargins(20, 6, 20, 20)
        qa_layout.setSpacing(8)
        self.quick_add_input = QLineEdit()
        self.quick_add_input.setObjectName("QuickAdd")
        self.quick_add_input.setPlaceholderText("Add a task...")
        self.quick_add_input.returnPressed.connect(self._quick_add_task)
        qa_layout.addWidget(self.quick_add_input, stretch=1)
        add_btn = QPushButton("ADD")
        add_btn.setObjectName("IconButton")
        add_btn.clicked.connect(self._quick_add_task)
        qa_layout.addWidget(add_btn)
        self.panel.content_layout.addWidget(quick_add)

        self.setCentralWidget(self.window_frame)
        self._sync_decorations()

    def _setup_resize_grips(self) -> None:
        edges = {
            "top": Qt.Edge.TopEdge,
            "bottom": Qt.Edge.BottomEdge,
            "left": Qt.Edge.LeftEdge,
            "right": Qt.Edge.RightEdge,
            "top_left": Qt.Edge.TopEdge | Qt.Edge.LeftEdge,
            "top_right": Qt.Edge.TopEdge | Qt.Edge.RightEdge,
            "bottom_left": Qt.Edge.BottomEdge | Qt.Edge.LeftEdge,
            "bottom_right": Qt.Edge.BottomEdge | Qt.Edge.RightEdge,
        }
        self._grips: dict[str, ResizeGrip] = {
            name: ResizeGrip(edge, self.window_frame) for name, edge in edges.items()
        }
        for grip in self._grips.values():
            grip.raise_()
        self._layout_resize_grips()

    def _layout_resize_grips(self) -> None:
        if not getattr(self, "_grips", None):
            return
        t = ResizeGrip.THICKNESS
        w, h = self.window_frame.width(), self.window_frame.height()
        self._grips["top"].setGeometry(t, 0, max(0, w - 2 * t), t)
        self._grips["bottom"].setGeometry(t, h - t, max(0, w - 2 * t), t)
        self._grips["left"].setGeometry(0, t, t, max(0, h - 2 * t))
        self._grips["right"].setGeometry(w - t, t, t, max(0, h - 2 * t))
        self._grips["top_left"].setGeometry(0, 0, t, t)
        self._grips["top_right"].setGeometry(w - t, 0, t, t)
        self._grips["bottom_left"].setGeometry(0, h - t, t, t)
        self._grips["bottom_right"].setGeometry(w - t, h - t, t, t)
        for grip in self._grips.values():
            grip.raise_()

    def _sync_decorations(self) -> None:
        horns_overlay = getattr(self, "horns_overlay", None)
        if horns_overlay is not None:
            pixmap = horns_overlay.scaled_to_width(max(40, self.width() - 16))
            horns_overlay.set_pixmap(pixmap)
            x = self.x() + (self.width() - pixmap.width()) // 2
            y = self.y() - pixmap.height() + self._horns_overlap
            horns_overlay.move(x, y)

        tail_overlay = getattr(self, "tail_overlay", None)
        if tail_overlay is not None:
            pixmap = tail_overlay.natural_pixmap
            x = self.x() + self.width() - self._tail_edge_overlap
            y = self.y() + self.height() - pixmap.height() - 4
            tail_overlay.move(x, y)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if getattr(self, "window_frame", None) is None:
            return
        self._layout_resize_grips()
        self._sync_decorations()

    def moveEvent(self, event) -> None:  # noqa: N802
        super().moveEvent(event)
        self._sync_decorations()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._update_overlay_visibility()

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        self._update_overlay_visibility()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._update_overlay_visibility()

    def _on_app_state_changed(self, state) -> None:
        """Fires when focus moves to/from another application entirely -
        the piece 'minimized' and 'hidden to tray' don't cover. Without
        this, WindowStaysOnTopHint keeps the horns/tail floating over
        whatever app you alt-tab to."""
        self._app_active = state == Qt.ApplicationState.ApplicationActive
        self._update_overlay_visibility()

    def _update_overlay_visibility(self) -> None:
        overlays = [o for o in (getattr(self, "horns_overlay", None), getattr(self, "tail_overlay", None)) if o]
        if not overlays:
            return
        should_show = (
            self.isVisible()
            and not (self.windowState() & Qt.WindowState.WindowMinimized)
            and getattr(self, "_app_active", True)
        )
        if should_show:
            self._sync_decorations()
        for overlay in overlays:
            overlay.setVisible(should_show)

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = None
            return
        self.tray = QSystemTrayIcon(make_tray_icon(), self)
        self.tray.setToolTip("ZetDoList")
        menu = QMenu()
        show_action = menu.addAction("Show ZetDoList")
        show_action.triggered.connect(self._show_from_tray)
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.instance().quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.tray is not None:
            event.ignore()
            self.hide()
            self.tray.showMessage(
                "ZetDoList", "Still running in the tray.", QSystemTrayIcon.MessageIcon.Information, 2000
            )
        else:
            for overlay in (self.horns_overlay, self.tail_overlay):
                if overlay is not None:
                    overlay.close()
            event.accept()

    # ---------- Notes / tabs ----------

    def _rebuild_tabs(self) -> None:
        while self.tabs_layout.count():
            item = self.tabs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, note in enumerate(self.notes):
            btn = QPushButton(note["name"].upper())
            btn.setObjectName("TabButtonActive" if i == self.active_index else "TabButton")
            btn.clicked.connect(lambda _checked, idx=i: self._switch_note(idx))
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, idx=i, b=btn: self._show_tab_menu(b, pos, idx)
            )
            self.tabs_layout.addWidget(btn)

        add_btn = QPushButton("+")
        add_btn.setObjectName("TabButton")
        add_btn.clicked.connect(self._add_note)
        self.tabs_layout.addWidget(add_btn)
        self.tabs_layout.addStretch(1)

    def _switch_note(self, index: int) -> None:
        if index == self.active_index:
            return
        self.active_index = index
        set_active_index(index)
        self._rebuild_tabs()
        self.reload_tasks()

    def _add_note(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select an Obsidian note", "", "Markdown files (*.md)")
        if not path:
            return
        default_name = Path(path).stem
        name, ok = QInputDialog.getText(self, "Name this list", "Display name:", text=default_name)
        if not ok:
            return
        note = {
            "name": name.strip() or default_name,
            "path": path,
            "daily_reset": False,
            "last_reset_date": None,
            "streak": 0,
        }
        self.notes.append(note)
        self.active_index = len(self.notes) - 1
        set_notes(self.notes)
        set_active_index(self.active_index)
        self._watch_all_notes()
        self._rebuild_tabs()
        self.reload_tasks()

    def _show_tab_menu(self, button: QPushButton, pos, index: int) -> None:
        menu = QMenu(self)
        remove_action = menu.addAction("Remove")
        chosen = menu.exec(button.mapToGlobal(pos))
        if chosen == remove_action:
            self._remove_note(index)

    def _remove_note(self, index: int) -> None:
        if not self.notes or index >= len(self.notes):
            return
        if len(self.notes) == 1:
            QMessageBox.information(self, "ZetDoList", "You need at least one linked note.")
            return
        note = self.notes[index]
        reply = QMessageBox.question(
            self, "Remove note",
            f'Unlink "{note["name"]}" from ZetDoList?\n(The Obsidian file itself is not touched.)',
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        del self.notes[index]
        if index < self.active_index:
            self.active_index -= 1
        elif index == self.active_index:
            self.active_index = max(0, self.active_index - 1)
        self.active_index = min(self.active_index, len(self.notes) - 1)
        set_notes(self.notes)
        set_active_index(self.active_index)
        self._watch_all_notes()
        self._rebuild_tabs()
        self.reload_tasks()

    def _remove_active_note(self) -> None:
        self._remove_note(self.active_index)

    @property
    def active_note(self) -> dict | None:
        if not self.notes:
            return None
        return self.notes[self.active_index]

    def _watch_all_notes(self) -> None:
        if self.watcher.files():
            self.watcher.removePaths(self.watcher.files())
        for note in self.notes:
            if os.path.exists(note["path"]):
                self.watcher.addPath(note["path"])

    def _on_file_changed(self, path: str) -> None:
        if path not in self.watcher.files() and os.path.exists(path):
            self.watcher.addPath(path)
        QTimer.singleShot(150, self.reload_tasks)

    # ---------- Daily reset ----------

    def _toggle_daily_reset(self) -> None:
        note = self.active_note
        if note is None:
            return
        note["daily_reset"] = not note.get("daily_reset", False)
        if note["daily_reset"]:
            note["last_reset_date"] = date.today().isoformat()
            note["streak"] = note.get("streak", 0)
        set_notes(self.notes)
        self.reload_tasks()

    def _check_daily_resets(self) -> None:
        today = date.today().isoformat()
        changed = False
        for note in self.notes:
            if not note.get("daily_reset"):
                continue
            if note.get("last_reset_date") == today:
                continue
            if not os.path.exists(note["path"]):
                continue
            items = parse_todo_file(note["path"])
            if items:
                all_done = all(effective_checked(it) for it in items)
                note["streak"] = note.get("streak", 0) + 1 if all_done else 0
                completed = [it.text for it in items if effective_checked(it)]
                if completed:
                    record_completions(note["path"], note.get("last_reset_date") or today, completed)
            reset_all_checkboxes(note["path"], [it.line_index for it in items])
            note["last_reset_date"] = today
            changed = True
        if changed:
            set_notes(self.notes)
            self._notified_today.clear()
            self.reload_tasks()

    # ---------- Notifications ----------

    def _check_due_notifications(self) -> None:
        if self.tray is None:
            return
        today = date.today()
        for note in self.notes:
            if not os.path.exists(note["path"]):
                continue
            for item in parse_todo_file(note["path"]):
                if effective_checked(item):
                    continue
                due = item.due_date
                if due is None or due > today:
                    continue
                key = (note["path"], item.line_index, today.isoformat())
                if key in self._notified_today:
                    continue
                self._notified_today.add(key)
                status = "overdue" if due < today else "due today"
                self.tray.showMessage(
                    f"{note['name']}: task {status}", item.text, QSystemTrayIcon.MessageIcon.Information, 6000
                )

    # ---------- Sort / filter / pin ----------

    def _cycle_sort(self) -> None:
        idx = (SORT_MODES.index(self.sort_mode) + 1) % len(SORT_MODES)
        self.sort_mode = SORT_MODES[idx]
        set_setting("sort_mode", self.sort_mode)
        self.sort_btn.setText(SORT_LABELS[self.sort_mode])
        self.reload_tasks()

    def _cycle_filter(self) -> None:
        idx = (FILTER_MODES.index(self.filter_mode) + 1) % len(FILTER_MODES)
        self.filter_mode = FILTER_MODES[idx]
        set_setting("filter_mode", self.filter_mode)
        self.filter_btn.setText(FILTER_LABELS[self.filter_mode])
        self.reload_tasks()

    def _toggle_pin(self) -> None:
        self.always_on_top = not self.always_on_top
        set_setting("always_on_top", self.always_on_top)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.always_on_top)
        self.show()
        self.pin_btn.setText("PIN: ON" if self.always_on_top else "PIN: OFF")
        self.pin_btn.setObjectName("IconButtonOn" if self.always_on_top else "IconButton")
        self.pin_btn.setStyleSheet("")  # force re-polish

    def _toggle_chart_visible(self) -> None:
        self.show_chart = not self.show_chart
        set_setting("show_chart", self.show_chart)
        self.chart_btn.setText("CHART: ON" if self.show_chart else "CHART: OFF")
        self.chart_btn.setObjectName("IconButtonOn" if self.show_chart else "IconButton")
        self.chart_btn.setStyleSheet("")  # force re-polish
        self.reload_tasks()

    def _quick_add_task(self) -> None:
        text = self.quick_add_input.text().strip()
        note = self.active_note
        if not text or note is None:
            return
        append_task(note["path"], text)
        self.quick_add_input.clear()
        self.reload_tasks()

    # ---------- Rendering ----------

    def _apply_sort_filter(self, items: list[TodoItem]) -> list[TodoItem]:
        result = items
        if self.filter_mode == "active":
            result = [it for it in result if not it.checked]
        elif self.filter_mode == "done":
            result = [it for it in result if it.checked]

        if self.sort_mode == "az":
            result = sorted(result, key=lambda it: it.text.lower())
        elif self.sort_mode == "incomplete_first":
            result = sorted(result, key=lambda it: it.checked)
        return result

    def _update_status_row(self) -> None:
        note = self.active_note
        if note is None:
            self.file_label.setText("No note linked")
            self.streak_label.setText("")
            self.panel.set_title("TO DO LIST")
            self.daily_btn.setText("DAILY: OFF")
            return

        self.file_label.setText(f"FILE: {os.path.basename(note['path'])}")
        self.panel.set_title(note["name"].upper())
        is_daily = note.get("daily_reset", False)
        self.daily_btn.setText("DAILY: ON" if is_daily else "DAILY: OFF")
        self.daily_btn.setObjectName("IconButtonOn" if is_daily else "IconButton")
        self.daily_btn.setStyleSheet("")
        if is_daily:
            streak = note.get("streak", 0)
            self.streak_label.setText(f"STREAK: {streak}")
        else:
            self.streak_label.setText("")

    def _sync_auto_checks(self, note: dict, items: list[TodoItem]) -> None:
        """Parent items (ones with sub-items) are kept in sync with their
        children: once every sub-item is done, the parent checks itself
        off too - both in the app and back in the Obsidian file. Runs on
        every reload, so it applies no matter where the file was edited."""
        for item in items:
            if not item.children:
                continue
            derived = effective_checked(item)
            if derived != item.checked:
                set_checked(note["path"], item.line_index, derived)
                item.checked = derived

    def _refresh_chart(self, note: dict, items: list[TodoItem]) -> None:
        """Shows the completion chart only for daily-reset notes, and only
        if the user hasn't hidden it via the CHART button, ranking the
        note's current tasks by all-time times-completed."""
        if not note.get("daily_reset", False) or not self.show_chart:
            self.chart_wrap.hide()
            return
        counts = get_completion_counts(note["path"])
        seen: set[str] = set()
        data: list[tuple[str, int]] = []
        for it in items:
            if it.text in seen:
                continue
            seen.add(it.text)
            data.append((it.text, counts.get(it.text, 0)))
        data.sort(key=lambda pair: (-pair[1], pair[0].lower()))
        self.history_chart.set_data(data)
        self.chart_wrap.show()

    def reload_tasks(self) -> None:
        self._update_status_row()
        note = self.active_note
        if note is None or not os.path.exists(note["path"]):
            for row in self.rows:
                self.list_layout.removeWidget(row)
                row.deleteLater()
            self.rows = []
            self.chart_wrap.hide()
            return

        items = parse_todo_file(note["path"])
        self._sync_auto_checks(note, items)
        self._refresh_chart(note, items)

        collapsed_texts = set(note.get("collapsed", []))
        hidden = collapsed_hidden_line_indices(items, collapsed_texts)
        visible_items = [it for it in items if it.line_index not in hidden]
        display_items = self._apply_sort_filter(visible_items)

        for row in self.rows:
            self.list_layout.removeWidget(row)
            row.deleteLater()
        self.rows = []

        if not items:
            empty = QLabel("No checklist items found.\nAdd \"- [ ] task\" lines in Obsidian,\nor use the box below.")
            empty.setObjectName("EmptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.insertWidget(0, empty)
            self.rows.append(empty)
            return
        if not display_items:
            empty = QLabel("Nothing matches the current filter.")
            empty.setObjectName("EmptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.insertWidget(0, empty)
            self.rows.append(empty)
            return

        for idx, item in enumerate(display_items):
            row = TaskRow(item, has_children=bool(item.children), collapsed=item.text in collapsed_texts)
            row.toggled.connect(self._on_row_toggled)
            row.collapse_requested.connect(self._on_collapse_toggled)
            self.list_layout.insertWidget(idx, row)
            self.rows.append(row)

    def _on_row_toggled(self, line_index: int, checked: bool) -> None:
        note = self.active_note
        if note is None:
            return
        set_checked(note["path"], line_index, checked)
        # file-watcher fires -> reload_tasks() re-renders shortly after;
        # if filtering by active/done the row may need to disappear sooner:
        if self.filter_mode in ("active", "done"):
            QTimer.singleShot(200, self.reload_tasks)

    def _on_collapse_toggled(self, text: str) -> None:
        note = self.active_note
        if note is None:
            return
        collapsed = set(note.get("collapsed", []))
        if text in collapsed:
            collapsed.discard(text)
        else:
            collapsed.add(text)
        note["collapsed"] = sorted(collapsed)
        set_notes(self.notes)
        self.reload_tasks()
