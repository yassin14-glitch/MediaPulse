# Changelog

All notable changes to **MediaPulse Pro** are documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.1.0] - 2026-10-14

### 🚀 Major Enhancements & Performance
- **Massive Size Reduction**: Reduced distribution footprint by ~50% by eliminating duplicate bundled FFmpeg runtimes and pruning unused heavy libraries (`matplotlib`, `numpy`, `customtkinter`, `jedi`, etc.).
- **Sub-100ms Startup**: Replaced blocking sleep timers with asynchronous non-blocking socket synchronization, bringing the application window to screen almost instantly.
- **Throttled Progress Reporting**: Rate-limited UI hook updates to 120ms intervals, eliminating CPU spikes and UI flooding during multi-megabyte/second transfers.
- **Automatic Resume & Connection Recovery**: Increased retry and fragment retry tolerance to 10 attempts with automatic partial fragment continuation (`continuedl`).

### 🌐 Complete Internationalization (i18n)
- Native translations across **12 languages**:
  - English (`en`)
  - Arabic (`ar`) with authentic right-to-left (`dir="rtl"`) UI layout and typography
  - French (`fr`)
  - Spanish (`es`)
  - German (`de`)
  - Portuguese (`pt`)
  - Turkish (`tr`)
  - Russian (`ru`)
  - Chinese Simplified (`zh`)
  - Japanese (`ja`)
  - Hindi (`hi`)
  - Indonesian (`id`)
- Zero hardcoded UI strings; automatic system language detection and instant live language switching without application restart.
- Automated test coverage ensuring 100% key parity across all language bundles.

### ✨ New Features & Tools
- **Video Trimmer**: Extract and download only a specified time range (`start_time` - `end_time`) with frame accuracy without downloading full streams.
- **Batch Link Importer**: Paste multiple URLs simultaneously to automatically queue sequential background downloads.
- **Drag-to-Reorder Queue**: Reorder pending downloads up or down on the fly, with individual pause, resume, and cancellation.
- **Searchable Library**: Real-time filtering of download history with instant "Play", "Show in Folder", and "Download Again" actions.
- **Pre-Download Link Preview**: High-resolution thumbnail, channel info, view count, and duration preview with instant format pills.
- **SponsorBlock Integration**: Optional auto-skipping of sponsored segments and promotional fillers.
- **Subtitles & Metadata**: Embed subtitles and album/video metadata directly into MP4/MKV containers.
- **Drag & Drop Links**: Drag links directly into the desktop window to trigger downloads.
- **Global Keyboard Shortcuts**: Quick navigation and controls (`Ctrl+V`, `Enter`, `Ctrl+F`, `Ctrl+,`, `Esc`).
- **On-Demand FFmpeg Downloader**: Diagnostic panel with 1-click automatic download and verification of static FFmpeg binaries.
- **Clipboard Watcher**: Automatic detection of copied multimedia links with floating download toasts.
- **First-Run Onboarding**: Glassmorphism walkthrough modal introducing core capabilities.

---

## [1.0.0] - 2026-10-14

### Initial Release
- Multi-platform video and audio downloader powered by `yt-dlp` and `FFmpeg 7.1`.
- Modern Glassmorphism desktop interface powered by Edge WebView2 and FastAPI.
- YouTube Pro tab supporting 4K, 1080p, playlists, and 320kbps MP3 extraction.
- Universal Web Video sniffer supporting Instagram Reels, TikTok, Twitter/X, Vimeo, Reddit, and HTML5 video streams.
- Automatic browser cookie integration for Firefox, Edge, Chrome, Brave, and Opera.
- High-DPI per-monitor awareness and custom Windows `AppUserModelID`.
- In-app yt-dlp updater and persistent settings storage.
