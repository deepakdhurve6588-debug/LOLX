# send_multiple_targets.py
import time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

TARGETS_FILE = "targets.txt"
MESSAGES_FILE = "messages.txt"

def read_lines(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def send_messages(page, messages):
    selectors = ['div[role="textbox"]', 'div[contenteditable="true"]', 'textarea']
    input_el = None
    for sel in selectors:
        try:
            el = page.locator(sel)
            if el.count() > 0:
                input_el = el.first
                break
        except:
            pass
    if not input_el:
        print("❌ Message input box not found.")
        return False
    for i, m in enumerate(messages, start=1):
        try:
            input_el.click()
        except:
            pass
        try:
            input_el.fill(m)
        except:
            input_el.press("Control+a")
            input_el.type(m)
        try:
            input_el.press("Enter")
        except:
            page.keyboard.press("Enter")
        print(f"✅ Sent {i}/{len(messages)}")
        time.sleep(1.5)
    return True

def main():
    targets = read_lines(TARGETS_FILE)
    messages = read_lines(MESSAGES_FILE)
    if not targets:
        print("❌ No targets found in targets.txt")
        return
    if not messages:
        print("❌ No messages found in messages.txt")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        for idx, target in enumerate(targets, start=1):
            print(f"\n=== ({idx}/{len(targets)}) Sending to Target: {target} ===")
            url = f"https://www.messenger.com/t/{target}"
            page.goto(url)
            try:
                page.wait_for_load_state("networkidle", timeout=7000)
            except PWTimeout:
                pass
            # login check
            if "login" in page.url or "checkpoint" in page.url:
                print("🔐 Please login manually in the opened browser window.")
                input("After login (and opening same chat), press Enter here...")
                page.goto(url)
                try:
                    page.wait_for_load_state("networkidle", timeout=7000)
                except PWTimeout:
                    pass
            time.sleep(2)
            success = send_messages(page, messages)
            if success:
                print(f"🎉 Messages sent to {target}")
            else:
                print(f"⚠️ Failed to send to {target}")
            time.sleep(1.5)

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
