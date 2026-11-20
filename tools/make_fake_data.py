"""Fill a database with about one year of realistic fake data (for testing only).

Usage: python tools/make_fake_data.py <path-to-洗車資料.db> [--customers 150] [--days 365] [--seed 1]
A safety copy 加入假資料前備份_<time>.db is written next to the database first.
"""
import argparse
import datetime as dt
import os
import random
import shutil
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.brands import BRANDS  # noqa: E402
from app.config import WASH_TYPES  # noqa: E402
from app.db import Database, DataError  # noqa: E402

PRICES = {"一般洗車": (200, 400), "精緻洗車": (500, 900), "美容": (1200, 3500), "其他": (100, 600)}
NOTES = ["老客戶", "要打蠟", "內裝要吸", "週末才來", "公司車", "", "", "", "", ""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--customers", type=int, default=150)
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    if os.path.exists(args.db):
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(args.db, os.path.join(os.path.dirname(os.path.abspath(args.db)), f"加入假資料前備份_{stamp}.db"))
    db = Database(args.db)
    today = dt.date.today()
    cars = []
    while len(cars) < args.customers:
        p1 = "".join(rng.choice(string.ascii_uppercase) for _ in range(3))
        p2 = f"{rng.randint(0, 9999):04d}"
        phone = f"09{rng.randint(10000000, 99999999)}"
        brand = rng.choice([b for b, _ in BRANDS] + [""] * 6)
        try:
            cid = db.add_customer(p1, p2, phone, rng.choice(NOTES), brand)
        except DataError:
            continue
        if rng.random() < 0.08:
            db.set_vip(cid, True)
        cars.append((p1, p2, rng.choice([7, 14, 21, 30, 60, None])))
    n = 0
    for p1, p2, every in cars:
        if every is None:
            continue
        d = today - dt.timedelta(days=rng.randint(0, every))
        while d >= today - dt.timedelta(days=args.days):
            t = rng.choices(WASH_TYPES, weights=[70, 20, 6, 4])[0]
            lo, hi = PRICES[t]
            db.add_wash(p1, p2, rng.randint(lo // 50, hi // 50) * 50, d.isoformat(),
                        t if rng.random() < 0.8 else f"{t} - {rng.choice(['打蠟', '內裝清潔', '鍍膜'])}")
            n += 1
            d -= dt.timedelta(days=max(1, every + rng.randint(-3, 5)))
    print(f"added {len(cars)} customers, {n} wash records")
    db.close()


if __name__ == "__main__":
    main()
