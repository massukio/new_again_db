"""Global stylesheet + UI scaling.

Everything is sized from one base font size (pt). The main window recomputes
that size whenever it is resized, so the UI fits any screen / window size.
Fixed pixel sizes set in code go through ``sized()`` so they scale too.
"""
import weakref

from app import config

# ---- palette -------------------------------------------------------------
BG = "#F3F1EC"            # warm paper background
SURFACE = "#FFFFFF"       # cards
SURFACE_ALT = "#F8F6F2"   # tiles, table header
BORDER = "#E3DED5"
BORDER_STRONG = "#BDB6AA"
TEXT = "#1F2328"
MUTED = "#6A6F78"
PRIMARY = "#0E6E84"       # navigation / links (the carwash app's teal, darkened for contrast)
PRIMARY_DARK = "#0B5566"
PRIMARY_SOFT = "#E4F2F5"
SUCCESS = "#2F7D50"       # selected items / save
SUCCESS_DARK = "#24623F"
SUCCESS_SOFT = "#E8F3EC"
DANGER = "#B3261E"
DANGER_SOFT = "#FBECEB"
AMBER = "#9A6412"
AMBER_SOFT = "#FFF5E2"

_scale = 1.0
_registry = []  # (weakref to widget, method name, reference values)


def scale() -> float:
    return _scale


def px(n: float) -> int:
    return max(1, round(n * _scale))


def sized(widget, method: str, *values):
    """Call e.g. widget.setMinimumWidth(px(280)) now and again whenever the scale changes."""
    _registry.append((weakref.ref(widget), method, values))
    getattr(widget, method)(*(px(v) for v in values))
    return widget


def set_scale(new_scale: float) -> None:
    global _scale
    _scale = new_scale
    alive = []
    for ref, method, values in _registry:
        w = ref()
        if w is None:
            continue
        try:
            getattr(w, method)(*(px(v) for v in values))
        except RuntimeError:  # C++ object already deleted
            continue
        alive.append((ref, method, values))
    _registry[:] = alive


def base_font_for(width: int, height: int, factor: float) -> int:
    fit = min(width / config.REF_WIDTH, height / config.REF_HEIGHT) ** config.SCALE_EXPONENT
    base = round(config.REF_FONT_PT * fit * factor)
    return max(config.MIN_FONT_PT, min(config.MAX_FONT_PT, base))


def build_stylesheet(base: int) -> str:
    k = base / config.REF_FONT_PT

    def p(n):  # scale a pixel value with the font
        return max(1, round(n * k))

    small = max(base - 3, 11)
    return f"""
    QWidget {{
        font-family: "Microsoft JhengHei UI", "Microsoft JhengHei", "PingFang TC", sans-serif;
        font-size: {base}pt; color: {TEXT};
    }}
    QMainWindow, QDialog {{ background: {BG}; }}
    QScrollArea {{ background: transparent; border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QToolTip {{ font-size: {base}pt; background: {SURFACE}; border: 1px solid {BORDER_STRONG}; padding: {p(6)}px; }}

    /* ---------- header ---------- */
    QFrame[role="header"] {{ background: {SURFACE}; border: none; border-bottom: 1px solid {BORDER}; }}
    QLabel[role="brand"] {{ font-size: {base + 4}pt; font-weight: bold; color: {PRIMARY_DARK}; }}
    QLabel[role="brandmark"] {{
        background: {PRIMARY}; color: white; font-weight: bold; font-size: {base + 2}pt;
        border-radius: {p(10)}px; padding: {p(4)}px {p(9)}px;
    }}
    QPushButton[role="nav"] {{
        background: transparent; border: none; border-radius: {p(10)}px;
        color: {MUTED}; font-size: {base + 2}pt; font-weight: bold; padding: {p(10)}px {p(20)}px;
    }}
    QPushButton[role="nav"]:hover {{ background: {PRIMARY_SOFT}; color: {PRIMARY_DARK}; }}
    QPushButton[role="nav"]:checked {{ background: {PRIMARY}; color: white; }}

    /* ---------- cards & text ---------- */
    QFrame[role="card"] {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: {p(16)}px; }}
    QFrame[role="tile"] {{ background: {SURFACE_ALT}; border: none; border-radius: {p(12)}px; }}
    QFrame[role="divider"] {{ background: {BORDER}; border: none; max-height: 1px; min-height: 1px; }}
    QLabel[role="cardtitle"] {{ font-size: {base + 3}pt; font-weight: bold; color: {TEXT}; }}
    QLabel[role="field"] {{ font-weight: bold; color: {TEXT}; }}
    QLabel[role="muted"], QLabel[role="hint"] {{ color: {MUTED}; font-size: {small}pt; }}
    QLabel[role="tilecap"] {{ color: {MUTED}; font-size: {small}pt; }}
    QLabel[role="tileval"] {{ font-size: {base + 5}pt; font-weight: bold; color: {TEXT}; }}
    QLabel[role="plate"] {{ font-size: {base + 9}pt; font-weight: bold; color: {TEXT}; letter-spacing: 1px; }}
    QLabel[role="total"] {{ font-size: {base + 1}pt; font-weight: bold; color: {SUCCESS_DARK}; }}
    QLabel[role="badge"] {{
        background: {AMBER_SOFT}; color: {AMBER}; border-radius: {p(8)}px;
        padding: {p(3)}px {p(10)}px; font-size: {small}pt; font-weight: bold;
    }}
    QLabel[role="badgenew"] {{
        background: {PRIMARY_SOFT}; color: {PRIMARY_DARK}; border-radius: {p(8)}px;
        padding: {p(3)}px {p(10)}px; font-size: {small}pt; font-weight: bold;
    }}
    QLabel[role="rowkey"] {{ color: {MUTED}; }}
    QLabel[role="rowval"] {{ font-weight: bold; }}
    QLabel[role="info"] {{
        background: {AMBER_SOFT}; border: none; border-radius: {p(12)}px; padding: {p(12)}px {p(16)}px;
    }}
    QLabel[role="empty"] {{ color: {MUTED}; padding: {p(18)}px; }}

    /* ---------- buttons ---------- */
    QPushButton {{
        background: {SURFACE}; border: 1px solid {BORDER_STRONG}; border-radius: {p(10)}px;
        padding: {p(9)}px {p(18)}px; color: {TEXT};
    }}
    QPushButton:hover {{ background: {PRIMARY_SOFT}; border-color: {PRIMARY}; }}
    QPushButton:pressed {{ background: #D5E4F0; }}
    QPushButton:disabled {{ color: #A9A9A9; border-color: {BORDER}; background: {SURFACE_ALT}; }}
    QPushButton[role="primary"] {{
        background: {SUCCESS}; color: white; border: none; font-weight: bold;
        font-size: {base + 3}pt; padding: {p(13)}px {p(34)}px; border-radius: {p(12)}px;
    }}
    QPushButton[role="primary"]:hover {{ background: {SUCCESS_DARK}; }}
    QPushButton[role="danger"] {{ background: {SURFACE}; color: {DANGER}; border: 1px solid #E3A9A5; font-weight: bold; }}
    QPushButton[role="danger"]:hover {{ background: {DANGER_SOFT}; border-color: {DANGER}; }}
    QPushButton[role="action"] {{
        background: {PRIMARY}; color: white; border: none; font-weight: bold;
        font-size: {base + 2}pt; padding: {p(13)}px {p(20)}px; border-radius: {p(12)}px;
    }}
    QPushButton[role="action"]:hover {{ background: {PRIMARY_DARK}; }}
    QPushButton[role="big"] {{ font-size: {base + 2}pt; padding: {p(13)}px {p(20)}px; border-radius: {p(12)}px; }}
    QPushButton[role="bigdanger"] {{
        font-size: {base + 2}pt; padding: {p(13)}px {p(20)}px; border-radius: {p(12)}px;
        background: {SURFACE}; color: {DANGER}; border: 1px solid #E3A9A5; font-weight: bold;
    }}
    QPushButton[role="bigdanger"]:hover {{ background: {DANGER_SOFT}; border-color: {DANGER}; }}
    QPushButton[role="brand"] {{
        font-size: {small + 1}pt; padding: {p(8)}px {p(6)}px; border-radius: {p(12)}px;
        border: 1px solid {BORDER_STRONG}; text-align: center;
    }}
    QPushButton[role="brand"]:checked {{ background: {SUCCESS_SOFT}; border: 2px solid {SUCCESS}; font-weight: bold; }}
    QLabel[role="toast"] {{
        background: {SUCCESS_SOFT}; color: {SUCCESS_DARK}; border-radius: {p(10)}px;
        padding: {p(6)}px {p(14)}px; font-weight: bold;
    }}
    QLabel[role="toastwarn"] {{
        background: {AMBER_SOFT}; color: {AMBER}; border-radius: {p(10)}px;
        padding: {p(6)}px {p(14)}px; font-weight: bold;
    }}
    QLabel[role="selected"] {{
        background: {PRIMARY_SOFT}; color: {PRIMARY_DARK}; border: 2px solid {PRIMARY};
        border-radius: {p(12)}px; padding: {p(8)}px {p(12)}px; font-size: {base + 5}pt; font-weight: bold;
    }}
    QLabel[role="selected"][empty="true"] {{
        background: {SURFACE_ALT}; color: {MUTED}; border: 2px dashed {BORDER_STRONG};
        font-size: {base}pt; font-weight: normal;
    }}
    QLabel[role="dash"] {{ font-size: {base + 6}pt; color: {MUTED}; }}
    QPushButton[role="link"] {{
        background: transparent; border: none; color: {PRIMARY}; font-weight: bold; padding: {p(6)}px {p(10)}px;
    }}
    QPushButton[role="link"]:hover {{ background: {PRIMARY_SOFT}; }}
    QPushButton[role="item"] {{
        font-size: {base + 1}pt; padding: {p(15)}px {p(8)}px; border-radius: {p(12)}px;
        border: 1px solid {BORDER_STRONG};
    }}
    QPushButton[role="item"]:checked {{ background: {SUCCESS}; color: white; border: 1px solid {SUCCESS_DARK}; font-weight: bold; }}
    QPushButton[role="item"]:checked:hover {{ background: {SUCCESS_DARK}; }}
    QPushButton[role="date"] {{ font-size: {base + 3}pt; font-weight: bold; padding: {p(8)}px {p(20)}px; }}
    QFrame[role="segbar"] {{ background: #E9E5DE; border-radius: {p(12)}px; }}
    QPushButton[role="seg"] {{
        background: transparent; border: none; border-radius: {p(9)}px; color: {MUTED};
        font-weight: bold; padding: {p(8)}px {p(20)}px;
    }}
    QPushButton[role="seg"]:checked {{ background: {SURFACE}; color: {PRIMARY_DARK}; border: 1px solid {BORDER}; }}

    /* ---------- inputs ---------- */
    QLineEdit {{
        background: {SURFACE}; border: 2px solid {BORDER_STRONG}; border-radius: {p(10)}px;
        padding: {p(8)}px {p(12)}px; font-size: {base + 4}pt; selection-background-color: {PRIMARY};
    }}
    QLineEdit:focus {{ border: 2px solid {PRIMARY}; }}
    QLineEdit[role="small"] {{ font-size: {base + 1}pt; }}
    QLineEdit[role="search"] {{ font-size: {base + 8}pt; font-weight: bold; padding: {p(6)}px {p(10)}px; }}

    /* ---------- lists & tables ---------- */
    QTableWidget {{
        background: {SURFACE}; border: none; gridline-color: transparent; font-size: {base}pt;
        selection-background-color: {PRIMARY_SOFT}; selection-color: {TEXT};
        alternate-background-color: #FBFAF7;
    }}
    QTableWidget::item {{ padding: {p(6)}px {p(10)}px; border-bottom: 1px solid {BORDER}; }}
    QTableWidget::item:hover {{ background: {PRIMARY_SOFT}; }}
    QTableWidget::item:selected {{ background: {PRIMARY}; color: white; font-weight: bold; }}
    QHeaderView::section {{
        background: {SURFACE_ALT}; color: {MUTED}; padding: {p(8)}px {p(10)}px; border: none;
        border-bottom: 1px solid {BORDER}; font-weight: bold; font-size: {small + 1}pt;
    }}
    QTableCornerButton::section {{ background: {SURFACE_ALT}; border: none; }}
    QListWidget {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: {p(10)}px; font-size: {base + 1}pt; }}
    QListWidget::item {{ padding: {p(10)}px {p(12)}px; border-bottom: 1px solid {BORDER}; }}
    QListWidget::item:selected {{ background: {PRIMARY_SOFT}; color: {TEXT}; }}

    QCalendarWidget QWidget {{ font-size: {base + 1}pt; }}
    QCalendarWidget QToolButton {{ font-size: {base + 1}pt; color: {TEXT}; padding: {p(6)}px; background: transparent; border: none; }}
    QCalendarWidget QWidget#qt_calendar_navigationbar {{ background: {SURFACE_ALT}; }}
    QCalendarWidget QAbstractItemView {{ selection-background-color: {PRIMARY}; selection-color: white; background: {SURFACE}; }}

    QMenu {{ font-size: {base + 1}pt; background: {SURFACE}; border: 1px solid {BORDER_STRONG}; border-radius: {p(8)}px; }}
    QMenu::item {{ padding: {p(10)}px {p(24)}px; }}
    QMenu::item:selected {{ background: {PRIMARY_SOFT}; color: {TEXT}; }}
    QMessageBox {{ background: {SURFACE}; }}
    QMessageBox QLabel {{ font-size: {base + 1}pt; }}
    QMessageBox QPushButton {{ min-width: {p(120)}px; }}

    /* keyboard focus must always be visible (placed last so it wins over role styles) */
    QPushButton:focus, QPushButton[role]:focus {{ border: {p(3)}px solid #D99A00; }}
    QMessageBox QPushButton:default {{ border: {p(3)}px solid #D99A00; }}
    QScrollBar:vertical {{ background: transparent; width: {p(14)}px; margin: {p(2)}px; }}
    QScrollBar::handle:vertical {{ background: #CFC9BF; border-radius: {p(5)}px; min-height: {p(40)}px; }}
    QScrollBar::handle:vertical:hover {{ background: #B5AEA2; }}
    QScrollBar:horizontal {{ background: transparent; height: {p(14)}px; margin: {p(2)}px; }}
    QScrollBar::handle:horizontal {{ background: #CFC9BF; border-radius: {p(5)}px; min-width: {p(40)}px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    """
