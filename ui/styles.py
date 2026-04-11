"""
UI Styles — Clean, warm, modern design for elderly users.
Single accent color, high contrast, generous spacing.
"""

# Design system: warm neutral + single teal accent
ACCENT = "#0891B2"          # Teal — calm, trustworthy, readable
ACCENT_HOVER = "#0E7490"
ACCENT_LIGHT = "#E0F7FA"    # Very light teal for subtle highlights
DANGER = "#DC2626"          # Red only for delete — clear warning
DANGER_HOVER = "#B91C1C"

BG_PRIMARY = "#FAFAF9"      # Warm off-white
BG_SURFACE = "#FFFFFF"       # Cards/table
BG_SIDEBAR = "#F5F5F4"      # Button panel background
BORDER = "#E7E5E4"          # Subtle warm gray border
TEXT_PRIMARY = "#1C1917"     # Near-black, warm
TEXT_SECONDARY = "#78716C"   # Muted warm gray
TEXT_ON_ACCENT = "#FFFFFF"

FONT_FAMILY = "'PingFang TC', 'Microsoft JhengHei', 'Noto Sans TC', 'Helvetica Neue', sans-serif"

SHADOW_SM = "0 1px 2px rgba(0,0,0,0.06)"
SHADOW_MD = "0 2px 8px rgba(0,0,0,0.08)"


def build_main_stylesheet(button_font_size, table_font_size, input_font_size):
    return f"""
    /* === Base === */
    QWidget {{
        font-family: {FONT_FAMILY};
        color: {TEXT_PRIMARY};
        background-color: {BG_PRIMARY};
    }}
    QMainWindow {{
        background-color: {BG_PRIMARY};
    }}

    /* === Table === */
    QTableWidget {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        font-size: {table_font_size}px;
        gridline-color: {BORDER};
        selection-background-color: {ACCENT_LIGHT};
        selection-color: {TEXT_PRIMARY};
        outline: none;
    }}
    QTableWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {BORDER};
    }}
    QTableWidget::item:selected {{
        background-color: {ACCENT_LIGHT};
        color: {TEXT_PRIMARY};
    }}
    QHeaderView::section {{
        background-color: {BG_SIDEBAR};
        color: {TEXT_SECONDARY};
        padding: 10px 12px;
        border: none;
        border-bottom: 2px solid {BORDER};
        font-size: {int(table_font_size * 0.75)}px;
        font-weight: bold;
        text-transform: uppercase;
    }}

    /* === Buttons — unified style, accent color === */
    QPushButton {{
        background-color: {ACCENT};
        color: {TEXT_ON_ACCENT};
        border: none;
        padding: 14px 24px;
        font-size: {button_font_size}px;
        font-weight: bold;
        border-radius: 10px;
        margin: 3px 0px;
        min-height: 48px;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton:pressed {{
        background-color: #0C4A6E;
    }}

    /* Delete button — only exception, uses red for clarity */
    QPushButton#delete_button {{
        background-color: {BG_SURFACE};
        color: {DANGER};
        border: 2px solid {DANGER};
    }}
    QPushButton#delete_button:hover {{
        background-color: {DANGER};
        color: {TEXT_ON_ACCENT};
    }}

    /* Wash record / earnings buttons — outlined accent style */
    QPushButton#wash_record_button, QPushButton#earnings_button {{
        background-color: {BG_SURFACE};
        color: {ACCENT};
        border: 2px solid {ACCENT};
    }}
    QPushButton#wash_record_button:hover, QPushButton#earnings_button:hover {{
        background-color: {ACCENT};
        color: {TEXT_ON_ACCENT};
    }}

    /* Clear search — subtle outline style */
    QPushButton#clear_button {{
        background-color: {BG_SURFACE};
        color: {TEXT_SECONDARY};
        border: 2px solid {BORDER};
        min-height: 40px;
        padding: 10px 20px;
    }}
    QPushButton#clear_button:hover {{
        background-color: {BG_SIDEBAR};
        color: {TEXT_PRIMARY};
        border-color: {TEXT_SECONDARY};
    }}

    /* === Input Fields === */
    QLineEdit {{
        background-color: {BG_SURFACE};
        padding: 12px 16px;
        border: 2px solid {BORDER};
        border-radius: 10px;
        font-size: {input_font_size}px;
        font-weight: bold;
        color: {TEXT_PRIMARY};
    }}
    QLineEdit:focus {{
        border-color: {ACCENT};
        background-color: {BG_SURFACE};
    }}
    QLineEdit::placeholder {{
        color: {TEXT_SECONDARY};
    }}

    /* === ComboBox === */
    QComboBox {{
        background-color: {BG_SURFACE};
        padding: 10px 16px;
        border: 2px solid {BORDER};
        border-radius: 10px;
        font-size: {input_font_size}px;
        font-weight: bold;
        color: {TEXT_PRIMARY};
        min-width: 140px;
    }}
    QComboBox:focus {{
        border-color: {ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        selection-background-color: {ACCENT_LIGHT};
        selection-color: {TEXT_PRIMARY};
        font-size: {input_font_size}px;
        padding: 4px;
    }}
    QComboBox QAbstractItemView::item {{
        padding: 6px 12px;
    }}
    QComboBox QAbstractItemView::indicator {{
        width: 0px;
        height: 0px;
    }}

    /* === Menu Bar === */
    QMenuBar {{
        background-color: {BG_PRIMARY};
        border-bottom: 1px solid {BORDER};
        padding: 2px 8px;
    }}
    QMenuBar::item {{
        padding: 6px 12px;
        border-radius: 4px;
    }}
    QMenuBar::item:selected {{
        background-color: {ACCENT_LIGHT};
    }}
    QMenu {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {ACCENT_LIGHT};
    }}

    /* === Scrollbar === */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_SECONDARY};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """


def build_dialog_stylesheet(button_font_size):
    return f"""
    QDialog {{
        background-color: {BG_PRIMARY};
        font-family: {FONT_FAMILY};
        color: {TEXT_PRIMARY};
    }}
    QWidget {{
        background-color: {BG_PRIMARY};
        color: {TEXT_PRIMARY};
    }}
    QLabel {{
        color: {TEXT_SECONDARY};
        font-weight: bold;
        background-color: transparent;
    }}
    QLineEdit {{
        background-color: {BG_SURFACE};
        padding: 12px 16px;
        border: 2px solid {BORDER};
        border-radius: 10px;
        color: {TEXT_PRIMARY};
    }}
    QLineEdit:focus {{
        border-color: {ACCENT};
    }}
    QLineEdit::placeholder {{
        color: {TEXT_SECONDARY};
    }}
    QDateEdit {{
        background-color: {BG_SURFACE};
        padding: 8px 12px;
        border: 2px solid {BORDER};
        border-radius: 8px;
        color: {TEXT_PRIMARY};
    }}
    QTableWidget {{
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        selection-background-color: {ACCENT_LIGHT};
        selection-color: {TEXT_PRIMARY};
    }}
    QTableWidget::item {{
        padding: 6px 10px;
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
    }}
    QHeaderView::section {{
        background-color: {BG_SIDEBAR};
        color: {TEXT_SECONDARY};
        padding: 8px 10px;
        border: none;
        border-bottom: 2px solid {BORDER};
        font-weight: bold;
    }}
    QPushButton {{
        background-color: {ACCENT};
        color: {TEXT_ON_ACCENT};
        border: none;
        padding: 12px 24px;
        font-size: {button_font_size}px;
        font-weight: bold;
        border-radius: 10px;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
    """
