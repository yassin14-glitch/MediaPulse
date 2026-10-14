# Contributing to MediaPulse Pro

Thank you for your interest in contributing to **MediaPulse Pro**! We welcome community contributions, bug fixes, feature proposals, and translations.

---

## 🛠️ Development Setup

### 1. Prerequisites
- **Python 3.10+** (64-bit recommended)
- **Windows 10 / 11** (or Windows with Microsoft Edge WebView2 Runtime installed)
- **Git**

### 2. Clone and Setup Environment
```powershell
# Clone the repository
git clone https://github.com/your-username/mediapulse-pro.git
cd mediapulse-pro

# Create a clean virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1

# Install core dependencies
pip install -r requirements.txt
pip install pytest httpx pyinstaller
```

---

## 🧪 Running Tests

Before submitting any code changes, always run the automated test suite:

```powershell
# Run the fast unit test suite (recommended)
pytest tests -m "not slow" -v

# Run the complete test suite (including live network tests)
pytest tests -v
```

---

## 🌐 Adding or Updating a Language

Adding a new language to MediaPulse Pro requires creating just **one single JSON file**:

1. Open `locales/en.json` as a reference.
2. Copy `en.json` to `locales/<lang_code>.json` (for example, `locales/it.json` for Italian or `locales/nl.json` for Dutch).
3. Translate the string values. Do not change the JSON keys.
4. Add the language metadata entry to `locales/manifest.json`:
   ```json
   {
     "code": "it",
     "name": "Italian",
     "native": "Italiano",
     "dir": "ltr"
   }
   ```
5. Run the i18n verification test to ensure all keys match:
   ```powershell
   pytest tests/test_i18n.py -v
   ```

---

## 📦 Building the Windows Release

To compile the standalone desktop distribution:

```powershell
# Build standalone onedir package
.\build.bat
```
The compiled output is located at:
```
dist\MediaPulsePro\MediaPulsePro.exe
```

---

## ⚖️ Code of Conduct & Guidelines

- **No DRM Circumvention**: MediaPulse Pro is strictly intended for downloading authorized, public domain, or personal media. PRs implementing DRM circumvention or decryption algorithms will be rejected.
- **Maintain Clean Code**: Ensure type hints and docstrings are maintained.
- **Test Before Committing**: Every PR must pass all existing pytest suites.
