"""TodoItem model, the indentation-based parent/child tree, and all reading
from / writing back to the Obsidian .md checkbox lines."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date

# ============================================================================
# Markdown sync - reads/writes Obsidian checkbox lines only
# ============================================================================

CHECKBOX_RE = re.compile(r"^(?P<indent>[ \t]*)[-*]\s\[(?P<mark>[ xX])\]\s?(?P<text>.*)$")


DUE_DATE_RE = re.compile(r"(?:due:\s*|\U0001F4C5\s*)(\d{4}-\d{2}-\d{2})", re.IGNORECASE)


@dataclass
class TodoItem:
    line_index: int
    indent_level: int
    checked: bool
    text: str
    children: list[TodoItem] = field(default_factory=list)

    @property
    def due_date(self) -> date | None:
        m = DUE_DATE_RE.search(self.text)
        if not m:
            return None
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            return None


def _indent_level(indent: str) -> int:
    tabs = indent.count("\t")
    spaces = len(indent.replace("\t", ""))
    return tabs + spaces // 2


def _attach_children(items: list[TodoItem]) -> None:
    """Populates each item's `children` from indentation alone, using a
    stack so any nesting depth works. Mutates the items in place - this
    is what makes sub-items "hideable" and parent checkboxes derivable,
    purely from whatever indentation is currently in the file."""
    stack: list[TodoItem] = []
    for item in items:
        while stack and stack[-1].indent_level >= item.indent_level:
            stack.pop()
        if stack:
            stack[-1].children.append(item)
        stack.append(item)


def effective_checked(item: TodoItem) -> bool:
    """An item with sub-items counts as done once every sub-item does
    (recursively); otherwise its own checkbox is used as-is."""
    if not item.children:
        return item.checked
    return all(effective_checked(child) for child in item.children)


def collapsed_hidden_line_indices(items: list[TodoItem], collapsed_texts: set[str]) -> set[int]:
    """Returns the line_index of every item that should be hidden because
    one of its ancestors (matched by text) is currently collapsed."""
    hidden: set[int] = set()

    def hide_subtree(parent: TodoItem) -> None:
        for child in parent.children:
            hidden.add(child.line_index)
            hide_subtree(child)

    for item in items:
        if item.children and item.text in collapsed_texts:
            hide_subtree(item)
    return hidden


def parse_todo_file(file_path: str) -> list[TodoItem]:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    items: list[TodoItem] = []
    for i, line in enumerate(lines):
        m = CHECKBOX_RE.match(line.rstrip("\n"))
        if not m:
            continue
        items.append(
            TodoItem(
                line_index=i,
                indent_level=_indent_level(m.group("indent")),
                checked=m.group("mark").lower() == "x",
                text=m.group("text").strip(),
            )
        )
    _attach_children(items)
    return items


def set_checked(file_path: str, line_index: int, checked: bool) -> None:
    """Flips only the checkbox marker on one line; everything else in the
    file is untouched."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if line_index >= len(lines):
        return
    lines[line_index] = _flip_line(lines[line_index], checked)
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _flip_line(line: str, checked: bool) -> str:
    new_mark = "x" if checked else " "
    bullet = "*" if line.lstrip().startswith("*") else "-"
    new_line = CHECKBOX_RE.sub(
        lambda m: f"{m.group('indent')}{bullet} [{new_mark}] {m.group('text')}",
        line.rstrip("\n"),
    )
    return new_line + "\n"


def reset_all_checkboxes(file_path: str, line_indices: list[int]) -> None:
    """Unchecks every checkbox line given, in a single read/write pass."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for idx in line_indices:
        if idx < len(lines):
            lines[idx] = _flip_line(lines[idx], False)
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def append_task(file_path: str, text: str) -> None:
    """Appends a new '- [ ] text' line to the end of the file."""
    needs_newline = False
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "rb") as f:
            f.seek(-1, os.SEEK_END)
            needs_newline = f.read(1) != b"\n"
    with open(file_path, "a", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")
        f.write(f"- [ ] {text}\n")
