"""Pack the release zip: one folder with the exe and the manual, nothing else.

    python tools/make_release.py            (build_exe.bat runs it after PyInstaller)

dist/<APP_NAME>_<APP_VERSION>.zip
    <APP_NAME>_<APP_VERSION>/
        <APP_NAME>.exe
        使用說明書.html      the in-app manual as ONE file (pictures embedded), opens in any browser

Same file in autorepair_db and new_again_db.
"""
import base64
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app import config  # noqa: E402

MANUAL_DIR = os.path.join(ROOT, "assets", "manual")
MANUAL_NAME = "使用說明書.html"
BROWSER_CSS = """<style>
body { max-width: 1000px; margin: 24px auto; padding: 0 16px; background: #fff; color: #1F2328;
       font-family: "Microsoft JhengHei", "PingFang TC", sans-serif; font-size: 18px; line-height: 1.7; }
img { max-width: 100%; height: auto; }
table { border-collapse: collapse; margin: 10px 0; }
h2 { margin-top: 40px; }
@media print { h2[style] { page-break-before: always; } }
</style>
"""


def standalone_manual() -> str:
    """manual.html with every picture embedded, so the one file is the whole manual."""
    with open(os.path.join(MANUAL_DIR, "manual.html"), encoding="utf-8") as f:
        html = f.read()

    def embed(m):
        with open(os.path.join(MANUAL_DIR, m.group(1)), "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        return f'<img src="data:image/png;base64,{data}"{m.group(2)}>'
    html = re.sub(r'<img src="([^"]+)"([^>]*)>', embed, html)
    return html.replace("</head>", BROWSER_CSS + "</head>", 1)


def pack(exe: str, out_dir: str) -> str:
    """Write the release zip into out_dir and return its path."""
    folder = f"{config.APP_NAME}_{config.APP_VERSION}"
    out = os.path.join(out_dir, folder + ".zip")
    expected = [f"{folder}/{config.APP_NAME}.exe", f"{folder}/{MANUAL_NAME}"]
    tmp = out + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:  # non-ASCII names get the UTF-8 flag
        z.write(exe, expected[0])
        z.writestr(expected[1], standalone_manual())
    with zipfile.ZipFile(tmp) as z:
        names = z.namelist()
        if names != expected or z.testzip() is not None:
            raise SystemExit(f"release zip is wrong: {names}")
    os.replace(tmp, out)
    return out


def main():
    sys.stdout.reconfigure(errors="replace")  # the Windows console may not show Chinese
    dist = os.path.join(ROOT, "dist")
    out = pack(os.path.join(dist, f"{config.APP_NAME}.exe"), dist)
    print("Release zip:", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
