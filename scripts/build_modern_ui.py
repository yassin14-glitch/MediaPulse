"""Builds the comprehensive modern.html interface for MediaPulse Pro.
Includes i18n with RTL Arabic, Video Trimmer, Batch Queue with Reordering,
Searchable History, Settings with FFmpeg downloader, Keyboard Shortcuts,
Drag & Drop, and First-Run Onboarding.
"""
import os

HTML_CONTENT = r'''<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MediaPulse Pro • Universal Video Downloader</title>
    <style>
        :root {
            --bg: #090d16;
            --sidebar: #0f172a;
            --card: #131c2e;
            --card-hover: #1e293b;
            --border: #23334d;
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.4);
            --accent-green: #10b981;
            --accent-green-glow: rgba(16, 185, 129, 0.4);
            --danger: #ef4444;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --radius-lg: 16px;
            --radius-md: 10px;
            --radius-sm: 6px;
        }

        [dir="rtl"] {
            font-family: "Segoe UI", "Tahoma", "Cairo", -apple-system, sans-serif;
            text-align: right;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", Ubuntu, sans-serif;
        }

        body {
            background-color: var(--bg);
            color: var(--text);
            height: 100vh;
            display: flex;
            overflow: hidden;
        }

        /* 1. Sidebar */
        aside {
            width: 250px;
            background: var(--sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 24px 16px;
            flex-shrink: 0;
            transition: all 0.2s ease;
        }

        [dir="rtl"] aside {
            border-right: none;
            border-left: 1px solid var(--border);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 28px;
            padding-left: 8px;
        }
        [dir="rtl"] .brand {
            padding-left: 0;
            padding-right: 8px;
        }

        .brand-icon {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 4px 15px var(--primary-glow);
        }

        .brand-title {
            font-size: 17px;
            font-weight: 800;
            letter-spacing: -0.3px;
            background: linear-gradient(to right, #60a5fa, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .nav-label {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.8px;
            color: #64748b;
            margin: 0 0 10px 12px;
        }
        [dir="rtl"] .nav-label {
            margin: 0 12px 10px 0;
        }

        .nav-menu {
            display: flex;
            flex-direction: column;
            gap: 6px;
            flex: 1;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            border-radius: var(--radius-md);
            color: var(--text-muted);
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .nav-item:hover {
            background-color: var(--card-hover);
            color: var(--text);
        }

        .nav-item.active {
            background-color: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }

        .nav-icon {
            font-size: 18px;
            width: 22px;
            text-align: center;
        }

        .sidebar-footer {
            border-top: 1px solid var(--border);
            padding-top: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .quick-lang-select {
            background: #1e293b;
            border: 1px solid var(--border);
            color: #cbd5e1;
            padding: 6px 10px;
            border-radius: var(--radius-sm);
            font-size: 12px;
            cursor: pointer;
            width: 100%;
            outline: none;
        }

        /* 2. Main Content Container */
        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg);
            overflow-y: auto;
            position: relative;
        }

        header {
            height: 64px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 32px;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 20;
        }

        .header-title {
            font-size: 18px;
            font-weight: 700;
        }

        .header-badges {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .badge {
            background: #1e293b;
            border: 1px solid var(--border);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .badge.accent {
            background: rgba(16, 185, 129, 0.1);
            border-color: rgba(16, 185, 129, 0.3);
            color: #34d399;
        }

        .content-area {
            padding: 32px;
            max-width: 1080px;
            width: 100%;
            margin: 0 auto;
        }

        .tab-pane {
            display: none;
            animation: fadeIn 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .tab-pane.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* 3. Cards & Inputs */
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 24px;
            margin-bottom: 24px;
            position: relative;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
        }

        .card-title {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .url-input-container {
            position: relative;
            display: flex;
            align-items: center;
            margin-bottom: 16px;
        }

        .url-input {
            width: 100%;
            background: #0b1120;
            border: 2px solid var(--border);
            padding: 14px 160px 14px 44px;
            border-radius: var(--radius-md);
            color: var(--text);
            font-size: 14px;
            outline: none;
            transition: all 0.2s;
        }
        [dir="rtl"] .url-input {
            padding: 14px 44px 14px 160px;
        }

        .url-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-glow);
        }

        .url-icon {
            position: absolute;
            left: 14px;
            color: #64748b;
            font-size: 18px;
            pointer-events: none;
        }
        [dir="rtl"] .url-icon {
            left: auto;
            right: 14px;
        }

        .url-actions {
            position: absolute;
            right: 8px;
            display: flex;
            gap: 6px;
        }
        [dir="rtl"] .url-actions {
            right: auto;
            left: 8px;
        }

        .btn-input-action {
            background: #1e293b;
            border: 1px solid var(--border);
            color: #cbd5e1;
            padding: 8px 12px;
            border-radius: var(--radius-sm);
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-input-action:hover {
            background: #334155;
            color: #fff;
        }

        /* 4. Controls Row */
        .controls-row {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }

        .chip-group {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .chip {
            background: #0b1120;
            border: 1px solid var(--border);
            padding: 8px 14px;
            border-radius: var(--radius-sm);
            font-size: 12px;
            font-weight: 700;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s;
        }

        .chip:hover {
            background: #1e293b;
            color: var(--text);
            border-color: #475569;
        }

        .chip.active {
            background: rgba(59, 130, 246, 0.2);
            border-color: #3b82f6;
            color: #60a5fa;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
        }

        .select-dark {
            background: #0b1120;
            border: 1px solid var(--border);
            color: var(--text);
            padding: 8px 12px;
            border-radius: var(--radius-sm);
            font-size: 13px;
            font-weight: 600;
            outline: none;
            cursor: pointer;
        }

        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: #fff;
            border: none;
            padding: 12px 24px;
            border-radius: var(--radius-md);
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 15px var(--primary-glow);
            transition: all 0.2s;
        }

        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
        }

        .btn-secondary {
            background: #1e293b;
            border: 1px solid var(--border);
            color: #cbd5e1;
            padding: 12px 18px;
            border-radius: var(--radius-md);
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-secondary:hover {
            background: #334155;
            color: #fff;
        }

        /* 5. Preview Card */
        .preview-card {
            display: none;
            background: #0b1120;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 16px;
            margin-bottom: 20px;
            animation: fadeIn 0.2s;
        }

        .preview-flex {
            display: flex;
            gap: 16px;
        }

        .preview-thumb {
            width: 180px;
            height: 100px;
            border-radius: 8px;
            object-fit: cover;
            background: #1e293b;
            flex-shrink: 0;
        }

        .preview-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .preview-title {
            font-size: 15px;
            font-weight: 700;
            color: #f1f5f9;
            line-height: 1.3;
        }

        .preview-meta {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .trim-badge {
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(245, 158, 11, 0.4);
            color: #fbbf24;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
        }

        /* 6. Live Progress */
        .progress-card {
            background: #0b1120;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 18px;
            margin-top: 16px;
            display: none;
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .progress-track {
            height: 10px;
            background: #1e293b;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6, #10b981);
            width: 0%;
            border-radius: 5px;
            transition: width 0.15s ease-out;
        }

        .progress-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            color: var(--text-muted);
            font-weight: 600;
        }

        /* 7. Streams & History Items */
        .item-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .stream-item {
            background: #0b1120;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 14px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s;
        }

        .stream-item:hover {
            border-color: #3b82f6;
            background: #0d1527;
        }

        .btn-pill {
            background: #1e293b;
            border: 1px solid var(--border);
            color: var(--text);
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-pill:hover {
            background: #334155;
        }
        .btn-pill.success {
            background: #10b981;
            border-color: #10b981;
            color: #fff;
        }
        .btn-pill.success:hover { background: #059669; }
        .btn-pill.danger {
            background: rgba(239, 68, 68, 0.2);
            border-color: rgba(239, 68, 68, 0.4);
            color: #f87171;
        }
        .btn-pill.danger:hover { background: #ef4444; color: #fff; }

        /* 8. Modals & Overlays */
        .modal-backdrop {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(8px);
            z-index: 100;
            align-items: center;
            justify-content: center;
        }
        .modal-backdrop.show { display: flex; }

        .modal-box {
            background: #131c2e;
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            width: 520px;
            max-width: 90vw;
            padding: 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
            animation: modalPop 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        @keyframes modalPop {
            from { transform: scale(0.95); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .modal-title {
            font-size: 18px;
            font-weight: 800;
        }

        .close-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 20px;
            cursor: pointer;
        }
        .close-btn:hover { color: #fff; }

        .textarea-dark {
            width: 100%;
            height: 140px;
            background: #0b1120;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 12px;
            color: #fff;
            font-size: 13px;
            outline: none;
            resize: vertical;
        }

        .drag-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(59, 130, 246, 0.85);
            backdrop-filter: blur(8px);
            z-index: 200;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 24px;
            font-weight: 800;
            flex-direction: column;
            gap: 16px;
            pointer-events: none;
        }

        .clipboard-toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #1e293b;
            border: 1px solid #3b82f6;
            padding: 14px 20px;
            border-radius: var(--radius-md);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            display: none;
            align-items: center;
            gap: 14px;
            z-index: 90;
            animation: fadeIn 0.2s;
        }
        [dir="rtl"] .clipboard-toast {
            right: auto;
            left: 24px;
        }

        /* Settings Grid */
        .settings-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .setting-card {
            background: #0b1120;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 16px;
        }

        .setting-label {
            font-size: 13px;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 6px;
        }

        .setting-desc {
            font-size: 11px;
            color: var(--text-muted);
            margin-bottom: 12px;
            line-height: 1.4;
        }

        .toggle-label {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            color: #e2e8f0;
        }
    </style>
</head>
<body>

    <!-- Drag & Drop Overlay -->
    <div id="dragOverlay" class="drag-overlay">
        <span style="font-size: 48px;">📥</span>
        <div data-i18n="drop_overlay_text">Drop Video Links Here to Download</div>
    </div>

    <!-- Clipboard Detection Toast -->
    <div id="clipboardToast" class="clipboard-toast">
        <span style="font-size: 20px;">📋</span>
        <div>
            <div style="font-weight: 700; font-size: 13px;">Video Link Found in Clipboard</div>
            <div id="clipboardUrlText" style="font-size: 11px; color: #94a3b8; max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"></div>
        </div>
        <button class="btn-pill success" onclick="downloadClipboardUrl()">Download</button>
        <button class="btn-pill" onclick="dismissClipboardToast()">×</button>
    </div>

    <!-- 1. Left Sidebar Navigation -->
    <aside>
        <div class="brand">
            <div class="brand-icon">⚡</div>
            <div class="brand-title" data-i18n="app_name">MediaPulse Pro</div>
        </div>

        <div class="nav-label">NAVIGATION</div>
        <nav class="nav-menu">
            <div class="nav-item active" onclick="switchTab('youtube')">
                <span class="nav-icon">📺</span>
                <span data-i18n="nav_youtube">YouTube Pro</span>
            </div>
            <div class="nav-item" onclick="switchTab('web')">
                <span class="nav-icon">🌐</span>
                <span data-i18n="nav_web">Universal Web</span>
            </div>
            <div class="nav-item" onclick="switchTab('queue')">
                <span class="nav-icon">📋</span>
                <span data-i18n="nav_queue">Batch Queue</span>
                <span id="queueCountBadge" class="badge" style="margin-left: auto; padding: 2px 6px; font-size: 10px; display: none;">0</span>
            </div>
            <div class="nav-item" onclick="switchTab('history')">
                <span class="nav-icon">📁</span>
                <span data-i18n="nav_history">Library & History</span>
            </div>
            <div class="nav-item" onclick="switchTab('settings')">
                <span class="nav-icon">⚙️</span>
                <span data-i18n="nav_settings">Settings</span>
            </div>
        </nav>

        <div class="sidebar-footer">
            <select id="quickLangSelect" class="quick-lang-select" onchange="changeLanguage(this.value)">
                <option value="en">English</option>
                <option value="ar">العربية (Arabic)</option>
                <option value="fr">Français (French)</option>
                <option value="es">Español (Spanish)</option>
                <option value="de">Deutsch (German)</option>
                <option value="pt">Português (Portuguese)</option>
                <option value="tr">Türkçe (Turkish)</option>
                <option value="ru">Русский (Russian)</option>
                <option value="zh">简体中文 (Chinese)</option>
                <option value="ja">日本語 (Japanese)</option>
                <option value="hi">हिन्दी (Hindi)</option>
                <option value="id">Bahasa Indonesia</option>
            </select>
            <div style="font-size: 11px; color: #475569; text-align: center;">v1.1.0 • MIT Open Source</div>
        </div>
    </aside>

    <!-- 2. Main Content Area -->
    <main>
        <header>
            <div id="headerTitle" class="header-title" data-i18n="nav_youtube">YouTube Pro</div>
            <div class="header-badges">
                <div id="ffmpegBadge" class="badge">FFmpeg: Checking...</div>
                <div id="folderPill" class="badge" style="cursor: pointer;" onclick="openDownloadFolder()" title="Click to open download folder">📁 Downloads</div>
            </div>
        </header>

        <div class="content-area">

            <!-- TAB 1: YOUTUBE PRO -->
            <div id="pane-youtube" class="tab-pane active">
                <div class="card">
                    <div class="card-title">
                        <span>⚡</span>
                        <span data-i18n="nav_youtube">YouTube Pro</span>
                    </div>

                    <div class="url-input-container">
                        <span class="url-icon">🔗</span>
                        <input id="ytUrlInput" type="text" class="url-input" data-i18n-ph="input_placeholder_yt" placeholder="Paste YouTube video, playlist, or Short URL..." onkeydown="if(event.key==='Enter') fetchYoutubePreview()">
                        <div class="url-actions">
                            <button class="btn-input-action" onclick="fetchYoutubePreview()" data-i18n="btn_preview">Preview</button>
                            <button class="btn-input-action" onclick="openBatchModal()" data-i18n="btn_batch">Batch</button>
                        </div>
                    </div>

                    <!-- Pre-Download Preview Card -->
                    <div id="ytPreviewCard" class="preview-card">
                        <div class="preview-flex">
                            <img id="ytPreviewThumb" class="preview-thumb" src="" alt="Thumbnail">
                            <div class="preview-info">
                                <div>
                                    <div id="ytPreviewTitle" class="preview-title">Video Title</div>
                                    <div id="ytPreviewMeta" class="preview-meta">Channel • Duration • Views</div>
                                    <div id="trimBadgeIndicator" class="trim-badge" style="display: none;">
                                        <span id="trimBadgeText">✂️ Clip</span>
                                        <span style="cursor: pointer; margin-left: 6px;" onclick="clearTrim()">×</span>
                                    </div>
                                </div>
                                <div style="display: flex; gap: 8px; margin-top: 10px;">
                                    <button class="btn-pill" onclick="openTrimModal()" data-i18n="btn_trim">✂️ Trim Video</button>
                                    <button class="btn-pill" onclick="addCurrentToQueue()" data-i18n="btn_add_queue">+ Add to Queue</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Format & Quality Chips -->
                    <div class="controls-row">
                        <div class="chip-group">
                            <div class="chip active" onclick="selectPreset('best', 'mp4', this)" data-i18n="preset_best">Best Available</div>
                            <div class="chip" onclick="selectPreset('2160p', 'mp4', this)" data-i18n="preset_4k">4K Ultra HD</div>
                            <div class="chip" onclick="selectPreset('1440p', 'mp4', this)" data-i18n="preset_2k">2K QHD</div>
                            <div class="chip" onclick="selectPreset('1080p', 'mp4', this)" data-i18n="preset_1080p">1080p Full HD</div>
                            <div class="chip" onclick="selectPreset('720p', 'mp4', this)" data-i18n="preset_720p">720p HD</div>
                            <div class="chip" onclick="selectPreset('320k', 'mp3', this)" data-i18n="preset_mp3">MP3 Studio 320k</div>
                        </div>

                        <select id="ytContainerSelect" class="select-dark">
                            <option value="mp4">MP4 Video</option>
                            <option value="mkv">MKV Video</option>
                            <option value="webm">WebM Video</option>
                            <option value="mp3">MP3 Audio</option>
                            <option value="m4a">M4A Audio</option>
                            <option value="flac">FLAC Lossless</option>
                            <option value="opus">OPUS Audio</option>
                        </select>

                        <button id="btnYtDownload" class="btn-primary" onclick="startSingleDownload('yt')" style="margin-left: auto;">
                            <span>⬇️</span>
                            <span data-i18n="btn_download">Download Now</span>
                        </button>
                    </div>

                    <!-- Live Progress Card -->
                    <div id="ytProgressCard" class="progress-card">
                        <div class="progress-header">
                            <span id="ytProgressTitle" style="max-width: 70%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Downloading...</span>
                            <span id="ytProgressPercent" style="color: #60a5fa;">0.0%</span>
                        </div>
                        <div class="progress-track">
                            <div id="ytProgressFill" class="progress-fill"></div>
                        </div>
                        <div class="progress-footer">
                            <span id="ytProgressSpeed">-- MB/s</span>
                            <span id="ytProgressSize">0 B / 0 B</span>
                            <span id="ytProgressEta">ETA: --:--</span>
                            <button class="btn-pill danger" onclick="cancelActiveDownload('yt')" data-i18n="btn_cancel">Cancel</button>
                        </div>
                        <div id="ytSuccessActions" style="display: none; gap: 10px; margin-top: 14px;">
                            <button class="btn-pill success" onclick="playLastFile()">▶ Play File</button>
                            <button class="btn-pill" onclick="openDownloadFolder()">📂 Open Folder</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB 2: UNIVERSAL WEB SNIFFER -->
            <div id="pane-web" class="tab-pane">
                <div class="card">
                    <div class="card-title">
                        <span>🌐</span>
                        <span data-i18n="nav_web">Universal Web Video Sniffer</span>
                    </div>
                    <div class="url-input-container">
                        <span class="url-icon">🔗</span>
                        <input id="webUrlInput" type="text" class="url-input" data-i18n-ph="input_placeholder_web" placeholder="Paste any URL (Instagram, TikTok, Twitter/X, Vimeo, Reddit...)" onkeydown="if(event.key==='Enter') scanWebSite()">
                        <div class="url-actions">
                            <button id="btnWebScan" class="btn-input-action" onclick="scanWebSite()">Scan Page</button>
                        </div>
                    </div>

                    <div id="webStreamsContainer" class="item-list"></div>
                </div>
            </div>

            <!-- TAB 3: BATCH QUEUE -->
            <div id="pane-queue" class="tab-pane">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <div class="card-title" style="margin-bottom: 0;">
                            <span>📋</span>
                            <span data-i18n="nav_queue">Download Queue</span>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn-pill" onclick="openBatchModal()" data-i18n="btn_batch">+ Batch Add</button>
                            <button class="btn-pill" onclick="clearCompletedQueue()" data-i18n="btn_clear_completed">Clear Completed</button>
                        </div>
                    </div>

                    <div id="queueListContainer" class="item-list">
                        <div style="color: gray; padding: 20px 0;" data-i18n="queue_empty">Queue is empty. Paste links to start downloading.</div>
                    </div>
                </div>
            </div>

            <!-- TAB 4: LIBRARY & HISTORY -->
            <div id="pane-history" class="tab-pane">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
                        <div class="card-title" style="margin-bottom: 0;">
                            <span>📁</span>
                            <span data-i18n="nav_history">Library & History</span>
                        </div>
                        <div style="display: flex; gap: 8px; flex: 1; max-width: 380px;">
                            <input id="historySearchInput" type="text" class="select-dark" style="flex: 1;" placeholder="Search history..." oninput="filterHistory(this.value)">
                            <button class="btn-pill danger" onclick="clearAllHistory()" data-i18n="btn_clear_history">Clear All</button>
                        </div>
                    </div>

                    <div id="historyListContainer" class="item-list"></div>
                </div>
            </div>

            <!-- TAB 5: SETTINGS -->
            <div id="pane-settings" class="tab-pane">
                <div class="card">
                    <div class="card-title">
                        <span>⚙️</span>
                        <span data-i18n="settings_title">Application Settings</span>
                    </div>

                    <div class="settings-grid">
                        <!-- Language -->
                        <div class="setting-card">
                            <div class="setting-label" data-i18n="settings_lang">Language</div>
                            <div class="setting-desc">Choose interface language with instant switching and full RTL support.</div>
                            <select id="settingsLangSelect" class="select-dark" style="width: 100%;" onchange="saveSetting('language', this.value); changeLanguage(this.value);">
                                <option value="en">English</option>
                                <option value="ar">العربية (Arabic - RTL)</option>
                                <option value="fr">Français (French)</option>
                                <option value="es">Español (Spanish)</option>
                                <option value="de">Deutsch (German)</option>
                                <option value="pt">Português (Portuguese)</option>
                                <option value="tr">Türkçe (Turkish)</option>
                                <option value="ru">Русский (Russian)</option>
                                <option value="zh">简体中文 (Chinese)</option>
                                <option value="ja">日本語 (Japanese)</option>
                                <option value="hi">हिन्दी (Hindi)</option>
                                <option value="id">Bahasa Indonesia</option>
                            </select>
                        </div>

                        <!-- Download Folder -->
                        <div class="setting-card">
                            <div class="setting-label" data-i18n="settings_folder">Download Folder</div>
                            <div id="settingsFolderDisplay" style="font-size: 12px; color: #60a5fa; margin-bottom: 8px; word-break: break-all;">--</div>
                            <button class="btn-pill" onclick="chooseDownloadFolder()" data-i18n="btn_change_folder">Change Folder</button>
                        </div>

                        <!-- Filename Template -->
                        <div class="setting-card">
                            <div class="setting-label" data-i18n="settings_filename">Filename Template</div>
                            <div class="setting-desc">yt-dlp pattern (e.g. %(title)s [%(id)s].%(ext)s)</div>
                            <input id="settingsFilenameTemplate" type="text" class="select-dark" style="width: 100%;" onchange="saveSetting('filename_template', this.value)">
                        </div>

                        <!-- Speed Limit -->
                        <div class="setting-card">
                            <div class="setting-label" data-i18n="settings_speed_limit">Speed Limit</div>
                            <div class="setting-desc">Cap maximum transfer rate.</div>
                            <select id="settingsSpeedLimit" class="select-dark" style="width: 100%;" onchange="saveSetting('speed_limit', this.value)">
                                <option value="unlimited" data-i18n="speed_unlimited">Unlimited</option>
                                <option value="1M">1 MB/s</option>
                                <option value="2M">2 MB/s</option>
                                <option value="5M">5 MB/s</option>
                                <option value="10M">10 MB/s</option>
                            </select>
                        </div>

                        <!-- Browser Cookies -->
                        <div class="setting-card">
                            <div class="setting-label" data-i18n="settings_cookies">Browser Cookies</div>
                            <div class="setting-desc" data-i18n="cookies_desc">Extract cookies for Instagram Reels and restricted videos.</div>
                            <select id="settingsCookieSelect" class="select-dark" style="width: 100%;" onchange="saveSetting('browser_cookies', this.value)">
                                <option value="auto" data-i18n="cookies_auto">Auto-Detect (Recommended)</option>
                                <option value="firefox">Mozilla Firefox</option>
                                <option value="edge">Microsoft Edge</option>
                                <option value="chrome">Google Chrome</option>
                                <option value="brave">Brave Browser</option>
                                <option value="none" data-i18n="cookies_none">None (No Cookies)</option>
                            </select>
                        </div>

                        <!-- Network Proxy -->
                        <div class="setting-card">
                            <div class="setting-label" data-i18n="settings_proxy">Network Proxy</div>
                            <div class="setting-desc">HTTP or SOCKS5 proxy server.</div>
                            <input id="settingsProxy" type="text" class="select-dark" style="width: 100%;" placeholder="http://127.0.0.1:8080" onchange="saveSetting('proxy', this.value)">
                        </div>

                        <!-- Feature Toggles -->
                        <div class="setting-card" style="grid-column: span 2;">
                            <div class="setting-label">Enhanced Features</div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px;">
                                <label class="toggle-label">
                                    <input type="checkbox" id="toggleSubs" onchange="saveSetting('subtitles_embed', this.checked)">
                                    <span data-i18n="settings_subtitles_embed">Embed Subtitles</span>
                                </label>
                                <label class="toggle-label">
                                    <input type="checkbox" id="toggleMetadata" onchange="saveSetting('embed_metadata', this.checked)">
                                    <span data-i18n="settings_metadata">Embed Metadata & Thumbnail</span>
                                </label>
                                <label class="toggle-label">
                                    <input type="checkbox" id="toggleSponsor" onchange="saveSetting('sponsorblock', this.checked)">
                                    <span data-i18n="settings_sponsorblock">SponsorBlock Auto-Skip</span>
                                </label>
                                <label class="toggle-label">
                                    <input type="checkbox" id="toggleClipboard" onchange="saveSetting('clipboard_watcher', this.checked)">
                                    <span data-i18n="settings_clipboard">Clipboard Video Link Watcher</span>
                                </label>
                                <label class="toggle-label">
                                    <input type="checkbox" id="toggleSound" onchange="saveSetting('sound', this.checked)">
                                    <span data-i18n="settings_sound">Sound on Completion</span>
                                </label>
                            </div>
                        </div>

                        <!-- FFmpeg Diagnostics Card -->
                        <div class="setting-card" style="grid-column: span 2;">
                            <div class="setting-label" data-i18n="settings_ffmpeg_status">FFmpeg Diagnostics</div>
                            <div id="ffmpegStatusDetails" style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">Checking...</div>
                            <div id="ffmpegDownloadProgress" style="display: none; margin-bottom: 12px;">
                                <div class="progress-track"><div id="ffmpegProgressFill" class="progress-fill"></div></div>
                                <div id="ffmpegDownloadMsg" style="font-size: 11px; color: #60a5fa;">Downloading...</div>
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <button id="btnDownloadFfmpeg" class="btn-pill" onclick="downloadFfmpegOnDemand()" data-i18n="btn_download_ffmpeg">Download FFmpeg</button>
                                <button class="btn-pill" onclick="checkYtdlpUpdate()">Check yt-dlp Update</button>
                                <button class="btn-pill" onclick="clearAppCache()">Clear Cache</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- MODAL 1: VIDEO TRIMMER -->
    <div id="trimModal" class="modal-backdrop">
        <div class="modal-box">
            <div class="modal-header">
                <div class="modal-title" data-i18n="trim_title">Trim Video (Time Range)</div>
                <button class="close-btn" onclick="closeTrimModal()">×</button>
            </div>
            <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
                Download only a clip of the video quickly without downloading the entire stream.
            </div>
            <div style="display: flex; gap: 12px; margin-bottom: 20px;">
                <div style="flex: 1;">
                    <label style="font-size: 12px; font-weight: 700;" data-i18n="trim_start">Start Time (HH:MM:SS)</label>
                    <input id="trimStartInput" type="text" class="select-dark" style="width: 100%; margin-top: 6px;" placeholder="00:01:00">
                </div>
                <div style="flex: 1;">
                    <label style="font-size: 12px; font-weight: 700;" data-i18n="trim_end">End Time (HH:MM:SS)</label>
                    <input id="trimEndInput" type="text" class="select-dark" style="width: 100%; margin-top: 6px;" placeholder="00:02:30">
                </div>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 8px;">
                <button class="btn-pill" onclick="clearTrim()" data-i18n="trim_clear">Clear Trim</button>
                <button class="btn-pill success" onclick="applyTrim()" data-i18n="trim_apply">Apply Trim</button>
            </div>
        </div>
    </div>

    <!-- MODAL 2: BATCH PASTE -->
    <div id="batchModal" class="modal-backdrop">
        <div class="modal-box">
            <div class="modal-header">
                <div class="modal-title" data-i18n="batch_title">Batch Add Links</div>
                <button class="close-btn" onclick="closeBatchModal()">×</button>
            </div>
            <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;" data-i18n="batch_desc">
                Paste one link per line to queue multiple downloads:
            </div>
            <textarea id="batchTextarea" class="textarea-dark" placeholder="https://www.youtube.com/watch?v=...&#10;https://www.instagram.com/reel/...&#10;https://www.tiktok.com/@..."></textarea>
            <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px;">
                <button class="btn-pill" onclick="closeBatchModal()" data-i18n="btn_cancel">Cancel</button>
                <button class="btn-pill success" onclick="submitBatchAdd()" data-i18n="batch_add_all">Add All to Queue</button>
            </div>
        </div>
    </div>

    <!-- MODAL 3: WELCOME WALKTHROUGH -->
    <div id="welcomeModal" class="modal-backdrop">
        <div class="modal-box" style="text-align: center;">
            <div style="font-size: 40px; margin-bottom: 12px;">⚡</div>
            <div class="modal-title" style="font-size: 22px; margin-bottom: 8px;" data-i18n="welcome_title">Welcome to MediaPulse Pro</div>
            <div style="font-size: 14px; color: var(--text-muted); margin-bottom: 24px;" data-i18n="welcome_desc">
                Fast, modern, and private multimedia downloader for 1,800+ sites.
            </div>
            <div style="text-align: left; background: #0b1120; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 16px; margin-bottom: 24px; font-size: 13px; line-height: 1.8;">
                <div>✔️ <span data-i18n="welcome_feature1">4K, 1080p, Playlists, and MP3 320kbps audio</span></div>
                <div>✔️ <span data-i18n="welcome_feature2">Instagram Reels, TikTok, Twitter/X with browser session support</span></div>
                <div>✔️ <span data-i18n="welcome_feature3">Batch queue, video trimmer, SponsorBlock & multi-language</span></div>
            </div>
            <button class="btn-primary" style="width: 100%; justify-content: center;" onclick="dismissWelcomeModal()" data-i18n="btn_get_started">Get Started</button>
        </div>
    </div>

    <script>
        // Global Application State
        let currentTab = 'youtube';
        let currentLang = 'en';
        let translations = {};
        let activeTaskId = null;
        let activePollTimer = null;
        let lastDownloadedFilePath = null;
        let currentSelectedQuality = 'best';
        let currentSelectedFormat = 'mp4';
        let activeTrimStart = null;
        let activeTrimEnd = null;
        let currentAppConfig = {};
        let lastClipboardUrl = null;

        // Initialization
        window.addEventListener('DOMContentLoaded', () => {
            initApp();
            setupEventListeners();
            startClipboardPolling();
        });

        async function initApp() {
            try {
                const statusRes = await fetch('/api/status');
                const status = await statusRes.json();
                currentAppConfig = status.config || {};

                // Update badges
                updateFfmpegBadge(status.ffmpeg_available, status.ffmpeg_version);
                updateFolderPill(status.download_dir);

                // Language
                currentLang = status.language || 'en';
                document.getElementById('quickLangSelect').value = currentLang;
                document.getElementById('settingsLangSelect').value = currentLang;
                await loadAndApplyTranslations(currentLang);

                // Populate settings
                populateSettingsForm(currentAppConfig);

                // Load initial tab data
                loadHistory();
                pollQueue();

                // Check First-Run
                if (!currentAppConfig.first_run_completed) {
                    document.getElementById('welcomeModal').classList.add('show');
                }
            } catch (err) {
                console.error("Initialization error:", err);
            }
        }

        // --- i18n Translation Engine ---
        async function loadAndApplyTranslations(langCode) {
            try {
                const res = await fetch(`/api/locales/${langCode}`);
                translations = await res.json();
                currentLang = langCode;

                const isRtl = (langCode === 'ar');
                document.documentElement.setAttribute('dir', isRtl ? 'rtl' : 'ltr');
                document.documentElement.setAttribute('lang', langCode);

                // Translate all data-i18n elements
                document.querySelectorAll('[data-i18n]').forEach(el => {
                    const key = el.getAttribute('data-i18n');
                    if (translations[key]) {
                        el.innerText = translations[key];
                    }
                });

                // Translate placeholders
                document.querySelectorAll('[data-i18n-ph]').forEach(el => {
                    const key = el.getAttribute('data-i18n-ph');
                    if (translations[key]) {
                        el.placeholder = translations[key];
                    }
                });

                // Header title
                const headerMap = {
                    youtube: translations.nav_youtube || 'YouTube Pro',
                    web: translations.nav_web || 'Universal Web',
                    queue: translations.nav_queue || 'Batch Queue',
                    history: translations.nav_history || 'Library & History',
                    settings: translations.nav_settings || 'Settings'
                };
                document.getElementById('headerTitle').innerText = headerMap[currentTab] || 'MediaPulse Pro';
            } catch (err) {
                console.error("Failed to load translations:", err);
            }
        }

        async function changeLanguage(langCode) {
            await fetch('/api/settings/language', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ language: langCode })
            });
            document.getElementById('quickLangSelect').value = langCode;
            document.getElementById('settingsLangSelect').value = langCode;
            await loadAndApplyTranslations(langCode);
        }

        function t(key, fallback) {
            return translations[key] || fallback || key;
        }

        // --- Navigation ---
        function switchTab(tabId) {
            currentTab = tabId;
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

            const targetPane = document.getElementById(`pane-${tabId}`);
            if (targetPane) targetPane.classList.add('active');

            const navIndex = ['youtube', 'web', 'queue', 'history', 'settings'].indexOf(tabId);
            const navItems = document.querySelectorAll('.nav-item');
            if (navItems[navIndex]) navItems[navIndex].classList.add('active');

            const headerMap = {
                youtube: t('nav_youtube', 'YouTube Pro'),
                web: t('nav_web', 'Universal Web'),
                queue: t('nav_queue', 'Batch Queue'),
                history: t('nav_history', 'Library & History'),
                settings: t('nav_settings', 'Settings')
            };
            document.getElementById('headerTitle').innerText = headerMap[tabId] || 'MediaPulse Pro';

            if (tabId === 'history') loadHistory();
            if (tabId === 'queue') pollQueue();
        }

        // --- Keyboard Shortcuts & Drag/Drop ---
        function setupEventListeners() {
            // Drag and drop onto window
            let dragCounter = 0;
            window.addEventListener('dragenter', (e) => {
                e.preventDefault();
                dragCounter++;
                document.getElementById('dragOverlay').style.display = 'flex';
            });
            window.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dragCounter--;
                if (dragCounter <= 0) {
                    dragCounter = 0;
                    document.getElementById('dragOverlay').style.display = 'none';
                }
            });
            window.addEventListener('dragover', (e) => e.preventDefault());
            window.addEventListener('drop', (e) => {
                e.preventDefault();
                dragCounter = 0;
                document.getElementById('dragOverlay').style.display = 'none';
                const text = e.dataTransfer.getData('text');
                if (text && text.startsWith('http')) {
                    if (currentTab === 'web') {
                        document.getElementById('webUrlInput').value = text.trim();
                        scanWebSite();
                    } else {
                        switchTab('youtube');
                        document.getElementById('ytUrlInput').value = text.trim();
                        fetchYoutubePreview();
                    }
                }
            });

            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    closeTrimModal();
                    closeBatchModal();
                    dismissWelcomeModal();
                } else if (e.ctrlKey && e.key === ',') {
                    e.preventDefault();
                    switchTab('settings');
                } else if (e.ctrlKey && (e.key === 'f' || e.key === 'F')) {
                    e.preventDefault();
                    switchTab('history');
                    setTimeout(() => document.getElementById('historySearchInput').focus(), 100);
                }
            });
        }

        // --- Clipboard Watcher ---
        function startClipboardPolling() {
            setInterval(async () => {
                if (!currentAppConfig.clipboard_watcher) return;
                try {
                    const res = await fetch('/api/clipboard/check');
                    const data = await res.json();
                    if (data.has_video_url && data.url && data.url !== lastClipboardUrl) {
                        lastClipboardUrl = data.url;
                        showClipboardToast(data.url);
                    }
                } catch(e) {}
            }, 3000);
        }

        function showClipboardToast(url) {
            document.getElementById('clipboardUrlText').innerText = url;
            document.getElementById('clipboardToast').style.display = 'flex';
        }

        function dismissClipboardToast() {
            document.getElementById('clipboardToast').style.display = 'none';
        }

        function downloadClipboardUrl() {
            dismissClipboardToast();
            if (lastClipboardUrl) {
                switchTab('youtube');
                document.getElementById('ytUrlInput').value = lastClipboardUrl;
                fetchYoutubePreview();
            }
        }

        // --- Presets & Options ---
        function selectPreset(quality, format, elem) {
            document.querySelectorAll('.chip-group .chip').forEach(c => c.classList.remove('active'));
            if (elem) elem.classList.add('active');
            currentSelectedQuality = quality;
            currentSelectedFormat = format;
            document.getElementById('ytContainerSelect').value = format;
        }

        // --- YouTube Preview ---
        async function fetchYoutubePreview() {
            const url = document.getElementById('ytUrlInput').value.trim();
            if (!url) return;

            try {
                const res = await fetch('/api/youtube/info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                if (!res.ok) {
                    const err = await res.json();
                    alert(err.detail || "Could not retrieve preview.");
                    return;
                }
                const info = await res.json();
                document.getElementById('ytPreviewThumb').src = info.thumbnail || '';
                document.getElementById('ytPreviewTitle').innerText = info.title || 'Video';
                document.getElementById('ytPreviewMeta').innerText = `${info.uploader || 'Unknown'} • ${formatSeconds(info.duration)} • ${info.view_count ? info.view_count.toLocaleString() + ' views' : ''}`;
                document.getElementById('ytPreviewCard').style.display = 'block';
            } catch (err) {
                console.error("Preview error:", err);
            }
        }

        // --- Trimmer ---
        function openTrimModal() {
            document.getElementById('trimModal').classList.add('show');
        }
        function closeTrimModal() {
            document.getElementById('trimModal').classList.remove('show');
        }
        function applyTrim() {
            activeTrimStart = document.getElementById('trimStartInput').value.trim() || null;
            activeTrimEnd = document.getElementById('trimEndInput').value.trim() || null;
            if (activeTrimStart || activeTrimEnd) {
                document.getElementById('trimBadgeText').innerText = `✂️ Clip: ${activeTrimStart || '00:00:00'} - ${activeTrimEnd || 'End'}`;
                document.getElementById('trimBadgeIndicator').style.display = 'inline-flex';
            }
            closeTrimModal();
        }
        function clearTrim() {
            activeTrimStart = null;
            activeTrimEnd = null;
            document.getElementById('trimStartInput').value = '';
            document.getElementById('trimEndInput').value = '';
            document.getElementById('trimBadgeIndicator').style.display = 'none';
        }

        // --- Batch Add ---
        function openBatchModal() {
            document.getElementById('batchModal').classList.add('show');
        }
        function closeBatchModal() {
            document.getElementById('batchModal').classList.remove('show');
        }
        async function submitBatchAdd() {
            const text = document.getElementById('batchTextarea').value;
            const urls = text.split('\n').map(u => u.trim()).filter(u => u.length > 0);
            if (urls.length === 0) return;

            await fetch('/api/queue/batch-add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    urls: urls,
                    mode: currentSelectedFormat === 'mp3' ? 'audio' : 'video',
                    quality: currentSelectedQuality,
                    container: currentSelectedFormat
                })
            });

            closeBatchModal();
            document.getElementById('batchTextarea').value = '';
            switchTab('queue');
        }

        // --- Single Download Execution ---
        async function startSingleDownload(prefix) {
            const urlInput = document.getElementById(prefix === 'yt' ? 'ytUrlInput' : 'webUrlInput');
            const url = urlInput.value.trim();
            if (!url) return;

            const mode = (currentSelectedFormat === 'mp3' || currentSelectedFormat === 'm4a' || currentSelectedFormat === 'flac') ? 'audio' : 'video';
            const container = document.getElementById('ytContainerSelect').value;

            document.getElementById(`${prefix}ProgressCard`).style.display = 'block';
            document.getElementById(`${prefix}SuccessActions`).style.display = 'none';
            document.getElementById(`${prefix}ProgressFill`).style.width = '0%';
            document.getElementById(`${prefix}ProgressPercent`).innerText = '0.0%';

            try {
                const res = await fetch('/api/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: url,
                        mode: mode,
                        quality: currentSelectedQuality,
                        container: container,
                        trim_start: activeTrimStart,
                        trim_end: activeTrimEnd
                    })
                });

                const data = await res.json();
                activeTaskId = data.task_id;
                pollDownloadProgress(prefix, activeTaskId);
            } catch (err) {
                alert("Download failed to start: " + err);
            }
        }

        function pollDownloadProgress(prefix, taskId) {
            if (activePollTimer) clearInterval(activePollTimer);

            activePollTimer = setInterval(async () => {
                try {
                    const res = await fetch(`/api/download/status/${taskId}`);
                    const data = await res.json();

                    document.getElementById(`${prefix}ProgressTitle`).innerText = data.filename || 'Downloading media...';
                    document.getElementById(`${prefix}ProgressPercent`).innerText = `${(data.percent || 0).toFixed(1)}%`;
                    document.getElementById(`${prefix}ProgressFill`).style.width = `${Math.min(data.percent || 0, 100)}%`;
                    document.getElementById(`${prefix}ProgressSpeed`).innerText = data.speed || '--';
                    document.getElementById(`${prefix}ProgressSize`).innerText = data.size || '--';
                    document.getElementById(`${prefix}ProgressEta`).innerText = `ETA: ${data.eta || '--:--'}`;

                    if (data.status === 'completed') {
                        clearInterval(activePollTimer);
                        lastDownloadedFilePath = data.file_path;
                        document.getElementById(`${prefix}ProgressPercent`).innerText = '100% Completed';
                        document.getElementById(`${prefix}SuccessActions`).style.display = 'flex';
                        playCompletionSound();
                        loadHistory();
                    } else if (data.status === 'error' || data.status === 'cancelled') {
                        clearInterval(activePollTimer);
                        alert(data.status === 'cancelled' ? 'Download cancelled.' : 'Download failed.');
                    }
                } catch (e) {
                    clearInterval(activePollTimer);
                }
            }, 300);
        }

        async function cancelActiveDownload(prefix) {
            if (activeTaskId) {
                await fetch(`/api/download/cancel/${activeTaskId}`, { method: 'POST' });
            }
        }

        // --- Universal Web Sniffer ---
        async function scanWebSite() {
            const url = document.getElementById('webUrlInput').value.trim();
            if (!url) return;

            const container = document.getElementById('webStreamsContainer');
            container.innerHTML = '<div style="padding: 20px; color: #60a5fa;">🔍 Deep scanning page for media streams & metadata...</div>';

            try {
                const res = await fetch('/api/web/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                const data = await res.json();
                const streams = data.streams || [];

                if (streams.length === 0) {
                    container.innerHTML = `
                        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px;">
                            <div style="font-weight: 700; color: #f87171;">⚠️ No direct streams found</div>
                            <div style="font-size: 12px; color: #cbd5e1; margin-top: 6px;">${data.error_hint || "Site may require login cookies or unsupported stream format."}</div>
                        </div>
                    `;
                    return;
                }

                let html = '';
                streams.forEach(s => {
                    const cleanUrl = encodeURIComponent(s.url);
                    html += `
                        <div class="stream-item">
                            <div>
                                <span class="badge accent">${s.format}</span>
                                <span class="badge">${s.quality || 'Best'}</span>
                                <div style="font-size: 13px; font-weight: 700; margin-top: 6px;">${s.label || 'Video Stream'}</div>
                            </div>
                            <button class="btn-pill success" onclick="downloadWebStream(decodeURIComponent('${cleanUrl}'))">Download</button>
                        </div>
                    `;
                });
                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = `<div style="color: #f87171;">Scan error: ${err}</div>`;
            }
        }

        function downloadWebStream(streamUrl) {
            switchTab('youtube');
            document.getElementById('ytUrlInput').value = streamUrl;
            startSingleDownload('yt');
        }

        // --- Queue Management ---
        async function pollQueue() {
            try {
                const res = await fetch('/api/queue');
                const data = await res.json();
                const tasks = data.tasks || [];
                const container = document.getElementById('queueListContainer');
                const badge = document.getElementById('queueCountBadge');

                const queuedCount = tasks.filter(t => t.state === 'queued' || t.state === 'downloading').length;
                if (queuedCount > 0) {
                    badge.innerText = queuedCount;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }

                if (tasks.length === 0) {
                    container.innerHTML = `<div style="color: gray; padding: 20px 0;">${t('queue_empty', 'Queue is empty.')}</div>`;
                    return;
                }

                let html = '';
                tasks.forEach((t, idx) => {
                    html += `
                        <div class="stream-item" id="task-${t.id}">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="display: flex; flex-direction: column; gap: 2px;">
                                    <button class="btn-pill" style="padding: 2px 6px; font-size: 9px;" onclick="moveTask('${t.id}', -1)">▲</button>
                                    <button class="btn-pill" style="padding: 2px 6px; font-size: 9px;" onclick="moveTask('${t.id}', 1)">▼</button>
                                </div>
                                <div>
                                    <span class="badge ${t.state === 'completed' ? 'accent' : ''}">${t.state.toUpperCase()}</span>
                                    <div style="font-weight: 700; font-size: 13px; margin-top: 4px;">${t.title}</div>
                                    <div style="font-size: 11px; color: var(--text-muted);">${t.size} • ${t.speed}</div>
                                </div>
                            </div>
                            <div style="display: flex; gap: 6px;">
                                ${t.state === 'paused' ? `<button class="btn-pill" onclick="resumeQueueTask('${t.id}')">▶ Resume</button>` : ''}
                                ${t.state === 'downloading' ? `<button class="btn-pill" onclick="pauseQueueTask('${t.id}')">⏸ Pause</button>` : ''}
                                <button class="btn-pill danger" onclick="removeQueueTask('${t.id}')">×</button>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            } catch(e) {}
        }

        async function addCurrentToQueue() {
            const url = document.getElementById('ytUrlInput').value.trim();
            if (!url) return;
            await fetch('/api/queue/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url,
                    mode: currentSelectedFormat === 'mp3' ? 'audio' : 'video',
                    quality: currentSelectedQuality,
                    container: currentSelectedFormat,
                    trim_start: activeTrimStart,
                    trim_end: activeTrimEnd
                })
            });
            switchTab('queue');
        }

        async function pauseQueueTask(id) { await fetch(`/api/queue/pause/${id}`, { method: 'POST' }); pollQueue(); }
        async function resumeQueueTask(id) { await fetch(`/api/queue/resume/${id}`, { method: 'POST' }); pollQueue(); }
        async function removeQueueTask(id) { await fetch(`/api/queue/remove/${id}`, { method: 'POST' }); pollQueue(); }
        async function clearCompletedQueue() { await fetch('/api/queue/clear', { method: 'POST' }); pollQueue(); }

        async function moveTask(id, dir) {
            const res = await fetch('/api/queue');
            const data = await res.json();
            const tasks = (data.tasks || []).map(t => t.id);
            const idx = tasks.indexOf(id);
            if (idx === -1) return;
            const newIdx = idx + dir;
            if (newIdx < 0 || newIdx >= tasks.length) return;
            tasks.splice(idx, 1);
            tasks.splice(newIdx, 0, id);
            await fetch('/api/queue/reorder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order: tasks })
            });
            pollQueue();
        }

        // --- Library & History ---
        let rawHistoryList = [];
        async function loadHistory() {
            try {
                const res = await fetch('/api/history');
                const data = await res.json();
                rawHistoryList = data.history || [];
                renderHistoryItems(rawHistoryList);
            } catch (err) {}
        }

        function filterHistory(query) {
            if (!query) {
                renderHistoryItems(rawHistoryList);
                return;
            }
            const q = query.toLowerCase();
            const filtered = rawHistoryList.filter(item => (item.title || '').toLowerCase().includes(q) || (item.url || '').toLowerCase().includes(q));
            renderHistoryItems(filtered);
        }

        function renderHistoryItems(list) {
            const container = document.getElementById('historyListContainer');
            if (list.length === 0) {
                container.innerHTML = `<div style="color: gray; padding: 20px 0;">${t('history_empty', 'No downloads yet.')}</div>`;
                return;
            }
            let html = '';
            list.forEach(item => {
                const pathEsc = encodeURIComponent(item.file_path || '');
                html += `
                    <div class="stream-item">
                        <div style="flex: 1; padding-right: 12px;">
                            <span class="badge ${item.source === 'YouTube' ? 'accent' : ''}">${item.source || 'Web'}</span>
                            <div style="font-weight: 700; margin-top: 4px;">${item.title}</div>
                            <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">${item.format || ''} • ${item.file_size || ''} • ${item.timestamp || ''}</div>
                        </div>
                        <div style="display: flex; gap: 6px;">
                            <button class="btn-pill success" onclick="playFile(decodeURIComponent('${pathEsc}'))">▶ Play</button>
                            <button class="btn-pill" onclick="openFileFolder(decodeURIComponent('${pathEsc}'))">📂 Folder</button>
                            <button class="btn-pill" onclick="redownloadUrl('${item.url}')">🔄</button>
                            <button class="btn-pill danger" onclick="deleteHistoryItem('${item.id}')">×</button>
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        async function deleteHistoryItem(id) {
            await fetch('/api/history/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            loadHistory();
        }

        async function clearAllHistory() {
            if (confirm("Clear all download history?")) {
                await fetch('/api/history/clear', { method: 'POST' });
                loadHistory();
            }
        }

        function redownloadUrl(url) {
            switchTab('youtube');
            document.getElementById('ytUrlInput').value = url;
            fetchYoutubePreview();
        }

        // --- Settings Management ---
        function populateSettingsForm(cfg) {
            if (cfg.download_dir) document.getElementById('settingsFolderDisplay').innerText = cfg.download_dir;
            if (cfg.filename_template) document.getElementById('settingsFilenameTemplate').value = cfg.filename_template;
            if (cfg.speed_limit) document.getElementById('settingsSpeedLimit').value = cfg.speed_limit;
            if (cfg.browser_cookies) document.getElementById('settingsCookieSelect').value = cfg.browser_cookies;
            if (cfg.proxy) document.getElementById('settingsProxy').value = cfg.proxy;
            document.getElementById('toggleSubs').checked = !!cfg.subtitles_embed;
            document.getElementById('toggleMetadata').checked = cfg.embed_metadata !== false;
            document.getElementById('toggleSponsor').checked = !!cfg.sponsorblock;
            document.getElementById('toggleClipboard').checked = cfg.clipboard_watcher !== false;
            document.getElementById('toggleSound').checked = cfg.sound !== false;
        }

        async function saveSetting(key, val) {
            currentAppConfig[key] = val;
            await fetch('/api/settings/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ settings: { [key]: val } })
            });
        }

        async function chooseDownloadFolder() {
            const res = await fetch('/api/choose-folder', { method: 'POST' });
            const data = await res.json();
            if (data.success && data.folder) {
                document.getElementById('settingsFolderDisplay').innerText = data.folder;
                updateFolderPill(data.folder);
            }
        }

        async function downloadFfmpegOnDemand() {
            const btn = document.getElementById('btnDownloadFfmpeg');
            btn.disabled = true;
            document.getElementById('ffmpegDownloadProgress').style.display = 'block';

            await fetch('/api/ffmpeg/download', { method: 'POST' });

            const timer = setInterval(async () => {
                const res = await fetch('/api/ffmpeg/download-status');
                const st = await res.json();
                document.getElementById('ffmpegProgressFill').style.width = `${st.percent || 0}%`;
                document.getElementById('ffmpegDownloadMsg').innerText = st.message || 'Downloading...';

                if (st.status === 'completed' || st.status === 'error') {
                    clearInterval(timer);
                    btn.disabled = false;
                    const statusRes = await fetch('/api/status');
                    const status = await statusRes.json();
                    updateFfmpegBadge(status.ffmpeg_available, status.ffmpeg_version);
                }
            }, 500);
        }

        async function clearAppCache() {
            const res = await fetch('/api/settings/clear-cache', { method: 'POST' });
            const data = await res.json();
            alert(`Cache cleared! ${data.cleaned || 0} temporary files removed.`);
        }

        async function checkYtdlpUpdate() {
            const res = await fetch('/api/update/check', { method: 'POST' });
            const data = await res.json();
            if (data.has_update) {
                if (confirm(`New yt-dlp version ${data.latest_version} available (current: ${data.current_version}). Update now?`)) {
                    await fetch('/api/update/perform', { method: 'POST' });
                    alert("Updated successfully!");
                }
            } else {
                alert(`yt-dlp is up to date (v${data.current_version}).`);
            }
        }

        // --- Onboarding ---
        function dismissWelcomeModal() {
            document.getElementById('welcomeModal').classList.remove('show');
            saveSetting('first_run_completed', true);
        }

        // --- Helpers ---
        function updateFfmpegBadge(available, version) {
            const badge = document.getElementById('ffmpegBadge');
            const details = document.getElementById('ffmpegStatusDetails');
            if (available) {
                badge.className = 'badge accent';
                badge.innerText = '✔️ FFmpeg Ready';
                details.innerText = `Active: ${version || 'FFmpeg 7.1'}`;
                document.getElementById('btnDownloadFfmpeg').style.display = 'none';
            } else {
                badge.className = 'badge';
                badge.innerText = '❌ FFmpeg Missing';
                details.innerText = 'FFmpeg not detected. Click below to install automatically:';
                document.getElementById('btnDownloadFfmpeg').style.display = 'inline-block';
            }
        }

        function updateFolderPill(folder) {
            document.getElementById('folderPill').innerText = `📁 ${folder ? folder.split(/[\\/]/).pop() : 'Downloads'}`;
        }

        function playFile(path) {
            if (path) fetch('/api/play-file', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) });
        }

        function playLastFile() {
            if (lastDownloadedFilePath) playFile(lastDownloadedFilePath);
        }

        function openFileFolder(path) {
            if (path) fetch('/api/open-folder', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: path.substring(0, path.lastIndexOf('\\')) }) });
        }

        function openDownloadFolder() {
            fetch('/api/open-folder', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
        }

        function formatSeconds(sec) {
            if (!sec) return '--:--';
            const m = Math.floor(sec / 60);
            const s = Math.floor(sec % 60);
            return `${m}:${s < 10 ? '0' : ''}${s}`;
        }

        function playCompletionSound() {
            if (!currentAppConfig.sound) return;
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(587.33, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15);
                gain.gain.setValueAtTime(0.12, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.35);
            } catch(e) {}
        }
    </script>
</body>
</html>
'''

def main():
    target_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "static", "modern.html")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT.strip())
    print(f"[OK] Successfully built modern.html at: {target_path}")

if __name__ == "__main__":
    main()
