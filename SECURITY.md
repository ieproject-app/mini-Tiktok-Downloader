# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | ✅ Active support  |

## Reporting a Vulnerability

If you discover a security vulnerability in mini-TikTok-Downloader, please report it responsibly:

1. **Do NOT** open a public GitHub issue for security vulnerabilities.
2. Contact us directly via the GitHub Security Advisory feature:
   - Go to the repository → **Security** tab → **Report a vulnerability**

### What to Include

- A clear description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

### Response Timeline

We aim to respond to security reports within **72 hours** and provide a fix within **7 days** for critical issues.

## Safe Usage Guidelines

- **This tool downloads public TikTok content only.** Do not use it to download private content without permission.
- **API keys and cookies** are stored locally in your machine's `%LOCALAPPDATA%\MiniTikTok\` folder and are never transmitted externally.
- **yt-dlp** is the underlying download engine. Keep it updated: `pip install -U yt-dlp`
- Always download from the official GitHub repository or via the install script.

## Third-party Dependencies

| Package  | Purpose            |
|----------|--------------------|
| yt-dlp   | Video extraction   |
| rich     | Terminal UI        |
| requests | Update checking    |

All dependencies are pinned in `requirements.txt`. Please ensure you're using trusted PyPI sources.
