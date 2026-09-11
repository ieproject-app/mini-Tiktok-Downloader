import os
import sys
import shutil
import subprocess
import zipfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import paths

BIN_DIR = paths.bin_dir()
FFMPEG_EXE = BIN_DIR / "ffmpeg.exe"
FFPROBE_EXE = BIN_DIR / "ffprobe.exe"

FFMPEG_WINDOWS_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"


def is_ffmpeg_available():
    if FFMPEG_EXE.exists():
        return str(BIN_DIR)
    if shutil.which("ffmpeg"):
        return "system"
    return None


def download_and_extract_ffmpeg():
    print("[~] FFmpeg tidak ditemukan. Mendownload FFmpeg otomatis...")
    print("[~] Downloading FFmpeg dari GitHub (ini hanya dilakukan sekali)...")
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = BIN_DIR / "ffmpeg_temp.zip"

    try:
        def reporthook(blocknum, blocksize, totalsize):
            read = blocknum * blocksize
            if totalsize > 0:
                percent = min(100, read * 100 // totalsize)
                sys.stdout.write(
                    f"\r    Progress: {percent}% ({read // (1024*1024)}MB / {totalsize // (1024*1024)}MB)"
                )
                sys.stdout.flush()

        urllib.request.urlretrieve(FFMPEG_WINDOWS_URL, zip_path, reporthook)
        print("\n[~] Mengekstrak FFmpeg...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith("ffmpeg.exe"):
                    file_info.filename = "ffmpeg.exe"
                    zip_ref.extract(file_info, BIN_DIR)
                elif file_info.filename.endswith("ffprobe.exe"):
                    file_info.filename = "ffprobe.exe"
                    zip_ref.extract(file_info, BIN_DIR)

        if zip_path.exists():
            os.remove(zip_path)

        print("[✓] FFmpeg berhasil diinstall!")
        return str(BIN_DIR)
    except Exception as e:
        print(f"[X] Gagal download FFmpeg: {e}")
        print("    Silakan install FFmpeg manual dari https://ffmpeg.org/download.html")
        return None


def ensure_dependencies():
    if sys.version_info < (3, 9):
        print(f"[X] Python 3.9+ diperlukan. Versi saat ini: {sys.version}")
        sys.exit(1)

    required = ["yt_dlp", "rich", "requests", "curl_cffi"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"[~] Menginstall dependensi: {', '.join(missing)}...")
        req_file = paths.requirements_file()
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        print("[✓] Dependensi berhasil diinstall!")

    ffmpeg_status = is_ffmpeg_available()
    if not ffmpeg_status:
        ffmpeg_status = download_and_extract_ffmpeg()

    if ffmpeg_status and ffmpeg_status != "system":
        os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ.get("PATH", "")

    return True


if __name__ == "__main__":
    ensure_dependencies()
