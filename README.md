# ZetDoList

A minimal desktop to-do app for Windows that shows checkboxes only — the actual task text lives in your [Obsidian](https://obsidian.md) notes and is edited there like normal. ZetDoList just renders `- [ ] task` / `- [x] task` lines as a clean checklist and keeps everything in sync both ways, styled as retro pixel art.

## Features

- **Two-way Obsidian sync** — check a box in the app or in Obsidian, either one updates the file; the app watches your linked files and reloads automatically
- **Multiple linked notes** shown as tabs, add/remove freely (right-click a tab to remove it)
- **Daily reset notes** — mark a note as daily, and its checkboxes clear each day with a streak counter
- **Nested goals** — indent sub-items under a task in Obsidian and the app automatically:
  - shows a collapse/expand arrow for any item with sub-items
  - checks the parent off once every sub-item is done (and un-checks it if one gets undone), written back into the file too
- **Completion history chart** — a "times completed" bar chart on daily notes, ranking tasks by how often you've actually finished them
- **Due dates** — add `due: 2026-08-15` (or a 📅 emoji) to a task line and it'll show a due/overdue label and can send a desktop notification
- **System tray support** — closes to tray instead of quitting, with a tray icon and menu
- **Pixel-art theme** — fully re-themeable via one color dictionary; supports optional decorative art (see [Customizing the look](#customizing-the-look))

## Requirements

- Windows (built and tested there; the frameless custom window chrome is Windows-first, though the underlying app is plain PyQt6)
- Python 3.10+
- [PyQt6](https://pypi.org/project/PyQt6/)

## Running from source

```
pip install -r requirements.txt
python ZetDoList.pyw
```

On first launch, you'll be asked to pick your first Obsidian `.md` file to link. Everything ZetDoList remembers (linked notes, settings, completion history) is stored outside this folder, in `~/.obsidiancheck/` — deleting or moving this project folder won't touch your data.

## Building a standalone .exe

```
pip install pyinstaller
pyinstaller --onefile --windowed --name ZetDoList --add-data "assets;assets" ZetDoList.pyw
```

The finished executable is `dist/ZetDoList.exe` — that's the only file you need to keep or share.

Notes on the flags:
- `--windowed` suppresses the console window (this is a GUI app)
- `--add-data "assets;assets"` bundles the `assets/` folder (decorative art, if present) into the exe. The `;` separator is Windows-specific — Mac/Linux use `:` instead
- If you have an icon file, add `--icon=path\to\icon.ico` (must be a real `.ico`, not `.png`)

## Project structure

```
ZetDoList.pyw          entry point - just imports and runs the app
assets/                 optional decorative art (see below)
zetdolist/
    config.py           settings + linked-notes persistence
    history.py          completion history log (the chart's data source)
    markdown_sync.py     TodoItem model, indent tree, reading/writing the .md checkbox lines
    fonts.py              embedded pixel fonts (base64) + loader
    theme.py               colors, stylesheet, shared size constants
    icons.py                window/tray icon generation
    chrome_widgets.py        background, panel, title bar, resize grips, decoration overlay
    task_widgets.py            checkbox, collapse arrow, task row
    chart_widgets.py             the completion bar chart
    main_window.py                MainWindow - wires everything together
    app.py                         main() entry point
```

## Customizing the look

All colors live in one dictionary in `zetdolist/theme.py` — every widget reads from it, so a full re-theme is just editing hex values there, no other code changes needed.

**Optional decorative art**: drop PNGs into an `assets/` folder next to `ZetDoList.pyw`:

| File | What it does |
|---|---|
| `assets/horns.png` | Floats above the title bar in its own transparent, click-through overlay window that follows the app around |
| `assets/tail.png` | Floats off the bottom-right edge, same overlay treatment |

Both are entirely optional — if the files aren't there, the app just runs without them, no errors. Any `QPushButton` in the code can also be skinned with an image instead of its default style using `apply_button_image()` from `zetdolist/assets.py`.

## Known quirk

Settings are stored in `~/.obsidiancheck/` (a name from before the project was renamed to ZetDoList). It works fine as-is; renaming it would just mean writing a migration step for anyone with existing data, so it's been left alone for now.

## Fonts

Embedded (as base64, so the app and its `.exe` build stay one self-contained file with no missing-font risk): **Press Start 2P** and **VT323**, both by Google Fonts, licensed under the [SIL Open Font License](https://openfontlicense.org/).

## License

Not yet set — see the note at the bottom of this file / ask the repo owner. Until a license is added, default copyright applies (no one else may copy, modify, or redistribute the code).
