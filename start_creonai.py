# start_creonai.py – REPAIRED

import os, subprocess, venv, platform
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
VENV_DIR     = PROJECT_ROOT / "venv"
PY_BIN       = VENV_DIR / ("Scripts" if platform.system() == "Windows" else "bin") / "python"
UVICORN_BIN  = VENV_DIR / ("Scripts" if platform.system() == "Windows" else "bin") / "uvicorn"

def run(cmd):
    subprocess.check_call(cmd)

def create_venv():
    print("🔧 Creating virtual environment …")
    venv.create(VENV_DIR, with_pip=True)

def install_packages():
    print("📦 Installing FastAPI & Uvicorn …")
    run([str(PY_BIN), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(PY_BIN), "-m", "pip", "install", "-r", "requirements.txt"])

def start_server():
    print("\n🚀 Server running at http://127.0.0.1:8000  (CTRL+C to stop)\n")
    run([str(UVICORN_BIN), "backend.main:app", "--reload"])

if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)

    if not VENV_DIR.exists():
        create_venv()

    try:
        run([str(UVICORN_BIN), "--version"])
    except (FileNotFoundError, subprocess.CalledProcessError):
        install_packages()

    start_server()
