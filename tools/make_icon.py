"""Build assets/app.ico (16-256 px) and assets/app.png from assets/icon_source.png.

The source is the generated artwork: a teal rounded square on a white
background. We find the square, crop it, make everything outside the rounded
corners transparent and centre it on a square canvas. To change the icon,
replace icon_source.png and rebuild.
"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "icon_source.png")
ICO = os.path.join(ROOT, "assets", "app.ico")
PNG = os.path.join(ROOT, "assets", "app.png")
CORNER_RATIO = 0.194  # corner radius / square width, measured on the source art
INSET = 3             # px trimmed inside the edge to avoid a white fringe


def find_square(im):
    w, h = im.size
    dark = lambda p: sum(p[:3]) < 600  # noqa: E731 - "not white"
    xs = [x for x in range(w) if dark(im.getpixel((x, h // 2)))]
    ys = [y for y in range(h) if dark(im.getpixel((w // 2, y)))]
    return xs[0], ys[0], xs[-1] + 1, ys[-1] + 1


def main():
    im = Image.open(SRC).convert("RGB")
    left, top, right, bottom = find_square(im)
    sq = im.crop((left + INSET, top + INSET, right - INSET, bottom - INSET)).convert("RGBA")
    w, h = sq.size
    big = 4  # supersample the mask for smooth corners
    mask = Image.new("L", (w * big, h * big), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * big - 1, h * big - 1),
                                           radius=int(w * CORNER_RATIO * big), fill=255)
    sq.putalpha(mask.resize((w, h), Image.LANCZOS))
    side = int(max(w, h) * 1.04)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(sq, ((side - w) // 2, (side - h) // 2), sq)
    icon = canvas.resize((256, 256), Image.LANCZOS)
    os.makedirs(os.path.dirname(PNG), exist_ok=True)
    icon.save(PNG)
    icon.save(ICO, sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64),
                          (128, 128), (256, 256)])
    print("wrote", ICO, "and", PNG)


if __name__ == "__main__":
    main()
