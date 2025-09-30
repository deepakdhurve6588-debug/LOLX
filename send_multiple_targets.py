# send_multiple_targets.py
import time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

TARGETS_FILE = "targets.txt"
MESSAGES_FILE = "messages.txt"
STORAGE_STATE_FILE = "storage_state.json"

def read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

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
    for m in messages:
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
        time.sleep(1.5)
    return True

def main():
    targets = read_lines(TARGETS_FILE)
    messages = read_lines(MESSAGES_FILE)

    if not targets or not messages:
        print("❌ Targets or messages missing.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=STORAGE_STATE_FILE)
        page = context.new_page()

        for idx, target in enumerate(targets, start=1):
            url = f"https://www.messenger.com/t/{target}"
            page.goto(url)
            try:
                page.wait_for_load_state("networkidle", timeout=7000)
            except PWTimeout:
                pass
            time.sleep(2)
            send_messages(page, messages)
            print(f"✅ Sent messages to {target}")
            time.sleep(2)

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
