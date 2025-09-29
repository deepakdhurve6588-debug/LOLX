import os
import time
import threading
from main import E2EEFacebookMessenger

def start_bot():
    """Main bot start करें"""
    print("🚀 Starting E2EE Facebook Messenger Bot on Render...")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🔧 Environment: {os.environ.get('RENDER', 'Development')}")
    
    # Bot instance create करें
    bot = E2EEFacebookMessenger()
    
    # Check if essential configuration है
    if not bot.token or not bot.target_user:
        print("❌ Missing token or user ID. Please check your configuration.")
        print("💡 Make sure token.txt and user_id.txt are properly configured.")
        return
    
    print("✅ Bot configured successfully")
    print(f"📱 Messages loaded: {len(bot.messages)}")
    print(f"👤 Target user: {bot.target_user}")
    print(f"🔐 Encryption: {'ACTIVE' if bot.fernet else 'INACTIVE'}")
    
    # Auto-send start करें
    interval = int(os.environ.get('MESSAGE_INTERVAL', '300'))  # Default 5 minutes
    print(f"⏰ Message interval: {interval} seconds")
    
    bot.start_auto_encrypted_sending(interval)

if __name__ == "__main__":
    # Render पर continuous run के लिए
    start_bot()
