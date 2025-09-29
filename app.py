import os
import time
from main import FacebookMessengerBot

def start_bot():
    print("🚀 Starting Messenger Bot on Render...")
    print("💬 Direct to Messenger Inbox")
    print(f"📁 Directory: {os.getcwd()}")
    
    # Check essential files
    required_files = ['token.txt', 'user_id.txt', 'message.txt']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ {file} missing")
            return
    
    bot = FacebookMessengerBot()
    
    if bot.token and bot.target_user:
        # 2 minutes interval
        bot.start_auto_messaging(120)
    else:
        print("❌ Configuration missing")

if __name__ == "__main__":
    start_bot()
