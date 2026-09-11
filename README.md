# 🎵 mini-TikTok-Downloader

> Download video & audio TikTok **tanpa watermark** langsung dari terminal — cepat, ringan, gratis.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![yt-dlp](https://img.shields.io/badge/powered%20by-yt--dlp-red)](https://github.com/yt-dlp/yt-dlp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue?logo=windows)](https://github.com/ieproject-app/mini-Tiktok-Downloader)
[![by SnipGeek](https://img.shields.io/badge/by-SnipGeek-purple)](https://labs.snipgeek.com)

---

## ✨ Fitur

| Fitur | Keterangan |
|-------|-----------|
| 🚫 **Tanpa Watermark** | Download video TikTok tanpa logo/watermark bawaan |
| 🎬 **Video MP4** | Download video kualitas terbaik (no watermark / with watermark) |
| 🎵 **Audio MP3 / M4A** | Ekstrak audio dari video TikTok (MP3 320kbps atau M4A asli) |
| 🔗 **URL Pendek** | Support `vm.tiktok.com`, `vt.tiktok.com`, dan URL pendek lainnya |
| 🍪 **Browser Cookies** | Download konten private/age-restricted via cookies browser |
| 📁 **Auto-folder** | Video & audio disimpan otomatis ke subfolder terpisah |
| 🔄 **Auto-update** | Cek update otomatis dari GitHub Releases (1x/24 jam) |
| ⚡ **Fallback otomatis** | Retry strategi berbeda bila download pertama gagal |

---

## 🚀 Cara Install

### Opsi A — One-liner (Rekomendasi)

Buka **PowerShell** dan jalankan:

```powershell
irm https://raw.githubusercontent.com/ieproject-app/mini-Tiktok-Downloader/main/install.ps1 | iex
```

Setelah selesai, buka terminal baru dan jalankan:

```
minitk
```

### Opsi B — Manual (Portable)

1. Clone atau download repo ini
2. Pastikan Python 3.9+ sudah terinstall
3. Double-click `run.bat` atau jalankan:
   ```
   python _engine\src\app.py
   ```

> FFmpeg akan otomatis didownload saat pertama kali dijalankan (±100MB).

---

## 📖 Cara Pakai

```
Paste URL TikTok → Enter → Pilih format → Download selesai!
```

### URL yang Didukung

```
https://www.tiktok.com/@username/video/1234567890123456789
https://vm.tiktok.com/XXXXXXX/
https://vt.tiktok.com/XXXXXXX/
```

### Format Download

| Pilihan | Format | Keterangan |
|---------|--------|-----------|
| `1` | **Video (No Watermark)** ⭐ | MP4 kualitas terbaik, TANPA watermark TikTok (rasio asli) |
| `2` | **Video Landscape 16:9** 🎬 | MP4 potong bar hitam otomatis, pas untuk layar laptop/TV |
| `3` | Video (With Watermark) | MP4 kualitas terbaik, dengan watermark |
| `4` | Audio MP3 | 320 kbps, dengan cover art embed |
| `5` | Audio M4A | Kualitas asli (lebih kecil) |

### Shortcut Keyboard

| Tombol | Aksi |
|--------|------|
| `S` | Settings |
| `O` | Buka folder download |
| `W` | Buka SnipGeek Labs |
| `Q` | Keluar |

---

## 📁 Lokasi File

### Mode Portable (via `run.bat`)
```
mini-Tiktok-Downloader/
└── downloads/
    ├── video/        ← file MP4
    └── audio/        ← file MP3/M4A
```

### Mode Installed (via installer)
```
%USERPROFILE%\Downloads\MiniTikTok\
├── video/
└── audio/

%LOCALAPPDATA%\MiniTikTok\
├── app/              ← file aplikasi
├── data/             ← config.json, ffmpeg bin
└── venv/             ← Python environment
```

---

## 🍪 Download Video Private / Age-Restricted

Untuk konten yang memerlukan login:

1. Login ke TikTok di browser (Chrome/Edge/Firefox/dll)
2. Buka **Settings (S)** → **Cookies browser**
3. Pilih browser yang digunakan
4. Download seperti biasa — app akan otomatis pakai cookies

---

## 🔧 Persyaratan Sistem

| Komponen | Versi Minimum |
|----------|--------------|
| OS | Windows 10/11 |
| Python | 3.9+ |
| FFmpeg | Auto-download (tidak perlu install manual) |

---

## 🆚 Perbandingan dengan mini-YT-Downloader

| Fitur | mini-YT-Downloader | mini-TikTok-Downloader |
|-------|-------------------|----------------------|
| YouTube | ✅ | ❌ |
| TikTok | ❌ | ✅ |
| Tanpa Watermark | N/A | ✅ |
| Playlist | ✅ | ❌ (TikTok tidak punya playlist standar) |
| Potong per Chapter | ✅ (Murottal) | ❌ |
| Audio MP3/M4A | ✅ | ✅ |
| Browser Cookies | ✅ | ✅ |
| Auto-update | ✅ | ✅ |

---

## ❓ FAQ

**Q: Kenapa ada watermark di hasil download?**  
A: Gunakan pilihan format `1 - Video (No Watermark)`. Jika masih ada, coba aktifkan browser cookies.

**Q: Error "Unable to extract video data"?**  
A: TikTok kadang memblokir request tanpa cookies. Aktifkan cookies browser di Settings.

**Q: Apakah bisa download video dari akun private?**  
A: Ya, asalkan akun TikTok sudah di-follow dan cookies browser sudah aktif.

**Q: Bagaimana cara update yt-dlp?**  
A: Jalankan: `pip install -U yt-dlp` (untuk mode portable) atau biarkan installer mengurus otomatis.

---

## 📄 Lisensi

MIT License — lihat [LICENSE](LICENSE) untuk detail.

---

## 🙏 Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — Download engine
- [Rich](https://github.com/Textualize/rich) — Terminal UI
- [SnipGeek](https://labs.snipgeek.com) — Developer

---

> ⚠️ **Disclaimer**: Tool ini hanya untuk keperluan pribadi dan konten yang diizinkan. Hormati hak cipta kreator TikTok. Jangan digunakan untuk tujuan komersial tanpa izin.
