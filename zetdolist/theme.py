"""Colors, the global stylesheet, and small shared size constants used
across every widget module."""
from __future__ import annotations

from .fonts import BODY_FONT_FAMILY, TITLE_FONT_FAMILY

# ============================================================================
# Theme
# ============================================================================

THEME = {
    "bg_top": "#0f0c22",
    "bg_bottom": "#050410",
    "sparkle": "#e3f382",
    "panel_bg": "#4a2782",
    "panel_border": "#140a28",
    "row_bg": "#ffffff",
    "row_border": "#140a28",
    "text": "#1e1438",
    "text_dim": "#c3b0e0",
    "accent": "#1e1438",
    "done": "#b8a3d4",
    "banner_bg": "#ffffff",
    "banner_border": "#140a28",
    "shadow": "#050410",
    "tab_active_bg": "#6b35c4",
    "tab_active_text": "#ffffff",
    "streak": "#d4e86a",
    "overdue": "#ff6f6f",
    "glow": "#b866f0",
    # Custom OS window chrome
    "titlebar_bg": "#0f0c20",
    "titlebar_border": "#140a28",
    "titlebar_text": "#f0eaff",
    "titlebar_btn_hover": "#3d2264",
    "titlebar_btn_press": "#502896",
    "close_bg": "#ff6f6f",
    "close_hover": "#ff4747",
    "corner_dot": "#e3f382",
    "scanline": "#05040c",
}


BORDER_W = 3


SHADOW_OFFSET = 4


TITLEBAR_H = 34


STYLESHEET = f"""
QWidget {{
    color: {THEME['text']};
    font-family: '{BODY_FONT_FAMILY}', 'Consolas', monospace;
    font-size: 18px;
}}
QPushButton#IconButton {{
    background-color: {THEME['banner_bg']};
    border: {BORDER_W}px solid {THEME['panel_border']};
    border-radius: 0px;
    padding: 3px 8px;
    color: {THEME['accent']};
    font-family: '{BODY_FONT_FAMILY}', 'Consolas', monospace;
    font-size: 15px;
}}
QPushButton#IconButton:hover {{ background-color: #eef0ff; }}
QPushButton#IconButton:pressed {{ background-color: #d7dcff; }}
QPushButton#IconButtonOn {{
    background-color: {THEME['tab_active_bg']};
    border: {BORDER_W}px solid {THEME['panel_border']};
    border-radius: 0px;
    padding: 3px 8px;
    color: {THEME['tab_active_text']};
    font-family: '{BODY_FONT_FAMILY}', 'Consolas', monospace;
    font-size: 15px;
}}
QPushButton#TabButton {{
    background-color: {THEME['banner_bg']};
    border: {BORDER_W}px solid {THEME['panel_border']};
    border-bottom: none;
    border-radius: 0px;
    padding: 4px 10px;
    color: {THEME['accent']};
    font-size: 15px;
}}
QPushButton#TabButtonActive {{
    background-color: {THEME['tab_active_bg']};
    border: {BORDER_W}px solid {THEME['panel_border']};
    border-bottom: none;
    border-radius: 0px;
    padding: 4px 10px;
    color: {THEME['tab_active_text']};
    font-size: 15px;
    font-weight: bold;
}}
#AppTitle {{
    font-family: '{TITLE_FONT_FAMILY}', 'Consolas', monospace;
    font-size: 13px;
    color: {THEME['accent']};
}}
#TitleBarText {{
    font-family: '{TITLE_FONT_FAMILY}', 'Consolas', monospace;
    font-size: 11px;
    color: {THEME['titlebar_text']};
    background: transparent;
}}
#WindowFrame {{ background: transparent; }}
#FileLabel {{ color: {THEME['text_dim']}; font-size: 13px; }}
#StreakLabel {{ color: {THEME['streak']}; font-size: 15px; }}
QScrollArea {{ border: none; background: transparent; }}
#ListContainer {{ background: transparent; }}
#TaskLabel {{ color: {THEME['text']}; font-size: 19px; }}
#TaskLabel[done="true"] {{ color: {THEME['done']}; }}
#DueLabel {{ color: {THEME['overdue']}; font-size: 13px; }}
#EmptyState {{ color: {THEME['text_dim']}; font-size: 16px; }}
#ChartHeader {{ color: {THEME['accent']}; font-size: 15px; }}
#ChartTaskLabel {{ color: {THEME['text']}; font-size: 14px; }}
#ChartCountLabel {{ color: {THEME['accent']}; font-size: 14px; }}
#ChartEmpty {{ color: {THEME['text_dim']}; font-size: 14px; }}
QLineEdit#QuickAdd {{
    background-color: {THEME['row_bg']};
    border: {BORDER_W}px solid {THEME['row_border']};
    border-radius: 0px;
    padding: 6px 8px;
    color: {THEME['text']};
    font-size: 18px;
}}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {THEME['sparkle']}; border-radius: 0px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
