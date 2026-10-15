import os
import sys
import json
import time
import re
import requests
from colorama import init, Fore, Style

init(autoreset=True)
GREEN = Fore.GREEN
CYAN = Fore.CYAN
YELLOW = Fore.YELLOW
RED = Fore.RED
BOLD = Style.BRIGHT
RESET = Style.RESET_ALL

API_BASE = "https://best-temp-mail.com/api/v3"


def main():
    mb_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mailboxes.json")
    if not os.path.exists(mb_file) or os.path.getsize(mb_file) == 0:
        print(f"\n{RED}[!] No Steam account records found (mailboxes.json is empty).{RESET}")
        print("Please generate a new Steam account using steam_creator.py first.")
        input("\nPress Enter to exit...")
        return

    try:
        with open(mb_file, "r", encoding="utf-8") as f:
            mailboxes = json.load(f)
    except Exception as e:
        print(f"{RED}[!] Error reading record file: {e}{RESET}")
        input("\nPress Enter to exit...")
        return

    if not mailboxes:
        print(f"{RED}[!] Account list is empty.{RESET}")
        input("\nPress Enter to exit...")
        return

    user_list = list(mailboxes.keys())
    last_user = user_list[-1]

    # Target username
    target_user = None
    if len(sys.argv) > 1:
        target_user = sys.argv[1].strip()
    else:
        print(f"\n{CYAN}{BOLD}=============================================================")
        print("                 STEAM GUARD CODE FINDER")
        print(f"============================================================={RESET}")
        print(" Recent Accounts:")
        for idx, u in enumerate(user_list[-5:], 1):
            print(f"  {idx}. {BOLD}{u}{RESET} ({mailboxes[u].get('email')})")
        print("-------------------------------------------------------------")
        print(" Enter Steam Username:")
        print(f" (Press {BOLD}Enter{RESET} to use the most recent account: {BOLD}{YELLOW}{last_user}{RESET})")
        choice = input(f" {BOLD}Username: {RESET}").strip()
        target_user = choice if choice else last_user

    # Search (case-insensitive)
    matched_entry = None
    matched_key = None
    for k, v in mailboxes.items():
        if k.lower() == target_user.lower():
            matched_key = k
            matched_entry = v
            break

    if not matched_entry:
        print(f"\n{RED}[!] Username '{target_user}' was not found in records.{RESET}")
        print(f"Available accounts: {', '.join(user_list)}")
        input("\nPress Enter to exit...")
        return

    email = matched_entry.get("email")
    email_id = matched_entry.get("email_id")
    int_token = matched_entry.get("int_token")
    update_tag = matched_entry.get("update_tag")

    print(f"\n{YELLOW}[*]{RESET} Checking mailbox for {BOLD}{matched_key}{RESET} ({email})...")
    print(f"    {YELLOW}Waiting for Steam Guard verification email (approx. 5-30s)...{RESET}")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://best-temp-mail.com/",
        "Origin": "https://best-temp-mail.com",
    })

    deadline = time.time() + 90
    found_code = None

    while time.time() < deadline:
        try:
            payload = {
                "address": email,
                "id": email_id,
                "intToken": int_token,
                "update_tag": update_tag,
            }
            r = session.post(f"{API_BASE}/getEmailList", json=payload, timeout=12)
            if r.status_code == 200:
                data = r.json().get("data", {})
                new_tag = data.get("update_tag")
                if new_tag:
                    update_tag = new_tag

                for item in data.get("emailList", []):
                    subj = item.get("subject", "")
                    content = (item.get("text") or "") + "\n" + (item.get("html") or "")

                    # 1. Regex specifically targeting Steam Guard sentences
                    m = re.search(r'(?:Steam Guard code|login to your account|allow you to log in[^\n:]*?)[:\s]+([A-Z0-9]{5})\b', content, re.IGNORECASE)
                    if m:
                        found_code = m.group(1).upper()
                        break

                    # 2. General 5-character token regex in Steam emails
                    if "steam" in subj.lower() or "steam" in content.lower():
                        all_5s = re.findall(r'\b[A-Z0-9]{5}\b', content)
                        ignore = {"STEAM", "GUARD", "LOGIN", "HTTPS", "CLICK", "EMAIL", "RESET", "VALVE", "STORE", "COMPO"}
                        valid = [c for c in all_5s if c not in ignore and not c.isdigit()]
                        if valid:
                            found_code = valid[0]
                            break

            if found_code:
                break
        except Exception:
            pass

        time.sleep(3)
        print(".", end="", flush=True)

    print()

    if found_code:
        print(f"\n{GREEN}{BOLD}=============================================================")
        print(f"             STEAM GUARD CODE:  {YELLOW}{BOLD}{found_code}{RESET}")
        print(f"{GREEN}{BOLD}============================================================={RESET}")
        print(f" Account  : {BOLD}{matched_key}{RESET}")
        print(f" Email    : {email}")
        print(f" Code     : {YELLOW}{BOLD}{found_code}{RESET} (Enter this code into Steam)")
        print(f"=============================================================\n")

        # Copy to Windows clipboard
        try:
            os.system(f'powershell -command "Set-Clipboard -Value \'{found_code}\'" >nul 2>&1')
            print(f" {GREEN}[+] Code {BOLD}{found_code}{RESET}{GREEN} has been auto-copied to Clipboard! (Press Ctrl+V in Steam){RESET}\n")
        except Exception:
            pass
    else:
        print(f"\n{RED}[x] Steam Guard email has not arrived within 90 seconds.{RESET}")
        print("Please click 'Resend Code' in Steam and run this script again.")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Cancelled.{RESET}")
        sys.exit(0)
