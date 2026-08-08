"""
ZetDoList - a minimal desktop to-do app that shows checkboxes only,
styled as retro pixel art, synced with Obsidian.

Task *text* lives in Obsidian notes and is edited there like normal. This
app renders "- [ ] task" / "- [x] task" lines as checkbox rows and keeps
them in sync both ways.

Package layout:
    config.py          persisted app settings + the list of linked notes
    history.py          per-day completion log used by the chart
    markdown_sync.py     TodoItem, indentation tree, file read/write
    fonts.py               embedded pixel fonts (base64) + loader
    theme.py                 colors, stylesheet, shared size constants
    icons.py                  window/tray icon generation
    chrome_widgets.py          background, panel, title bar, resize grips
    task_widgets.py              checkbox, collapse arrow, task row
    chart_widgets.py               "times completed" bar chart
    main_window.py                  MainWindow - wires everything together
    app.py                            main() entry point
"""
