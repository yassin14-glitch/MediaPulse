"""Internationalization (i18n) engine for MediaPulse Pro.
Supports 12 languages with automatic fallback to English, system locale detection,
and RTL support metadata.
"""
import json
import locale
import os
import sys
from typing import Any, Dict, List, Optional

LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locales")
if getattr(sys, "frozen", False):
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass and os.path.isdir(os.path.join(meipass, "locales")):
        LOCALES_DIR = os.path.join(meipass, "locales")
    else:
        exe_dir = os.path.dirname(sys.executable)
        for cand in [os.path.join(exe_dir, "_internal", "locales"), os.path.join(exe_dir, "locales")]:
            if os.path.isdir(cand):
                LOCALES_DIR = cand
                break

_cache: Dict[str, Dict[str, str]] = {}
_current_lang: str = "en"
_fallback_lang: str = "en"


def get_available_languages() -> List[Dict[str, str]]:
    """Returns list of supported languages from manifest.json."""
    manifest_path = os.path.join(LOCALES_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [
        {"code": "en", "name": "English", "native": "English", "dir": "ltr"},
        {"code": "ar", "name": "Arabic", "native": "العربية", "dir": "rtl"}
    ]


def detect_system_language() -> str:
    """Detects system language code (e.g. 'en', 'ar', 'fr', 'zh')."""
    try:
        loc = None
        try:
            loc = locale.getlocale()[0]
        except Exception:
            pass
        if not loc:
            try:
                import ctypes
                windll = getattr(ctypes, 'windll', None)
                if windll:
                    import locale
                    lang_id = windll.kernel32.GetUserDefaultUILanguage()
                    loc = locale.windows_locale.get(lang_id)
            except Exception:
                pass
        if loc:
            code = loc.split("_")[0].lower()
            available_codes = [lang["code"] for lang in get_available_languages()]
            if code in available_codes:
                return code
    except Exception:
        pass
    return "en"


def load_translations(lang_code: str) -> Dict[str, str]:
    """Loads translations dictionary for a given language code with English fallback."""
    global _cache
    if lang_code in _cache:
        return _cache[lang_code]

    # Load English fallback first
    if "en" not in _cache:
        en_path = os.path.join(LOCALES_DIR, "en.json")
        if os.path.exists(en_path):
            with open(en_path, "r", encoding="utf-8") as f:
                _cache["en"] = json.load(f)
        else:
            _cache["en"] = {}

    target_path = os.path.join(LOCALES_DIR, f"{lang_code}.json")
    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge with English fallback for any missing key
                merged = dict(_cache.get("en", {}))
                merged.update(loaded)
                _cache[lang_code] = merged
                return merged
        except Exception:
            pass

    return _cache.get("en", {})


def set_current_language(lang_code: str):
    """Sets active language."""
    global _current_lang
    available_codes = [lang["code"] for lang in get_available_languages()]
    if lang_code in available_codes:
        _current_lang = lang_code
    elif lang_code == "auto":
        _current_lang = detect_system_language()


def get_current_language() -> str:
    return _current_lang


def t(key: str, default: Optional[str] = None) -> str:
    """Translates a key into current language."""
    trans = load_translations(_current_lang)
    return trans.get(key, default or key)
