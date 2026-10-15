<div align="center">

# Steam Account Creator

[![python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![platform](https://img.shields.io/badge/platform-Windows%20x64-0078D6?logo=windows&logoColor=white)](https://github.com/)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![status](https://img.shields.io/badge/status-active-success)](https://github.com/)

A lightweight, automated Windows CLI tool for rapid Steam account creation: local AI captcha auto-solving, disposable mailbox verification, silent background execution, and one-click Steam Guard code retrieval.

No paid captcha keys, no telemetry, nothing leaves your machine.

</div>

---

## Features

### Registration
- Automated account generation through Steam's official signup flow (`store.steampowered.com/join/`).
- Real-time Steam username availability checks: automatically generates and tests alternative clean usernames until Steam formally verifies acceptance.
- Secure, compliant password generator with Steam password policy validation.
- Batch creation support: specify how many accounts to generate in a single run.

### Captcha Engine
- Integrated **hektCaptcha** solver extension: solves hCaptcha challenges locally using ONNX / computer vision models.
- **Zero cost**: No 2Captcha, Anti-Captcha, or Capsolver API subscriptions required.
- Human-like interaction timing and automated checkbox triggering.

### Email & Steam Guard
- Disposable mailbox integration via `best-temp-mail.com` API: bypasses Steam's disposable email blacklist.
- Automatic polling and confirmation of Steam email verification tokens.
- **Steam Guard Code Retriever (`get_code.bat` / `get_code.py`)**:
  - Automatically fetches the 5-character Steam Guard login code on demand.
  - Copies the code directly to your Windows clipboard (`Ctrl + V`).

### Stealth & Background
- Runs silently in background mode via off-screen window positioning and auto-minimization.
- Prevents anti-bot headless detection while keeping full GPU hardware acceleration and extension execution intact.
- Preserves clean desktop workspace with zero browser pop-up interference.

### Storage & Security
- Saves generated accounts in clean, formatted blocks in `steam_account.txt`.
- Built-in `.gitignore` protection ensures private account credentials and mailbox tokens are never pushed to public repositories.

---

## Quick Start

### 1. Prerequisites
- **Windows 10 / 11 (64-bit)**
- **Google Chrome** installed
- **Python 3.10+** (ensure "Add Python to PATH" is checked during installation)

### 2. Setup
Clone this repository and install dependencies:
```bash
git clone https://github.com/YOUR_USERNAME/steam-account-creator.git
cd steam-account-creator
pip install -r requirements.txt
```

### 3. Usage

#### Run the Account Creator
Double-click `run.bat` or run:
```bash
python steam_creator.py
```
Options:
- `-c, --count <N>`: Number of accounts to create (e.g., `-c 5`)
- `--proxy <URL>`: Optional HTTP/HTTPS/SOCKS proxy
- `--visible`: Display Chrome browser window (default runs silently in background)

#### Fetch Steam Guard Code
When logging into the Steam Desktop Client for the first time:
Double-click `get_code.bat` or run:
```bash
python get_code.py
```
Select your account, and the 5-character Steam Guard verification code will be retrieved and auto-copied to your clipboard.

---

## Repository Structure

```text
├── steam_creator.py     # Main CLI automation engine
├── get_code.py          # Steam Guard code fetcher & clipboard copier
├── run.bat              # 1-click batch launcher for account creator
├── get_code.bat         # 1-click batch launcher for Steam Guard codes
├── requirements.txt     # Python dependencies
├── .gitignore           # Keeps generated credentials private
├── README.md            # Documentation
└── extensions/
    └── hektcaptcha/     # Local AI-driven hCaptcha solver
```

---

## Disclaimer
This project is for educational and testing purposes only. Please use responsibly and adhere to Steam's Subscriber Agreement and Terms of Service.
