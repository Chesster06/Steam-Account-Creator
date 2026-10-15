#!/usr/bin/env python3
"""
Steam Account Creator CLI
=========================
Features:
- Best-Temp-Mail.com API integration (avoid Steam disposable blacklist)
- Interactive Chrome Profile selector (Default, Profile 1, Profile 2, etc.)
- Auto-solve via installed Chrome extension (hektCaptcha, Buster, etc.)
- Auto email verification & account finalization
"""

import os
import sys
import time
import re
import random
import string
import uuid
import argparse
import json
from datetime import datetime

try:
    import requests
except ImportError:
    sys.exit("[!] Missing 'requests' library. Run: pip install requests")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    sys.exit("[!] Missing 'selenium' or 'webdriver_manager'. Run: pip install selenium webdriver-manager")

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    MAGENTA = Fore.MAGENTA
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT
except ImportError:
    CYAN = GREEN = YELLOW = RED = MAGENTA = RESET = BOLD = ""

STEAM_JOIN_URL = "https://store.steampowered.com/join/"
CHROME_USER_DATA_DIR = r"C:\Users\Administrator\AppData\Local\Google\Chrome\User Data"


def get_available_profiles():
    """Lists available Chrome profile directories with human-friendly names & emails."""
    profiles = []
    local_state_path = os.path.join(CHROME_USER_DATA_DIR, "Local State")
    info_cache = {}
    if os.path.exists(local_state_path):
        try:
            import json
            data = json.load(open(local_state_path, encoding="utf-8"))
            info_cache = data.get("profile", {}).get("info_cache", {})
        except Exception:
            pass

    if os.path.exists(CHROME_USER_DATA_DIR):
        for entry in os.listdir(CHROME_USER_DATA_DIR):
            full = os.path.join(CHROME_USER_DATA_DIR, entry)
            if os.path.isdir(full) and (entry == "Default" or entry.startswith("Profile ")):
                meta = info_cache.get(entry, {})
                display_name = meta.get("name", entry)
                email = meta.get("user_name", "")
                label = f"{entry} ({display_name}{' - ' + email if email else ''})"

                # Check if it has hektCaptcha
                ext_dir = os.path.join(full, "Extensions")
                has_solver = False
                if os.path.exists(ext_dir) and "bpfdbfnkjelhloljelooneehdalcmljb" in os.listdir(ext_dir):
                    has_solver = True
                    label += " [hektCaptcha Installed]"

                profiles.append({"dir": entry, "label": label, "has_solver": has_solver})

    def sort_key(item):
        name = item["dir"]
        if name == "Default":
            return (0, 0)
        match = re.search(r"Profile\s+(\d+)", name)
        return (1, int(match.group(1))) if match else (2, name)

    return sorted(profiles, key=sort_key)


def print_banner():
    banner = f"""
{CYAN}{BOLD}=============================================================
                    STEAM ACCOUNT CREATOR
============================================================={RESET}
"""
    print(banner)


class BestTempMailClient:
    """Disposable mailbox provider via best-temp-mail.com API."""

    API_BASE = "https://best-temp-mail.com/api/v3"

    def __init__(self, proxies=None):
        self.session = requests.Session()
        if proxies:
            self.session.proxies.update(proxies)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Referer": "https://best-temp-mail.com/",
            "Origin": "https://best-temp-mail.com",
        })
        self.int_token = str(uuid.uuid4())
        self.email_address = None
        self.email_id = None
        self.update_tag = None

    def create_mailbox(self):
        try:
            r = self.session.post(
                f"{self.API_BASE}/createEmail",
                json={"intToken": self.int_token},
                timeout=15,
            )
            r.raise_for_status()
            res = r.json()
            if res.get("status") == "success":
                data = res.get("data", {})
                self.email_address = data.get("address")
                self.email_id = data.get("id")
                self.update_tag = data.get("update_tag")
                return True, self.email_address
            return False, f"API error: {res}"
        except Exception as e:
            return False, str(e)

    def wait_for_verification_link(self, timeout_s=120, poll_interval_s=5):
        deadline = time.time() + timeout_s

        while time.time() < deadline:
            try:
                payload = {
                    "address": self.email_address,
                    "id": self.email_id,
                    "intToken": self.int_token,
                    "update_tag": self.update_tag,
                }
                r = self.session.post(f"{self.API_BASE}/getEmailList", json=payload, timeout=15)
                if r.status_code == 200:
                    data = r.json().get("data", {})
                    if data.get("hasNewEmail"):
                        self.update_tag = data.get("update_tag")
                        for email_item in data.get("emailList", []):
                            content = (email_item.get("html") or "") + "\n" + (email_item.get("text") or "")
                            match = re.search(r"https?://store\.steampowered\.com/account/newaccountverification[^\s\"'<>]+", content)
                            if match:
                                return match.group(0)
            except Exception:
                pass
            time.sleep(poll_interval_s)
        return None


def generate_username():
    """Generates simple, human-readable usernames (e.g. alexgamer88, samplay21)."""
    prefixes = ["alex", "adam", "ryan", "kevin", "sam", "dani", "leo", "zack", "max", "felix", "harris", "harith"]
    tags = ["gamer", "play", "pro", "boy", "zone", "king", "rush", "prime", "hero", "craft"]
    num = random.randint(10, 999)
    return f"{random.choice(prefixes)}{random.choice(tags)}{num}"


def generate_password():
    """Generates simple, easy-to-remember passwords (e.g. SteamPass888!, GamerPass123!)."""
    bases = ["SteamPass", "GamerPass", "PlaySteam", "SuperPass", "PrimePass", "CyberPass"]
    num = random.randint(100, 999)
    return f"{random.choice(bases)}{num}!"


def is_chrome_running():
    """Checks if Google Chrome process is currently active."""
    try:
        import subprocess
        output = subprocess.check_output('tasklist /FI "IMAGENAME eq chrome.exe"', shell=True, text=True, stderr=subprocess.DEVNULL)
        return "chrome.exe" in output.lower()
    except Exception:
        return False


def get_solver_extension_path():
    """Finds the path to hektCaptcha extension (Bundled local first, then system)."""
    # 1. Check local bundled folder (Plug & Play for any computer)
    local_ext = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extensions", "hektcaptcha")
    if os.path.exists(local_ext):
        return local_ext

    # 2. Fallback to system Chrome User Data
    default_hekt = os.path.join(CHROME_USER_DATA_DIR, "Default", "Extensions", "bpfdbfnkjelhloljelooneehdalcmljb")
    if os.path.exists(default_hekt):
        vers = [os.path.join(default_hekt, v) for v in os.listdir(default_hekt) if os.path.isdir(os.path.join(default_hekt, v))]
        if vers:
            return vers[-1]
    return None


def reset_chrome_crash_state(profile_name: str):
    """Resets Chrome's exit_type to Normal so the 'Restore pages?' bubble never appears."""
    pref_path = os.path.join(CHROME_USER_DATA_DIR, profile_name, "Preferences")
    if os.path.exists(pref_path):
        try:
            with open(pref_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = re.sub(r'"exit_type"\s*:\s*"[^"]+"', '"exit_type":"Normal"', content)
            content = re.sub(r'"exited_cleanly"\s*:\s*false', '"exited_cleanly":true', content)
            with open(pref_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass


def build_driver(headless: bool = True, proxy: str = None):
    options = Options()
    options.page_load_strategy = "eager"

    # Load hektCaptcha solver extension cleanly from user's installed extensions
    solver_ext = get_solver_extension_path()
    if solver_ext:
        options.add_argument(f"--load-extension={solver_ext}")

    if headless:
        # Off-screen positioning: completely invisible to user, but retains full GPU & extension solver capability
        options.add_argument("--window-position=-3000,-3000")

    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,850")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install(), log_output=os.devnull)
    driver = webdriver.Chrome(service=service, options=options)
    if headless:
        try:
            driver.minimize_window()
        except Exception:
            pass
    driver.set_page_load_timeout(35)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def save_mailbox_token(username: str, email: str, email_id: str, int_token: str, update_tag: str):
    """Saves mailbox auth tokens for later Steam Guard verification retrieval."""
    mb_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mailboxes.json")
    data = {}
    if os.path.exists(mb_file) and os.path.getsize(mb_file) > 0:
        try:
            with open(mb_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[username] = {
        "email": email,
        "email_id": email_id,
        "int_token": int_token,
        "update_tag": update_tag,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        with open(mb_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f" {RED}[!] Failed to save mailbox token: {e}{RESET}")


def create_one_account(index: int, total: int, headless: bool = True, proxy: str = None):
    print(f"\n{CYAN}{BOLD}[{index}/{total}] Starting Steam Registration Cycle...{RESET}")
    driver = None
    try:
        # Step 1: Create mailbox via best-temp-mail.com
        print(f" {YELLOW}[*]{RESET} Requesting temporary email from best-temp-mail.com...")
        mail = BestTempMailClient()
        ok, email = mail.create_mailbox()
        if not ok:
            print(f" {RED}[x]{RESET} Could not generate mailbox: {email}")
            return None
        print(f" {GREEN}[+]{RESET} Assigned email: {BOLD}{email}{RESET}")

        # Step 2: Open Steam Join Page in Chrome with hektCaptcha solver (Silent background)
        mode_desc = "Silent Background (Headless)" if headless else "Visible Chrome"
        print(f" {YELLOW}[*]{RESET} Launching Steam session in {BOLD}{mode_desc}{RESET}...")
        driver = build_driver(headless=headless, proxy=proxy)
        
        print(f" {YELLOW}[*]{RESET} Navigating to Steam signup page...")
        driver.get(STEAM_JOIN_URL)

        wait = WebDriverWait(driver, 20)
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        reenter_input = driver.find_element(By.ID, "reenter_email")

        # Step 3: Populate Form
        print(f" {YELLOW}[*]{RESET} Filling email and agreement fields...")
        email_input.clear()
        email_input.send_keys(email)
        reenter_input.clear()
        reenter_input.send_keys(email)

        # Tick agreement checkbox
        agree_checkbox = driver.find_element(By.ID, "i_agree_check")
        if not agree_checkbox.is_selected():
            driver.execute_script("arguments[0].click();", agree_checkbox)

        # Trigger hCaptcha checkbox click so hektCaptcha can start solving
        print(f" {YELLOW}[*]{RESET} Triggering hCaptcha checkbox click...")
        time.sleep(2)
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for frame in iframes:
                src = frame.get_attribute("src") or ""
                if "hcaptcha.com" in src:
                    driver.switch_to.frame(frame)
                    try:
                        chk = driver.find_element(By.ID, "checkbox")
                        chk.click()
                        print(f" {GREEN}[+]{RESET} Clicked hCaptcha checkbox! hektCaptcha is now solving...")
                    except Exception:
                        pass
                    driver.switch_to.default_content()
                    break
        except Exception:
            try:
                driver.switch_to.default_content()
            except Exception:
                pass

        # Step 4: Wait for Captcha to be solved by extension or user
        print(f" {YELLOW}[*]{RESET} Waiting for hCaptcha resolution (hektCaptcha)...")
        start_wait = time.time()
        solved = False

        while time.time() - start_wait < 75:
            res = driver.execute_script("""
                var el = document.querySelector('[name="h-captcha-response"], [name="g-recaptcha-response"]');
                return el ? el.value : '';
            """)
            if res and len(res) > 20:
                solved = True
                print(f" {GREEN}[+]{RESET} Captcha token detected and verified!")
                break
            time.sleep(2)

        if not solved:
            print(f" {YELLOW}[!] Timeout waiting for auto-token. Attempting to click Continue...{RESET}")

        # Click Continue Button
        btn = driver.find_element(By.ID, "createAccountButton")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(4)

        # Check for error display
        err_text = driver.execute_script("""
            var err = document.getElementById('error_display');
            return (err && err.style.display !== 'none') ? err.innerText : '';
        """)
        if err_text:
            print(f" {YELLOW}[!] Steam notification: {err_text}{RESET}")

        # Step 5: Wait for Steam Verification Email from best-temp-mail.com
        print(f" {YELLOW}[*]{RESET} Listening for Steam verification email in best-temp-mail.com...")
        verify_url = mail.wait_for_verification_link(timeout_s=120)
        if not verify_url:
            print(f" {RED}[x]{RESET} Verification email timed out.")
            return None

        print(f" {GREEN}[+]{RESET} Verification link received! Confirming token...")
        # Open verification URL in a new tab
        driver.execute_script("window.open(arguments[0], '_blank');", verify_url)
        time.sleep(4)

        # Switch back to main tab
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(4)

        # Step 6: Finalize Username and Password with Steam Availability Verification
        print(f" {YELLOW}[*]{RESET} Waiting for Steam account name creation form...")

        # Wait for account name field to appear
        acc_field = None
        for _ in range(20):
            try:
                acc_field = driver.find_element(By.ID, "accountname")
                if acc_field.is_displayed():
                    break
            except Exception:
                pass
            time.sleep(2)

        if not acc_field or not acc_field.is_displayed():
            print(f" {RED}[x]{RESET} Account creation form did not appear.")
            return None

        # Loop to ensure username is 100% available and valid on Steam
        max_user_attempts = 8
        user_valid = False
        account_name = ""

        for attempt in range(1, max_user_attempts + 1):
            account_name = generate_username()
            print(f" {YELLOW}[*]{RESET} Checking username ({attempt}/{max_user_attempts}): {BOLD}{account_name}{RESET}...")
            acc_field.clear()
            acc_field.send_keys(account_name)

            # Trigger Steam internal availability check
            driver.execute_script("if (typeof CheckAccountNameAvailability === 'function') { CheckAccountNameAvailability(); }")
            time.sleep(2)

            # Inspect Steam availability response
            avail_status = driver.execute_script("""
                var isAvail = (typeof g_bAccountNameAvailable !== 'undefined') ? g_bAccountNameAvailable : false;
                var el = document.getElementById('accountname_availability');
                var text = el ? el.innerText.trim() : '';
                var hasCheck = el ? el.querySelector('img.green_check') !== null : false;
                return { isAvail: isAvail, text: text, hasCheck: hasCheck };
            """)

            if avail_status.get("isAvail") or avail_status.get("hasCheck"):
                user_valid = True
                print(f" {GREEN}[+]{RESET} Username {BOLD}{account_name}{RESET} is AVAILABLE! Verified by Steam.")
                break
            else:
                reason = avail_status.get("text") or "Taken / In use"
                print(f" {YELLOW}[!] Username {account_name} rejected by Steam ({reason}). Generating alternative...")
                time.sleep(1)

        if not user_valid:
            print(f" {RED}[x]{RESET} Could not find available username after {max_user_attempts} attempts.")
            return None

        # Enter Password and verify
        password = generate_password()
        print(f" {YELLOW}[*]{RESET} Setting valid password...")
        pwd_field = driver.find_element(By.ID, "password")
        pwd_field.clear()
        pwd_field.send_keys(password)

        re_pwd_field = driver.find_element(By.ID, "reenter_password")
        re_pwd_field.clear()
        re_pwd_field.send_keys(password)

        driver.execute_script("if (typeof CheckPasswordStrength === 'function') { CheckPasswordStrength(); }")
        driver.execute_script("if (typeof CheckPasswordsMatch === 'function') { CheckPasswordsMatch(); }")
        time.sleep(1)

        # Submit final registration
        print(f" {YELLOW}[*]{RESET} Submitting final account creation...")
        submit_final = driver.find_element(By.ID, "createAccountButton")
        driver.execute_script("arguments[0].click();", submit_final)
        time.sleep(5)

        # Check for any post-submission error display
        post_err = driver.execute_script("""
            var err = document.getElementById('error_display');
            if (err && err.style.display !== 'none' && err.innerText.trim().length > 0) {
                return err.innerText.trim();
            }
            return '';
        """)

        if post_err:
            print(f" {RED}[x]{RESET} Steam registration error: {post_err}")
            return None

        print(f" {GREEN}{BOLD}[SUCCESS] Steam Account Created & Verified!{RESET}")
        print(f"  Username : {BOLD}{account_name}{RESET}")
        print(f"  Password : {BOLD}{password}{RESET}")
        print(f"  Email    : {BOLD}{email}{RESET}")

        # Save mailbox token for get_code.py Steam Guard retriever
        save_mailbox_token(account_name, email, mail.email_id, mail.int_token, mail.update_tag)

        # Immediately append to steam_account.txt in neat, easy-to-read blocks
        acc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steam_account.txt")
        try:
            count_existing = 0
            if os.path.exists(acc_path):
                with open(acc_path, "r", encoding="utf-8") as f:
                    count_existing = f.read().count("[#")
            new_idx = count_existing + 1
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # If file is empty or new, add title header
            header = ""
            if not os.path.exists(acc_path) or os.path.getsize(acc_path) == 0:
                header = "=" * 60 + "\n               STEAM ACCOUNTS LIST (GENERATED)\n" + "=" * 60 + "\n\n"

            entry_block = f"""------------------------------------------------------------
[#{new_idx}] STEAM ACCOUNT
------------------------------------------------------------
Username   : {account_name}
Password   : {password}
Email      : {email}
Created At : {now_str}
------------------------------------------------------------\n
"""
            with open(acc_path, "a", encoding="utf-8") as f:
                if header:
                    f.write(header)
                f.write(entry_block)
            print(f"  {CYAN}Saved to  : {BOLD}steam_account.txt (Entry #{new_idx}){RESET}")
        except Exception as e_save:
            print(f"  {RED}[!] Failed to write to steam_account.txt: {e_save}{RESET}")

        return {
            "username": account_name,
            "password": password,
            "email": email,
            "created_at": datetime.now().isoformat(),
        }

    except Exception as e:
        print(f" {RED}[x]{RESET} Error during creation cycle: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="Steam Account Creator CLI")
    parser.add_argument("-c", "--count", type=int, default=None, help="Number of accounts to create")
    parser.add_argument("--proxy", type=str, default=None, help="Proxy URL (e.g. http://user:pass@host:port)")
    parser.add_argument("--visible", action="store_true", help="Display Chrome browser window (default: runs silently in background)")
    args = parser.parse_args()

    # Headless is TRUE by default, unless user explicitly passes --visible
    headless_mode = not args.visible

    print_banner()

    # Step 1: Select Count
    count = args.count
    if count is None:
        try:
            user_input = input(f"{BOLD}Number of Steam accounts to create: {RESET}").strip()
            count = int(user_input)
            if count <= 0:
                print("Please enter a positive integer.")
                return
        except ValueError:
            print("Invalid input.")
            return

    # Step 2: Optional Proxy
    proxy = args.proxy
    if proxy is None:
        p_in = input(f"{BOLD}Proxy URL (optional, press Enter for direct connection): {RESET}").strip()
        proxy = p_in if p_in else None

    print(f"\n{CYAN}{BOLD}Starting registration task for {count} account(s)...{RESET}\n")

    successful_accounts = []
    failed_count = 0

    for i in range(1, count + 1):
        acc = create_one_account(
            index=i,
            total=count,
            headless=headless_mode,
            proxy=proxy,
        )
        if acc:
            successful_accounts.append(acc)
        else:
            failed_count += 1
        time.sleep(2)

    # Summary
    print(f"\n{CYAN}{BOLD}=============================================================")
    print("                    TASK SUMMARY")
    print(f"============================================================={RESET}")
    print(f" Requested : {count}")
    print(f" Success   : {GREEN}{len(successful_accounts)}{RESET}")
    print(f" Failed    : {RED}{failed_count}{RESET}")

    acc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steam_account.txt")
    if successful_accounts:
        print(f"\n{GREEN}[+] Semua {len(successful_accounts)} akaun telah disimpan ke: {BOLD}{acc_path}{RESET}")
        for idx, acc in enumerate(successful_accounts, 1):
            print(f" {idx}. {BOLD}{acc['username']}{RESET} : {acc['password']} ({acc['email']})")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Aborted by user.{RESET}")
        sys.exit(0)
