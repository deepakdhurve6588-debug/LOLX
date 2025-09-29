from e2ee_messenger import E2EEMessenger
import os

def start_bot():
    print("🚀 E2EE Messenger Bot Starting...")
    
    messenger = E2EEMessenger()
    
    # Auto-login if credentials in environment
    env_email = os.environ.get('BOT_EMAIL')
    env_password = os.environ.get('BOT_PASSWORD')
    
    if env_email and env_password:
        success, message = messenger.login_system.login_user(env_email, env_password)
        if success:
            enc_success, enc_message = messenger.setup_user_encryption(env_email, env_password)
            if enc_success:
                messenger.current_user = env_email
                print(f"✅ Auto-login successful: {env_email}")
                
                # Load config and start auto-messaging
                if messenger.load_facebook_config():
                    messenger.start_auto_messaging(interval=300)  # 5 minutes
                else:
                    print("❌ Facebook configuration missing")
            else:
                print(f"❌ Encryption setup failed: {enc_message}")
        else:
            print(f"❌ Auto-login failed: {message}")
    else:
        print("❌ Auto-login credentials missing")
        print("💡 Set BOT_EMAIL and BOT_PASSWORD environment variables")

if __name__ == "__main__":
    start_bot()
