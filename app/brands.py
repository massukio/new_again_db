"""Car brands commonly seen in Taiwan, with logo files for the optional brand choice."""
import os
from typing import Optional

from app.config import resource_path

# (display name, logo file in assets/brands) - sorted by popularity in Taiwan
BRANDS = [
    ("Toyota", "toyota.png"), ("Honda", "honda.png"), ("Nissan", "nissan.png"),
    ("Mitsubishi", "mitsubishi.png"), ("Ford", "ford.png"), ("Mazda", "mazda.png"),
    ("CMC 中華", "other.png"), ("Luxgen 納智捷", "luxgen.png"), ("BMW", "bmw.png"),
    ("Mercedes-Benz", "mercedes-benz.png"), ("Lexus", "lexus.png"), ("Hyundai", "hyundai.png"),
    ("Kia", "kia.png"), ("Volkswagen", "volkswagen.png"), ("Audi", "audi.png"),
    ("Subaru", "subaru.png"), ("Suzuki", "suzuki.png"), ("Volvo", "volvo.png"),
    ("Tesla", "tesla.png"), ("Porsche", "porsche.png"), ("Maserati", "maserati.png"),
    ("其他", "other.png"),
]


def brand_logo(name: str) -> Optional[str]:
    for n, f in BRANDS:
        if n == name:
            path = resource_path("assets", "brands", f)
            return path if os.path.exists(path) else None
    return None
