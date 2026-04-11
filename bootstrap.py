"""
Environment bootstrap script.
Installs uv via pip, then uses uv for everything else (fast venv + deps).
Called automatically by start.py before launching the app.
"""
import subprocess
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, ".venv")
VENV_PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe") if sys.platform == "win32" \
    else os.path.join(VENV_DIR, "bin", "python")


def run(cmd):
    print(f"  → {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=PROJECT_DIR).returncode == 0


def setup():
    """Bootstrap: pip→uv, uv→venv, uv→deps. Returns True on success."""
    # 1. Ensure uv installed (only pip usage in the whole project)
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("[bootstrap] Installing uv...")
        if not run([sys.executable, "-m", "pip", "install", "uv"]):
            return False

    # 2. Create venv via uv
    if not os.path.exists(VENV_DIR):
        print("[bootstrap] Creating virtual environment...")
        if not run(["uv", "venv", VENV_DIR]):
            return False

    # 3. Install deps via uv (direct packages, not editable install)
    print("[bootstrap] Installing dependencies...")
    if not run(["uv", "pip", "install", "--python", VENV_PYTHON,
                "PyQt5>=5.15.11", "pytest>=8.0", "pyinstaller>=6.0"]):
        return False

    print("[bootstrap] Environment ready.")
    return True


if __name__ == "__main__":
    sys.exit(0 if setup() else 1)
