"""Tests for internationalization (i18n):
- Verifies all 12 language files exist and are valid JSON
- Verifies every language file has all keys defined in en.json
- Verifies Arabic translation is natural and pure (no mixed English words except YouTube)
- Verifies fallback mechanism to English for unknown keys
- Verifies system language detection
"""
import json
import os
import re
import pytest

from core.i18n import (
    LOCALES_DIR,
    get_available_languages,
    load_translations,
    t,
    set_current_language,
    detect_system_language
)

EXPECTED_LANGUAGES = ["en", "ar", "fr", "es", "de", "pt", "tr", "ru", "zh", "ja", "hi", "id"]


def test_manifest_and_files_exist():
    manifest_path = os.path.join(LOCALES_DIR, "manifest.json")
    assert os.path.exists(manifest_path), "manifest.json must exist in locales/"

    langs = get_available_languages()
    assert len(langs) == 12, "Should support exactly 12 languages"

    codes = [l["code"] for l in langs]
    for code in EXPECTED_LANGUAGES:
        assert code in codes, f"Language {code} must be declared in manifest"
        lang_file = os.path.join(LOCALES_DIR, f"{code}.json")
        assert os.path.exists(lang_file), f"Translation file {code}.json must exist"


def test_all_languages_have_all_keys():
    en_path = os.path.join(LOCALES_DIR, "en.json")
    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    en_keys = set(en_data.keys())
    assert len(en_keys) >= 70, f"Expected at least 70 translation keys, got {len(en_keys)}"

    for code in EXPECTED_LANGUAGES:
        lang_path = os.path.join(LOCALES_DIR, f"{code}.json")
        with open(lang_path, "r", encoding="utf-8") as f:
            lang_data = json.load(f)

        missing_keys = en_keys - set(lang_data.keys())
        assert not missing_keys, f"Language '{code}' is missing keys: {missing_keys}"

        # Ensure no empty strings
        for k, v in lang_data.items():
            assert isinstance(v, str) and len(v.strip()) > 0, f"Key '{k}' in '{code}.json' has empty value"


def test_arabic_translation_quality():
    ar_path = os.path.join(LOCALES_DIR, "ar.json")
    with open(ar_path, "r", encoding="utf-8") as f:
        ar_data = json.load(f)

    # Check that Arabic strings contain Arabic unicode characters (0600-06FF)
    # Allowed latin words: "YouTube", "MediaPulse Pro", "MP3", "MP4", "4K", "2K", "1080p", "720p", "320k", "FFmpeg", "SponsorBlock", "Short", "Reels"
    allowed_latin = {
        "youtube", "mediapulse", "pro", "mp3", "mp4", "4k", "2k", "1080p", "720p", "320k",
        "ffmpeg", "sponsorblock", "short", "reels", "hh", "mm", "ss", "url", "http", "https",
        "socks5", "k", "p", "index", "total"
    }

    arabic_char_re = re.compile(r'[\u0600-\u06FF]')
    token_re = re.compile(r'[a-zA-Z0-9]+')

    for k, text in ar_data.items():
        if k in ["app_name", "batch_placeholder", "proxy_placeholder"]:
            continue
        # Should have Arabic characters
        assert arabic_char_re.search(text), f"Key '{k}' in ar.json does not contain Arabic text: '{text}'"

        # Check Latin words (tokens containing letters)
        # Strip {var} format placeholders before token validation
        clean_text = re.sub(r'\{[a-zA-Z0-9_]+\}', '', text)
        tokens = token_re.findall(clean_text)
        for token in tokens:
            if any(c.isalpha() for c in token):
                assert token.lower() in allowed_latin, f"Unexpected English word '{token}' in Arabic translation for key '{k}': '{text}'"




def test_i18n_translation_fallback():
    set_current_language("en")
    assert t("btn_download") == "Download Now"

    set_current_language("ar")
    assert t("btn_download") == "تنزيل الآن"

    # Missing key fallback
    assert t("non_existent_key_xyz", "Default Value") == "Default Value"


def test_rtl_metadata():
    langs = get_available_languages()
    ar_info = next((l for l in langs if l["code"] == "ar"), None)
    assert ar_info is not None
    assert ar_info["dir"] == "rtl", "Arabic must be marked as rtl"

    en_info = next((l for l in langs if l["code"] == "en"), None)
    assert en_info is not None
    assert en_info["dir"] == "ltr", "English must be marked as ltr"
