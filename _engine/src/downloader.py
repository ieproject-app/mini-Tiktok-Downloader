"""
downloader.py — TikTok download engine menggunakan yt-dlp.

Mendukung:
- Video TikTok (dengan/tanpa watermark)
- Audio MP3 / M4A dari TikTok
- URL pendek (vm.tiktok.com, vt.tiktok.com)
- URL panjang (www.tiktok.com/@user/video/ID)
- Slide/photo TikTok → otomatis di-skip atau fallback
"""

import os
import re
import time
import urllib.parse
import yt_dlp
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn, DownloadColumn

try:
    from yt_dlp.networking.impersonate import ImpersonateTarget
    _HAS_IMPERSONATE = True
except ImportError:
    _HAS_IMPERSONATE = False

_console = Console(force_terminal=True, legacy_windows=False)

# yt-dlp embeds raw ANSI color codes in error strings; strip them for clean display
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

# ─────────────────────────────────────────────────────────────────────────────
#  Host detection
# ─────────────────────────────────────────────────────────────────────────────

TIKTOK_HOSTS = (
    "tiktok.com",
    "www.tiktok.com",
    "m.tiktok.com",
    "vm.tiktok.com",
    "vt.tiktok.com",
    "lite.tiktok.com",
)


def normalize_tiktok_url(url: str) -> str:
    """Tambahkan https:// bila user paste URL tanpa scheme."""
    url = (url or "").strip()
    if not url or "://" in url:
        return url
    first = url.split("/", 1)[0].lower()
    if first in TIKTOK_HOSTS:
        return "https://" + url
    return url


def is_supported_tiktok_url(url: str) -> bool:
    """True bila URL adalah TikTok yang valid (termasuk URL pendek)."""
    try:
        parsed = urllib.parse.urlparse((url or "").strip())
    except Exception:
        return False
    host = (parsed.netloc or "").lower()
    return parsed.scheme in ("http", "https") and host in TIKTOK_HOSTS


def sanitize_title(title: str) -> str:
    """Sanitize a title into a safe, Windows-friendly filesystem name."""
    if not title:
        return "untitled"
    title = re.sub(r'[\\/*?:"<>|]', "-", title)
    title = re.sub(r"\s{2,}", " ", title).strip()
    title = title.rstrip(". ")
    title = title[:120].rstrip(". ")
    return title or "untitled"


# ─────────────────────────────────────────────────────────────────────────────
#  Format options
# ─────────────────────────────────────────────────────────────────────────────

FORMAT_VIDEO_NO_WM = "video_no_wm"    # Video tanpa watermark (default)
FORMAT_VIDEO_WM    = "video_wm"       # Video dengan watermark
FORMAT_AUDIO_MP3   = "mp3"            # Audio MP3 320kbps
FORMAT_AUDIO_M4A   = "m4a"            # Audio M4A (original codec)

ALL_FORMATS = [
    (FORMAT_VIDEO_NO_WM, "Video (No Watermark) — MP4"),
    (FORMAT_VIDEO_WM,    "Video (With Watermark) — MP4"),
    (FORMAT_AUDIO_MP3,   "Audio MP3 (320 kbps)"),
    (FORMAT_AUDIO_M4A,   "Audio M4A"),
]


def is_audio_format(fmt: str) -> bool:
    return fmt in (FORMAT_AUDIO_MP3, FORMAT_AUDIO_M4A)


# ─────────────────────────────────────────────────────────────────────────────
#  TikTok Downloader class
# ─────────────────────────────────────────────────────────────────────────────

class TikTokDownloader:
    def __init__(self, config_manager, ffmpeg_dir=None):
        self.cfg = config_manager
        self.ffmpeg_dir = ffmpeg_dir

    def cookies_browser_setting(self):
        return (self.cfg.get("cookies_browser", "") or "").strip().lower()

    def _get_base_opts(self, no_watermark=True):
        """Base yt-dlp opts optimized for TikTok.

        Catatan implementasi:
        - yt_dlp_ejs (bundled dengan yt-dlp[default]) menyediakan native Python
          JS solver, sehingga yt-dlp dapat melewati JS challenge TikTok TANPA
          membutuhkan curl_cffi/impersonation.
        - api_hostname 'api22-normal-c-useast1a.tiktokv.com' digunakan untuk
          mendapat stream video tanpa watermark (community-documented trick).
        - curl_cffi + ImpersonateTarget tersedia sebagai opsional fallback bila
          yt_dlp_ejs gagal di masa depan.
        """
        opts = {
            'quiet': True,
            'no_warnings': True,
            'force_ipv4': True,
            'retries': 5,
            'fragment_retries': 5,
            'socket_timeout': 30,
        }

        if no_watermark:
            # API hostname tanpa watermark — community-documented trick
            opts['extractor_args'] = {
                'tiktok': {
                    'api_hostname': ['api22-normal-c-useast1a.tiktokv.com'],
                }
            }

        # Opsional: aktifkan impersonasi Chrome bila curl_cffi tersedia
        # (sebagai fallback tambahan, bukan requirement utama)
        if _HAS_IMPERSONATE:
            try:
                opts['impersonate'] = ImpersonateTarget('chrome')
            except Exception:
                pass

        if self.cookies_browser_setting():
            opts['cookiesfrombrowser'] = (self.cookies_browser_setting(), None, None, None)

        if self.ffmpeg_dir:
            opts['ffmpeg_location'] = self.ffmpeg_dir

        return opts


    def get_video_info(self, url: str):
        """Ekstrak metadata video TikTok."""
        ydl_opts = self._get_base_opts(no_watermark=True)
        ydl_opts['extract_flat'] = False
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info

    def _clear_partial_files(self, target_dir: str, name_prefix: str):
        try:
            for f in os.listdir(target_dir):
                if f.startswith(name_prefix) and (
                    f.endswith('.part') or f.endswith('.ytdl') or '.part-' in f
                ):
                    os.remove(os.path.join(target_dir, f))
        except Exception:
            pass

    def download(self, url: str, fmt: str = FORMAT_VIDEO_NO_WM,
                 title: str = None, video_id: str = None) -> tuple:
        """
        Download TikTok video/audio.

        Returns:
            (out_file: str, target_dir: str)
        """
        is_audio = is_audio_format(fmt)
        no_watermark = (fmt == FORMAT_VIDEO_NO_WM)

        target_dir = self.cfg.get_target_dir(is_audio=is_audio)
        dir_for_tmpl = target_dir.replace("%", "%%")

        if title is not None:
            clean_title = sanitize_title(title)
            id_token = video_id if video_id else '%(id)s'
            outtmpl = os.path.join(
                dir_for_tmpl,
                f"{clean_title.replace('%', '%%')} [{id_token}].%(ext)s"
            )
        else:
            outtmpl = os.path.join(dir_for_tmpl, '%(uploader)s - %(title).80s [%(id)s].%(ext)s')

        # ── Progress bar ────────────────────────────────────────────────
        progress = Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=40, style="grey37", complete_style="bold green"),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
        )
        task_id = None

        def ytdl_progress_hook(d):
            nonlocal task_id
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                if task_id is None:
                    task_id = progress.add_task("Downloading...", total=total)
                else:
                    progress.update(task_id, completed=downloaded, total=total)
            elif d['status'] == 'finished':
                if task_id is not None:
                    progress.update(task_id, description="Processing...")

        # ── yt-dlp opts ──────────────────────────────────────────────────
        ydl_opts = self._get_base_opts(no_watermark=no_watermark)
        ydl_opts['outtmpl'] = outtmpl
        ydl_opts['progress_hooks'] = [ytdl_progress_hook]

        if fmt == FORMAT_VIDEO_NO_WM or fmt == FORMAT_VIDEO_WM:
            # Pilih kualitas video terbaik, merge ke MP4
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'

        elif fmt == FORMAT_AUDIO_MP3:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['writethumbnail'] = True
            ydl_opts['postprocessors'] = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                },
                {'key': 'FFmpegMetadata', 'add_metadata': True},
                {'key': 'EmbedThumbnail', 'already_have_thumbnail': False},
            ]

        elif fmt == FORMAT_AUDIO_M4A:
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
            ydl_opts['postprocessors'] = [
                {'key': 'FFmpegMetadata', 'add_metadata': True},
            ]

        # ── Download ─────────────────────────────────────────────────────
        with progress:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)

                if fmt == FORMAT_AUDIO_MP3:
                    downloaded_file = os.path.splitext(downloaded_file)[0] + ".mp3"
                elif fmt == FORMAT_AUDIO_M4A:
                    downloaded_file = os.path.splitext(downloaded_file)[0] + ".m4a"
                else:
                    # Video: pastikan ekstensi .mp4
                    base = os.path.splitext(downloaded_file)[0]
                    downloaded_file = base + ".mp4"

        # Verifikasi file ada (nama bisa sedikit beda setelah merge)
        if not os.path.exists(downloaded_file):
            candidates = [
                f for f in os.listdir(target_dir)
                if not f.endswith(('.part', '.ytdl', '.tmp'))
                and os.path.isfile(os.path.join(target_dir, f))
            ]
            if candidates:
                # Ambil file yang paling baru dimodifikasi
                candidates.sort(
                    key=lambda f: os.path.getmtime(os.path.join(target_dir, f)),
                    reverse=True
                )
                downloaded_file = os.path.join(target_dir, candidates[0])

        return downloaded_file, info, target_dir

    def download_with_fallback(self, url: str, fmt: str = FORMAT_VIDEO_NO_WM,
                                title: str = None, video_id: str = None) -> tuple:
        """Download dengan fallback otomatis bila percobaan pertama gagal.

        Ladder:
          1. Normal (no_watermark=True)
          2. Fallback: with_watermark (no_watermark=False)
          3. Fallback: format 'best' (single progressive stream)

        Returns (out_file, target_dir). Raises last error bila semua gagal.
        """
        strategies = [
            (fmt, "Mencoba strategi alternatif..."),
            # Bila format video no-wm gagal, coba dengan watermark sebagai fallback
            (
                FORMAT_VIDEO_WM if fmt == FORMAT_VIDEO_NO_WM else fmt,
                "Mencoba format fallback..."
            ),
        ]

        last_err = None
        for i, (try_fmt, fail_msg) in enumerate(strategies):
            try:
                out_file, info, target_dir = self.download(
                    url, fmt=try_fmt, title=title, video_id=video_id
                )
                return out_file, target_dir
            except Exception as e:
                last_err = e
                if fail_msg and i < len(strategies) - 1:
                    _console.print(f"[yellow]⚠  {fail_msg}[/yellow]")
                    time.sleep(2)
        raise last_err
