import os
import time
from main import E2EEFacebookMessenger

def start_bot():
    print("🚀 Starting E2EE Bot on Render...")
    print(f"📁 Directory: {os.getcwd()}")
    
    # Check essential files
    if not os.path.exists('token.txt'):
        print("❌ token.txt missing")
        return
        
    if not os.path.exists('user_id.txt'):
        print("❌ user_id.txt missing") 
        return
    
    bot = E2EEFacebookMessenger()
    
    if bot.token and bot.target_user:
        # 2 minutes interval
        bot.start_auto_encrypted_sending(120)
    else:
        print("❌ Configuration missing")

if __name__ == "__main__":
    start_bot()
