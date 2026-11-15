"""NETWATCH launcher - started by NETWATCH.bat (or: python app/netwatch.py).

Installs missing dependencies from requirements.txt automatically on first run.
"""
import importlib
import os
import subprocess
import sys

if sys.version_info < (3, 8):
    sys.exit("NETWATCH requires Python 3.8 or newer.")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS = os.path.join(APP_DIR, "requirements.txt")
MODULES = ("requests", "psutil")   # import names of the packages in requirements.txt


def missing_modules():
    missing = []
    for name in MODULES:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    return missing


def ensure_requirements():
    if not missing_modules():
        return
    print("[NETWATCH] Installing required packages from requirements.txt ...")
    cmd = [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS,
           "--quiet", "--disable-pip-version-check"]
    if subprocess.call(cmd) != 0:
        subprocess.call(cmd + ["--user"])     # no write access -> install for this user only
    importlib.invalidate_caches()
    still = missing_modules()
    if still:
        sys.exit("[NETWATCH] Could not install: " + ", ".join(still) +
                 "\nRun manually:  python -m pip install -r app\\requirements.txt")
    print("[NETWATCH] Packages installed.")


if __name__ == "__main__":
    sys.path.insert(0, APP_DIR)
    ensure_requirements()
    from netwatch.app import main
    main()
