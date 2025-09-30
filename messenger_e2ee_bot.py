#!/usr/bin/env python3
# messenger_e2ee_bot.py
import json
import time
import os
import atexit
import random
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

APPSTATE_FILE = "appstate.json"
USER_FILE = "replied_users.json"

def load_config(path="config.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file '{path}' not found.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class MessengerE2EEBot:
    def __init__(self, cfg):
        options = webdriver.ChromeOptions()
        if cfg.get("headless", False):
            options.add_argument("--headless=new")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.wait = WebDriverWait(self.driver, 20)
        self.email = cfg.get("email", "") or ""
        self.password = cfg.get("password", "") or ""
        self.delay_between_messages = float(cfg.get("delay_between_messages", 2))
        self.message_file = cfg.get("message_file", "messages.txt")
        self.targets_file = cfg.get("targets_file", "targets.txt")
        self.replied_users = self.load_replied_users()
        atexit.register(self.close)

    # ---------- Appstate ----------
    def save_appstate(self):
        try:
            self.driver.get("https://www.facebook.com")
            time.sleep(2)
            data = {
                "cookies": self.driver.get_cookies(),
                "localStorage": self.driver.execute_script(
                    "var items = {}; for(var i=0;i<localStorage.length;i++){ var k = localStorage.key(i); items[k] = localStorage.getItem(k);} return items;"
                )
            }
            with open(APPSTATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
            print("💾 AppState saved")
        except Exception as e:
            print("❌ Error saving appstate:", e)
            traceback.print_exc()

    def load_appstate(self):
        try:
            if os.path.exists(APPSTATE_FILE):
                with open(APPSTATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.driver.get("https://www.facebook.com")
                time.sleep(1)
                for cookie in data.get("cookies", []):
                    try:
                        if "sameSite" in cookie and cookie["sameSite"] == "None":
                            cookie["sameSite"] = "Strict"
                        if "expiry" in cookie:
                            cookie["expiry"] = int(cookie["expiry"])
                        self.driver.add_cookie(cookie)
                    except Exception:
                        pass
                # restore localStorage
                for k, v in data.get("localStorage", {}).items():
                    try:
                        self.driver.execute_script("localStorage.setItem(arguments[0], arguments[1]);", k, v)
                    except Exception:
                        pass
                self.driver.refresh()
                time.sleep(4)
                print("✅ AppState loaded")
                return True
            return False
        except Exception as e:
            print("❌ Error loading appstate:", e)
            traceback.print_exc()
            return False

    # ---------- replied users ----------
    def load_replied_users(self):
        if os.path.exists(USER_FILE):
            try:
                with open(USER_FILE, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def save_replied_users(self):
        try:
            with open(USER_FILE, "w", encoding="utf-8") as f:
                json.dump(list(self.replied_users), f)
        except Exception as e:
            print("❌ Could not save replied users:", e)

    def has_replied(self, uid):
        return uid in self.replied_users

    def mark_replied(self, uid):
        self.replied_users.add(uid)
        self.save_replied_users()

    # ---------- read files ----------
    def read_messages(self):
        if not os.path.exists(self.message_file):
            print("❌ messages file missing")
            return []
        with open(self.message_file, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]

    def read_targets(self):
        if not os.path.exists(self.targets_file):
            print("❌ targets file missing")
            return []
        with open(self.targets_file, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]

    # ---------- login ----------
    def login_with_credentials(self):
        if not self.email or not self.password:
            print("⚠️ No credentials in config, skip auto login.")
            return False
        try:
            self.driver.get("https://www.facebook.com/login")
            email_el = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            pass_el = self.wait.until(EC.presence_of_element_located((By.ID, "pass")))
            email_el.clear(); email_el.send_keys(self.email)
            pass_el.clear(); pass_el.send_keys(self.password)
            try:
                btn = self.driver.find_element(By.NAME, "login"); btn.click()
            except:
                pass
            time.sleep(5)
            cur = self.driver.current_url
            if "checkpoint" in cur or "login" in cur:
                print("⚠️ Login may require checkpoint/2FA.")
                return False
            print("✅ Automated login seems OK (no immediate checkpoint).")
            return True
        except Exception as e:
            print("❌ Exception during login:", e)
            traceback.print_exc()
            return False

    # ---------- E2EE detection ----------
    def is_chat_e2ee_by_ui(self):
        """
        Tries multiple UI checks in the currently open messenger chat.
        Returns (True/False, reason_str)
        """
        try:
            # common phrases to look for
            phrases = [
                "end-to-end encryption",
                "end to end encryption",
                "protected with end-to-end encryption",
                "Messages and calls are protected with end-to-end encryption",
                "This conversation is end-to-end encrypted",
                "End-to-end encrypted"
            ]
            page_text = ""
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            except:
                pass
            for p in phrases:
                if p.lower() in page_text:
                    return True, f"UI phrase '{p}' found"

            # look for lock icon elements / aria-labels
            try:
                lock_el = self.driver.find_elements(By.XPATH, "//*[contains(@aria-label,'end-to-end') or contains(@aria-label,'encrypted') or contains(@aria-label,'lock')]")
                if lock_el and len(lock_el) > 0:
                    return True, "lock/aria-label indicator found"
            except:
                pass

            return False, "No UI indicator text/lock found"
        except Exception as e:
            return False, f"UI check exception: {e}"

    def is_chat_e2ee_by_localstorage(self):
        """
        Look for likely keys in localStorage that suggest client-side encryption state.
        This is heuristic — presence does not guarantee, absence does not fully disprove.
        """
        try:
            items = self.driver.execute_script(
                "var i, items = {}; for(i=0;i<localStorage.length;i++){ var k = localStorage.key(i); items[k]=localStorage.getItem(k);} return items;"
            )
            if not isinstance(items, dict):
                return False, "localStorage unreadable"
            keys = list(items.keys())
            # heuristics: keys containing these substrings
            suspects = ["e2ee", "endtoend", "end-to-end", "crypto", "signal", "secret", "secure", "private_key", "messenger_key"]
            found = [k for k in keys for s in suspects if s in k.lower()]
            if found:
                return True, f"localStorage keys suggesting encryption found: {found[:5]}"
            # also check for specific structured storage like 'messenger_local_storage' etc.
            return False, "No suspicious localStorage keys found"
        except Exception as e:
            return False, f"localStorage check exception: {e}"

    def ensure_chat_is_e2ee(self):
        """
        Run both UI + localStorage heuristics and return verdict.
        """
        ui_ok, ui_reason = self.is_chat_e2ee_by_ui()
        ls_ok, ls_reason = self.is_chat_e2ee_by_localstorage()
        # prefer UI evidence, but if either shows positive return True
        if ui_ok:
            return True, f"UI check ok: {ui_reason}"
        if ls_ok:
            return True, f"localStorage check ok: {ls_reason}"
        return False, f"No E2EE evidence. UI: {ui_reason}; Storage: {ls_reason}"

    # ---------- send ----------
    def send_messages_to_target(self, target_id, messages):
        if not target_id:
            return False, "empty id"
        if self.has_replied(target_id):
            return False, "already replied"

        chat_url = f"https://www.messenger.com/t/{target_id}"
        self.driver.get(chat_url)
        time.sleep(3)

        # First check whether logged in / page loaded
        cur = self.driver.current_url
        if "login" in cur or "checkpoint" in cur:
            return False, "not logged in / checkpoint"

        # E2EE check
        ok, reason = self.ensure_chat_is_e2ee()
        if not ok:
            return False, f"chat not E2EE: {reason}"

        # find message box
        try:
            msg_box = None
            try:
                msg_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']")))
            except:
                try:
                    msg_box = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']")))
                except:
                    pass
            if not msg_box:
                return False, "message box not found"

            for i, m in enumerate(messages, 1):
                try:
                    msg_box.click()
                except:
                    pass
                msg_box.send_keys(m)
                time.sleep(0.3)
                msg_box.send_keys(Keys.ENTER)
                print(f"✅ Sent {i}/{len(messages)} to {target_id}")
                if i < len(messages):
                    time.sleep(self.delay_between_messages + random.uniform(0.5, 1.5))
            self.mark_replied(target_id)
            return True, "sent"
        except Exception as e:
            traceback.print_exc()
            return False, f"send error: {e}"

    def send_to_all_targets(self):
        messages = self.read_messages()
        targets = self.read_targets()
        if not messages:
            print("❌ No messages loaded.")
            return
        if not targets:
            print("❌ No targets loaded.")
            return

        print(f"Starting: {len(targets)} targets. Skipping already-replied.")
        for idx, t in enumerate(targets, 1):
            print(f"-> ({idx}/{len(targets)}) {t}")
            success, reason = self.send_messages_to_target(t, messages)
            if success:
                print(f"✔️ {t} done.")
            else:
                print(f"❌ {t} skipped/failed: {reason}")
                # If not logged in, stop and ask for manual login
                if "not logged in" in reason.lower() or "checkpoint" in reason.lower():
                    print("🔐 Looks like you're not logged in or Facebook asked for verification. Please login manually and save appstate, then re-run.")
                    return
            time.sleep(2 + random.random()*2)
        print("All targets processed.")

    def close(self):
        try:
            self.driver.quit()
        except:
            pass

if __name__ == "__main__":
    print("⚠️ WARNING: Automating Messenger may violate Facebook's TOS. Use responsibly.")
    cfg = load_config("config.json")
    bot = MessengerE2EEBot(cfg)

    # Try load appstate
    loaded = bot.load_appstate()
    if not loaded:
        # try automated login if creds present
        if bot.email and bot.password:
            ok = bot.login_with_credentials()
            if ok:
                bot.save_appstate()
                loaded = True
        if not loaded:
            # manual login flow
            print("🔁 Please login manually in the opened browser, open a sample E2EE chat and verify 'end-to-end' indicator, then press Enter here to save appstate.")
            bot.driver.get("https://www.facebook.com")
            input("After manual login + opening target E2EE chat, press Enter to save appstate...")
            bot.save_appstate()

    # Now run send
    bot.send_to_all_targets()
    bot.close()
