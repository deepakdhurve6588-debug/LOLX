import json
import os
from cryptography.fernet import Fernet

def check_setup():
    """Setup completeness check करें"""
    required_files = ['token.txt', 'user_id.txt', 'message.txt', 'encryption_key.txt']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing files:", ", ".join(missing_files))
        return False
    
    # Check if tokens are updated
    with open('token.txt', 'r') as f:
        token = f.read().strip()
    if token == "YOUR_FACEBOOK_TOKEN_HERE":
        print("❌ Please update token.txt with your Facebook token")
        return False
    
    with open('user_id.txt', 'r') as f:
        user_id = f.read().strip()
    if user_id == "FACEBOOK_USER_ID_HERE":
        print("❌ Please update user_id.txt with target Facebook ID")
        return False
    
    print("✅ Setup complete - all files configured")
    return True

def generate_new_encryption_key():
    """New encryption key generate करें"""
    try:
        key = Fernet.generate_key()
        with open('encryption_key.txt', 'wb') as f:
            f.write(key)
        print("✅ New encryption key generated")
        return key
    except Exception as e:
        print(f"❌ Error generating key: {e}")
        return None

def view_message_log():
    """Message log view करें"""
    log_file = 'logs/message_log.txt'
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            print(f"\n{'='*50}")
            print("MESSAGE LOG")
            print('='*50)
            print(f.read())
    else:
        print("❌ No log file found")

def clear_logs():
    """Logs clear करें"""
    log_files = ['logs/message_log.txt', 'logs/decryption_log.txt']
    for log_file in log_files:
        if os.path.exists(log_file):
            open(log_file, 'w').close()
    print("✅ Logs cleared")

if __name__ == "__main__":
    print("Utility functions for E2EE Facebook Messenger")
