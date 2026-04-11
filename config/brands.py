"""
Car brands commonly seen in Taiwan, with logo image files for visual selection.
Sorted by popularity in Taiwan market.
"""
import os
import sys


def _get_base_dir():
    """Get base dir — works for both dev and PyInstaller."""
    if getattr(sys, '_MEIPASS', None):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Directory containing brand logo PNGs
BRAND_LOGO_DIR = os.path.join(_get_base_dir(), "assets", "brands")

# (display_name, logo_filename)
BRANDS = [
    ("Toyota", "toyota.png"),
    ("Honda", "honda.png"),
    ("Nissan", "nissan.png"),
    ("Mitsubishi", "mitsubishi.png"),
    ("Ford", "ford.png"),
    ("Mazda", "mazda.png"),
    ("CMC 中華", "other.png"),
    ("Luxgen 納智捷", "luxgen.png"),
    ("BMW", "bmw.png"),
    ("Mercedes-Benz", "mercedes-benz.png"),
    ("Lexus", "lexus.png"),
    ("Hyundai", "hyundai.png"),
    ("Kia", "kia.png"),
    ("Volkswagen", "volkswagen.png"),
    ("Audi", "audi.png"),
    ("Subaru", "subaru.png"),
    ("Suzuki", "suzuki.png"),
    ("Volvo", "volvo.png"),
    ("Tesla", "tesla.png"),
    ("Porsche", "porsche.png"),
    ("Maserati", "maserati.png"),
    ("其他", "other.png"),
]

BRAND_NAMES = [name for name, _ in BRANDS]
BRAND_ICONS = {name: os.path.join(BRAND_LOGO_DIR, fname) for name, fname in BRANDS}
