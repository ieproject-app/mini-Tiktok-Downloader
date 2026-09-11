import os
import sys

# Force UTF-8 stream output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
import webbrowser
import subprocess
from pathlib import Path

# Add engine src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Run preflight check before imports to ensure dependencies & ffmpeg
from preflight import ensure_dependencies, is_ffmpeg_available
ensure_dependencies()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt, Confirm

from config_manager import ConfigManager
from downloader import (
    TikTokDownloader,
    normalize_tiktok_url,
    is_supported_tiktok_url,
    ALL_FORMATS,
    FORMAT_VIDEO_NO_WM,
    FORMAT_VIDEO_WM,
    FORMAT_AUDIO_MP3,
    FORMAT_AUDIO_M4A,
    is_audio_format,
    ANSI_RE,
)
import updater

console = Console(force_terminal=True, legacy_windows=False)
cfg = ConfigManager()

APP_VERSION = "1.0.0"
APP_NAME = "mini-TikTok-Downloader"
SNIPGEEK_LABS_URL = "https://labs.snipgeek.com/"
GITHUB_URL = "https://github.com/ieproject-app/mini-Tiktok-Downloader"

BROWSER_CHOICES = ["chrome", "edge", "firefox", "brave", "vivaldi", "opera", "safari", ""]


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def format_duration(seconds):
    if not seconds:
        return "N/A"
    mins, secs = divmod(int(seconds), 60)
    hrs, mins = divmod(mins, 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def format_views(n):
    if not n:
        return "N/A"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


# ─────────────────────────────────────────────────────────────────────────────
#  UI Rendering
# ─────────────────────────────────────────────────────────────────────────────

def render_header():
    header_text = (
        f"[bold magenta]🎵 mini-TikTok-Downloader[/bold magenta]\n"
        f"[dim white]Download video & audio TikTok tanpa watermark[/dim white]\n\n"
        f"[bold yellow]by SnipGeek · {GITHUB_URL}[/bold yellow]"
    )
    console.print(Panel(header_text, border_style="magenta", box=box.ASCII, expand=False))


def render_status_bar():
    curr_dir = cfg.get_root_download_dir()
    curr_fmt = cfg.get("last_format", FORMAT_VIDEO_NO_WM)
    fmt_label = dict((k, v) for k, v in ALL_FORMATS).get(curr_fmt, curr_fmt)
    total_dl = cfg.get("download_count", 0)
    ffmpeg_stat = "[bold green]✓ Ready[/bold green]" if is_ffmpeg_available() else "[bold red]✗ Missing[/bold red]"
    cb = (cfg.get("cookies_browser", "") or "").strip()
    cookies_stat = f"[bold green]{cb}[/bold green]" if cb else "[dim]Off[/dim]"

    table = Table(show_header=False, box=box.ASCII, expand=False)
    table.add_row("[bold magenta]📁 Folder Download[/bold magenta]", f"[underline]{curr_dir}[/underline]")
    table.add_row("[bold green]🎬 Format Default[/bold green]", f"[bold]{fmt_label}[/bold]")
    table.add_row("[bold blue]⚙  FFmpeg[/bold blue]", ffmpeg_stat)
    table.add_row("[bold cyan]🍪 Browser Cookies[/bold cyan]", cookies_stat)
    table.add_row("[bold yellow]📥 Total Download[/bold yellow]", f"[bold]{total_dl} video[/bold]")
    console.print(table)

    console.print(
        "\n[dim]Paste URL TikTok → Enter. "
        "Ketik [bold]S[/bold]=Settings  [bold]O[/bold]=Buka Folder  [bold]Q[/bold]=Keluar[/dim]"
    )


def render_format_menu():
    table = Table(title="Format Download", box=box.ASCII, expand=False)
    table.add_column("No", style="bold cyan", justify="center")
    table.add_column("Tipe", style="bold magenta")
    table.add_column("Kualitas", style="white")

    fmt_map = {
        "1": (FORMAT_VIDEO_NO_WM, "Video", "Tanpa Watermark (MP4) ⭐ Rekomendasi"),
        "2": (FORMAT_VIDEO_WM,    "Video", "Dengan Watermark (MP4)"),
        "3": (FORMAT_AUDIO_MP3,   "Audio", "MP3 320 kbps"),
        "4": (FORMAT_AUDIO_M4A,   "Audio", "M4A (Kualitas Asli)"),
    }

    for num, (_, tipe, label) in fmt_map.items():
        table.add_row(num, tipe, label)

    console.print(table)
    return fmt_map


def select_format_interactive(last_fmt):
    fmt_map = render_format_menu()
    reverse = {v[0]: k for k, v in fmt_map.items()}
    default_num = reverse.get(last_fmt, "1")
    last_label = dict((v[0], v[2]) for v in fmt_map.values()).get(last_fmt, last_fmt)

    console.print(f"[dim]Enter = gunakan terakhir: [bold]{last_label}[/bold][/dim]")
    console.print("[dim]B = Batal[/dim]")

    choice = Prompt.ask("Pilih format", default="").strip()

    if choice.lower() == "b":
        return None
    if choice == "":
        return last_fmt
    if choice in fmt_map:
        return fmt_map[choice][0]
    return last_fmt


def choose_folder_gui(current_folder):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        selected = filedialog.askdirectory(
            initialdir=current_folder,
            title="Pilih Folder Download"
        )
        root.destroy()
        if selected:
            return selected
    except Exception as e:
        console.print(f"[yellow]⚠  GUI folder picker tidak tersedia: {e}[/yellow]")
    return current_folder


def check_milestone(current_count):
    if current_count == 5 or (current_count > 5 and current_count % 25 == 0):
        console.print()
        appreciation = Panel(
            f"🎉 Kamu sudah download [bold]{current_count}[/bold] video TikTok!\n"
            f"Terima kasih sudah pakai mini-TikTok-Downloader ✨\n"
            f"[dim]{SNIPGEEK_LABS_URL}[/dim]",
            title="🏆 Milestone",
            border_style="yellow",
            box=box.ASCII
        )
        console.print(appreciation)


# ─────────────────────────────────────────────────────────────────────────────
#  Update Flow
# ─────────────────────────────────────────────────────────────────────────────

def run_update_flow(force=False):
    if not updater.should_check(cfg, force=force):
        return
    updater.mark_checked(cfg)

    with console.status("Memeriksa update...", spinner="dots"):
        rel = updater.fetch_latest_release()
    if not rel:
        if force:
            console.print("[yellow]Gagal memeriksa update (cek koneksi internet).[/yellow]")
        return

    if not updater.is_newer(rel["version"], APP_VERSION):
        if force:
            console.print(f"[green]✓ Aplikasi sudah versi terbaru (v{APP_VERSION}).[/green]")
        return

    console.print(f"\n[bold cyan]✨ Update tersedia! v{APP_VERSION} → v{rel['version']}[/bold cyan]")
    notes = (rel.get("notes") or "").strip()
    if notes:
        shown = notes if len(notes) <= 800 else notes[:800].rsplit("\n", 1)[0] + "\n…"
        console.print(Panel(shown, title=f"Changelog v{rel['version']}", border_style="cyan", box=box.ASCII))

    if not Confirm.ask("Update sekarang?", default=False):
        console.print(f"[dim]Download manual: {rel['url']}[/dim]")
        return

    if updater.spawn_installer_update():
        console.print("[green]Installer berjalan di background. Aplikasi akan restart...[/green]")
        time.sleep(2)
        sys.exit(0)
    console.print("[red]Gagal memulai update otomatis.[/red]")


# ─────────────────────────────────────────────────────────────────────────────
#  Settings Menu
# ─────────────────────────────────────────────────────────────────────────────

def settings_menu():
    while True:
        render_header()
        console.print(Panel("⚙  SETTINGS", border_style="yellow", box=box.ASCII))

        curr_dir = cfg.get_root_download_dir()
        curr_fmt = cfg.get("last_format", FORMAT_VIDEO_NO_WM)
        fmt_label = dict((k, v) for k, v in ALL_FORMATS).get(curr_fmt, curr_fmt)

        console.print(f"[dim]Folder saat ini: {curr_dir}[/dim]")
        console.print(f"[dim]Format default : {fmt_label}[/dim]")
        console.print()
        console.print("[bold cyan][1][/bold cyan] Ganti folder download")
        console.print("[bold cyan][2][/bold cyan] Buka folder download")
        console.print("[bold cyan][3][/bold cyan] Ubah format default")
        console.print("[bold cyan][4][/bold cyan] Cookies browser (untuk akun private)")
        console.print("[bold cyan][5][/bold cyan] Cek update")
        console.print("[bold cyan][6][/bold cyan] Buka GitHub repo")
        console.print("[bold cyan][0][/bold cyan] Kembali")

        opt = Prompt.ask("Pilihan", choices=["1","2","3","4","5","6","0"], default="0")

        if opt == "0":
            break
        elif opt == "1":
            old_dir = cfg.get_root_download_dir()
            new_dir = choose_folder_gui(old_dir)
            if new_dir and new_dir != old_dir:
                cfg.set_root_download_dir(new_dir)
                console.print(f"[green]✓ Folder download diubah ke: {new_dir}[/green]")
                time.sleep(1)
        elif opt == "2":
            cfg.open_download_folder()
            console.print("[green]✓ Folder dibuka.[/green]")
            time.sleep(1)
        elif opt == "3":
            new_fmt = select_format_interactive(cfg.get("last_format", FORMAT_VIDEO_NO_WM))
            if new_fmt:
                cfg.set("last_format", new_fmt)
                fmt_lbl = dict(ALL_FORMATS).get(new_fmt, new_fmt)
                console.print(f"[green]✓ Format default: {fmt_lbl}[/green]")
                time.sleep(1)
        elif opt == "4":
            current = cfg.get("cookies_browser", "") or "Off"
            console.print(f"[dim]Cookies browser saat ini: {current}[/dim]")
            console.print("[dim]Cookies diperlukan untuk download video akun private/age-restricted.[/dim]")
            console.print("[dim]Pastikan browser sudah login ke TikTok.[/dim]")
            console.print()
            for i, b in enumerate(BROWSER_CHOICES[:-1], 1):
                console.print(f"[bold cyan][{i}][/bold cyan] {b}")
            console.print(f"[bold cyan][{len(BROWSER_CHOICES)-1}][/bold cyan] Nonaktifkan cookies")

            choices = [str(i) for i in range(len(BROWSER_CHOICES))]
            pilihan = Prompt.ask("Pilih browser", choices=choices, default="0")
            chosen = BROWSER_CHOICES[int(pilihan)] if int(pilihan) < len(BROWSER_CHOICES) else ""
            cfg.set("cookies_browser", chosen)
            if chosen:
                console.print(f"[green]✓ Cookies dari browser: {chosen}[/green]")
            else:
                console.print("[green]✓ Cookies browser dinonaktifkan.[/green]")
            time.sleep(1)
        elif opt == "5":
            run_update_flow(force=True)
            Prompt.ask("Enter untuk lanjut")
        elif opt == "6":
            webbrowser.open(GITHUB_URL)
            console.print("[green]✓ GitHub dibuka di browser.[/green]")
            time.sleep(1)


# ─────────────────────────────────────────────────────────────────────────────
#  Main Loop
# ─────────────────────────────────────────────────────────────────────────────

def main():
    downloader = TikTokDownloader(
        config_manager=cfg,
        ffmpeg_dir=str(Path(__file__).resolve().parent.parent / "bin")
                    if (Path(__file__).resolve().parent.parent / "bin" / "ffmpeg.exe").exists()
                    else None
    )

    # Cek update (maks 1x per 24 jam)
    run_update_flow(force=False)

    while True:
        render_header()
        render_status_bar()

        input_url = Prompt.ask("\n[bold magenta]URL TikTok[/bold magenta]").strip()

        if not input_url:
            continue

        cmd = input_url.lower()
        if cmd == 'q':
            console.print("[dim]Sampai jumpa! 👋[/dim]")
            break
        elif cmd == 's':
            settings_menu()
            continue
        elif cmd == 'o':
            cfg.open_download_folder()
            console.print("[green]✓ Folder download dibuka.[/green]")
            time.sleep(1)
            continue
        elif cmd == 'w':
            webbrowser.open(SNIPGEEK_LABS_URL)
            console.print("[green]✓ SnipGeek Labs dibuka di browser.[/green]")
            time.sleep(1)
            continue
        else:
            input_url = normalize_tiktok_url(input_url)

        # ── Validasi URL ─────────────────────────────────────────────────
        if not is_supported_tiktok_url(input_url):
            console.print()
            console.print(Panel(
                "[bold red]❌ URL tidak dikenali.[/bold red]\n\n"
                "Pastikan URL berasal dari TikTok. Contoh yang valid:\n"
                "  [dim]https://www.tiktok.com/@username/video/1234567890[/dim]\n"
                "  [dim]https://vm.tiktok.com/XXXXXXX/[/dim]\n"
                "  [dim]https://vt.tiktok.com/XXXXXXX/[/dim]",
                border_style="red",
                box=box.ASCII
            ))
            Prompt.ask("Enter untuk lanjut")
            continue

        # ── Ambil Info Video ─────────────────────────────────────────────
        console.print()
        with console.status("🔍 Mengambil informasi video...", spinner="dots"):
            try:
                info = downloader.get_video_info(input_url)
            except Exception as e:
                err = ANSI_RE.sub('', str(e))
                console.print(Panel(
                    f"[bold red]❌ Gagal mengambil info video.[/bold red]\n\n{err}\n\n"
                    "[dim]Tips: Coba aktifkan cookies browser di Settings (S) "
                    "jika video adalah konten private/age-restricted.[/dim]",
                    border_style="red",
                    box=box.ASCII
                ))
                Prompt.ask("Enter untuk lanjut")
                continue

        # ── Tampilkan Info Card ──────────────────────────────────────────
        title = info.get('title') or info.get('description') or 'TikTok Video'
        author = info.get('uploader') or info.get('creator') or info.get('channel', 'Unknown')
        duration = format_duration(info.get('duration'))
        views = format_views(info.get('view_count'))
        likes = format_views(info.get('like_count'))
        video_id = info.get('id', '')

        # Potong title yang terlalu panjang untuk display
        display_title = title[:80] + "..." if len(title) > 80 else title

        info_table = Table(title="📱 Info Video TikTok", box=box.ASCII, expand=False)
        info_table.add_column("Field", style="bold cyan")
        info_table.add_column("Value", style="white")
        info_table.add_row("👤 Author", author)
        info_table.add_row("📝 Judul/Caption", display_title)
        info_table.add_row("⏱  Durasi", duration)
        info_table.add_row("👁  Views", views)
        info_table.add_row("❤️  Likes", likes)
        info_table.add_row("🆔 ID", video_id)
        console.print()
        console.print(info_table)
        console.print()

        # ── Pilih Format ─────────────────────────────────────────────────
        last_fmt = cfg.get("last_format", FORMAT_VIDEO_NO_WM)
        chosen_fmt = select_format_interactive(last_fmt)

        if not chosen_fmt:
            continue

        cfg.set("last_format", chosen_fmt)

        # ── Download ─────────────────────────────────────────────────────
        console.print()
        console.print("[bold cyan]⬇  Memulai download...[/bold cyan]")
        try:
            out_file, target_dir = downloader.download_with_fallback(
                url=input_url,
                fmt=chosen_fmt,
                title=title,
                video_id=video_id,
            )
            new_count = cfg.increment_download_count()

            console.print()
            console.print(Panel(
                f"[bold green]✅ Download selesai![/bold green]\n\n"
                f"[bold]File:[/bold] [underline]{out_file}[/underline]\n"
                f"[bold]Folder:[/bold] [underline]{target_dir}[/underline]\n\n"
                f"[dim]Total download: {new_count} video[/dim]",
                border_style="green",
                box=box.ASCII
            ))
            check_milestone(new_count)

        except Exception as e:
            err = ANSI_RE.sub('', str(e))
            console.print()
            console.print(Panel(
                f"[bold red]❌ Download gagal.[/bold red]\n\n{err}\n\n"
                "[dim]Tips:\n"
                "  • Aktifkan cookies browser di Settings (S)\n"
                "  • Pastikan koneksi internet stabil\n"
                "  • Coba URL ulang (salin langsung dari TikTok)[/dim]",
                border_style="red",
                box=box.ASCII
            ))

        # ── Next Action ──────────────────────────────────────────────────
        console.print()
        console.print("[bold cyan][1][/bold cyan] Download video lain")
        console.print("[bold cyan][2][/bold cyan] Buka folder hasil download")
        console.print("[bold cyan][3][/bold cyan] Settings")
        console.print("[bold cyan][0][/bold cyan] Keluar")

        nxt = Prompt.ask("Pilihan", choices=["1", "2", "3", "0"], default="1")

        if nxt == "0":
            console.print("[dim]Sampai jumpa! 👋[/dim]")
            break
        elif nxt == "2":
            cfg.open_download_folder(target_dir if 'target_dir' in dir() else None)
        elif nxt == "3":
            settings_menu()


if __name__ == "__main__":
    try:
        if "--version" in sys.argv:
            print(f"mini-TikTok-Downloader v{APP_VERSION}")
            sys.exit(0)
        if "update" in sys.argv[1:]:
            run_update_flow(force=True)
            sys.exit(0)
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Dibatalkan. Sampai jumpa! 👋[/dim]")
        sys.exit(0)
