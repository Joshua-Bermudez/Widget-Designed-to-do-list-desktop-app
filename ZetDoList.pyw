"""
ZetDoList launcher.

The actual implementation lives in the zetdolist/ package next to this
file - see zetdolist/__init__.py for a map of what's in each module.

Run:
    pip install PyQt6
    python ZetDoList.pyw

First launch will ask you to pick your first Obsidian .md file. Everything
is remembered in ~/.obsidiancheck/config.json.
"""
from zetdolist.app import main

if __name__ == "__main__":
    main()
