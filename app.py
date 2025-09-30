import os
import time
from userid_to_e2ee_messenger import UserIDToE2EEMessenger

def start_bot():
    print("🚀 E2EE Messenger Bot Starting on Render...")
    print("=" * 50)
    print(f"🕒 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🔧 Environment: {os.environ.get('RENDER', 'Production')}")
    
    # Check if config files exist
    required_files = ['config/token.txt', 'config/user_id.txt', 'config/messages.txt']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Missing: {file}")
            return
    
    # Initialize and start bot
    bot = UserIDToE2EEMessenger()
    
    # Auto-start with 5 minute interval
    print("🔧 Starting E2EE Auto-Messaging...")
    bot.start_auto_e2ee_messaging(interval=300)  # 5 minutes

if __name__ == "__main__":
    start_bot()
