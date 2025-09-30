import os
import time
from userid_to_e2ee_messenger import UserIDToE2EEMessenger

def start_bot():
    print("🚀 E2EE Messenger Bot Starting on Render...")
    print("=" * 50)
    print(f"🕒 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🌐 Environment: Render Cloud")
    
    # List files for debugging
    print("\n📁 Directory Contents:")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.txt') or file.endswith('.py'):
                print(f"   📄 {os.path.join(root, file)}")
    
    # Check config files
    print("\n🔍 Checking Config Files:")
    config_files = {
        'token.txt': 'config/token.txt',
        'user_id.txt': 'config/user_id.txt', 
        'messages.txt': 'config/messages.txt'
    }
    
    all_files_ok = True
    for name, path in config_files.items():
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read().strip()
                status = "✅" if content and "YOUR_" not in content else "❌"
                print(f"   {status} {name}: {content[:30]}...")
        else:
            print(f"   ❌ {name}: MISSING")
            all_files_ok = False
    
    if not all_files_ok:
        print("\n❌ Missing config files. Please check your repository.")
        return
    
    print("\n🎯 Starting E2EE Messenger Bot...")
    
    try:
        # Initialize bot
        bot = UserIDToE2EEMessenger()
        
        # Continuous running for Render
        message_count = 0
        while True:
            print(f"\n🔄 Cycle {message_count + 1} starting...")
            bot.start_auto_e2ee_messaging(interval=300)  # 5 minutes
            message_count += 1
            print(f"♻️  Restarting bot... Completed {message_count} cycles")
            time.sleep(10)  # Brief pause before restart
            
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        print("🔄 Restarting in 30 seconds...")
        time.sleep(30)
        start_bot()  # Restart

if __name__ == "__main__":
    start_bot()
