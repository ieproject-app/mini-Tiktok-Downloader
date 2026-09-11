"""
paths.py — Resolusi lokasi runtime mini-TikTok (portable vs ter-install).

Dua mode:
- PORTABLE (repo dev / zip manual): config di `_engine/`, ffmpeg di `_engine/bin`,
  downloads di repo root. Dipakai saat repo dijalankan lewat run.bat.
- INSTALLED (hasil install.ps1): data pengguna dipisah dari program —
  %LOCALAPPDATA%\\MiniTikTok\\data (config/ffmpeg bin) agar folder program
  tidak pernah ditulisi, dan download default ke ~/Downloads/MiniTikTok.
  Marker: file `installed.flag` di dalam `_engine/`.
"""

import os
from pathlib import Path

APP_DIR_NAME = "MiniTikTok"

_ENGINE_SRC = Path(__file__).resolve().parent
ENGINE_DIR = _ENGINE_SRC.parent          # .../_engine
REPO_ROOT = ENGINE_DIR.parent            # repo root


def is_installed() -> bool:
    """True bila berjalan dari salinan hasil installer (bukan repo dev)."""
    return (ENGINE_DIR / "installed.flag").exists()


def is_portable() -> bool:
    return not is_installed()


def data_dir() -> Path:
    """Direktori data yang boleh ditulisi (config/bin/log)."""
    if is_installed():
        base = os.environ.get("LOCALAPPDATA") or str(Path.home())
        d = Path(base) / APP_DIR_NAME / "data"
    else:
        d = ENGINE_DIR  # portable: config di _engine/
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return data_dir() / "config.json"


def bin_dir() -> Path:
    """Direktori ffmpeg/ffprobe (auto-download bila belum ada)."""
    if is_installed():
        d = data_dir() / "bin"
    else:
        d = ENGINE_DIR / "bin"
    d.mkdir(parents=True, exist_ok=True)
    return d


def default_downloads_dir() -> Path:
    if is_installed():
        d = Path.home() / "Downloads" / APP_DIR_NAME
    else:
        d = REPO_ROOT / "downloads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def requirements_file() -> Path:
    return REPO_ROOT / "requirements.txt"
