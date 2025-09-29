import requests
import json
import time
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from threading import Thread
from datetime import datetime

class E2EEFacebookMessenger:
    def __init__(self):
        self.setup_directories()
        self.token = self.load_token()
        self.api_url = "https://graph.facebook.com/v18.0/me/messages"
        self.messages = self.load_messages()
        self.current_index = 0
        self.is_running = False
        self.settings = self.load_settings()
        
        # E2EE Encryption setup
        self.encryption_key = self.load_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key) if self.encryption_key else None
        
        # Target user ID
        self.target_user = self.load_user_id()
    
    def setup_directories(self):
        """Required directories create करें"""
        os.makedirs('logs', exist_ok=True)
        os.makedirs('config', exist_ok=True)
    
    def load_settings(self):
        """Settings load करें"""
        settings_file = 'config/settings.json'
        default_settings = {
            "interval_seconds": 60,
            "auto_restart": True,
            "max_retries": 3,
            "log_messages": True
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    return json.load(f)
            else:
                with open(settings_file, 'w') as f:
                    json.dump(default_settings, f, indent=4)
                return default_settings
        except:
            return default_settings
    
    def load_or_create_encryption_key(self):
        """Encryption key load या create करें"""
        try:
            if os.path.exists('encryption_key.txt'):
                with open('encryption_key.txt', 'rb') as f:
                    key = f.read()
                print("✅ Encryption key loaded")
            else:
                # New encryption key generate करें
                password = "facebook_e2ee_secret_2024".encode()
                salt = b'facebook_salt_123456'
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
                with open('encryption_key.txt', 'wb') as f:
                    f.write(key)
                print("✅ New encryption key created")
            return key
        except Exception as e:
            print(f"❌ Encryption key error: {e}")
            return None
    
    def encrypt_message(self, message):
        """Message को encrypt करें"""
        if not self.fernet:
            return message
        
        encrypted = self.fernet.encrypt(message.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def log_message(self, message_type, content):
        """Message log करें"""
        if not self.settings.get('log_messages', True):
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message_type}: {content}\n"
        
        try:
            with open('logs/message_log.txt', 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    def load_token(self):
        """token.txt से Facebook token load करें"""
        try:
            with open('token.txt', 'r') as f:
                token = f.read().strip()
            if token and token != "YOUR_FACEBOOK_TOKEN_HERE":
                print("✅ Token loaded successfully")
                return token
            else:
                print("❌ Please update token.txt with your Facebook token")
                return None
        except FileNotFoundError:
            print("❌ token.txt file not found")
            return None
    
    def load_user_id(self):
        """user_id.txt से target user ID load करें"""
        try:
            with open('user_id.txt', 'r') as f:
                user_id = f.read().strip()
            if user_id and user_id != "FACEBOOK_USER_ID_HERE":
                print(f"✅ Target user loaded: {user_id}")
                return user_id
            else:
                print("❌ Please update user_id.txt with target Facebook ID")
                return None
        except FileNotFoundError:
            print("❌ user_id.txt file not found")
            return None
    
    def load_messages(self):
        """message.txt से messages load करें"""
        try:
            with open('message.txt', 'r', encoding='utf-8') as f:
                messages = [line.strip() for line in f if line.strip()]
            print(f"✅ {len(messages)} messages loaded")
            return messages
        except FileNotFoundError:
            print("❌ message.txt file not found")
            return []
    
    def send_encrypted_message(self, message):
        """E2EE encrypted message Facebook पर send करें"""
        if not self.token or not self.target_user:
            print("❌ Token or user ID missing")
            return False
        
        # Message encrypt करें
        encrypted_msg = self.encrypt_message(message)
        
        # Facebook format में message तैयार करें
        fb_message = f"🔐 ENCRYPTED_MESSAGE_START\n{encrypted_msg}\n🔐 ENCRYPTED_MESSAGE_END\n💡 Use receiver.py to decrypt"
        
        payload = {
            "recipient": {"id": self.target_user},
            "message": {"text": fb_message},
            "messaging_type": "MESSAGE_TAG",
            "tag": "NON_PROMOTIONAL_SUBSCRIPTION"
        }
        
        params = {
            "access_token": self.token
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Encrypted message sent")
                print(f"📧 Original: {message}")
                print(f"🔐 Encrypted: {encrypted_msg[:50]}...")
                self.log_message("SENT", f"Original: {message} | Encrypted: {encrypted_msg[:30]}...")
                return True
            else:
                error_msg = f"Failed: {response.json()}"
                print(f"❌ {error_msg}")
                self.log_message("ERROR", error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Send error: {e}"
            print(f"❌ {error_msg}")
            self.log_message("ERROR", error_msg)
            return False
    
    def send_next_encrypted_message(self):
        """Next encrypted message send करें"""
        if not self.messages:
            print("❌ No messages available")
            return False
        
        message = self.messages[self.current_index]
        success = self.send_encrypted_message(message)
        
        if success:
            self.current_index += 1
            
            # अगर सभी messages send हो गए, तो restart करें
            if self.current_index >= len(self.messages):
                print("🔄 All messages sent. Restarting from beginning...")
                self.current_index = 0
                self.log_message("RESTART", "Message cycle restarted")
            
            return True
        return False
    
    def start_auto_encrypted_sending(self, interval_seconds=60):
        """Automatic encrypted message sending start करें"""
        if not self.token or not self.messages:
            print("❌ Cannot start: Token or messages missing")
            return
        
        self.is_running = True
        print(f"🚀 Starting E2EE auto-send every {interval_seconds} seconds")
        print("🔐 All messages will be encrypted end-to-end")
        self.log_message("SYSTEM", f"Auto-send started with {interval_seconds}s interval")
        
        message_count = 0
        while self.is_running:
            try:
                if self.send_next_encrypted_message():
                    message_count += 1
                
                print(f"📊 Total sent: {message_count} | Next in {interval_seconds}s...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("🛑 Stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in auto-send: {e}")
                time.sleep(interval_seconds)
        
        self.log_message("SYSTEM", f"Auto-send stopped. Total sent: {message_count}")
    
    def stop_auto_sending(self):
        """Auto sending stop करें"""
        self.is_running = False
        print("🛑 Auto-sending stopped")

def main():
    messenger = E2EEFacebookMessenger()
    
    # Check if required files exist
    required_files = {
        'token.txt': 'YOUR_FACEBOOK_TOKEN_HERE',
        'user_id.txt': 'FACEBOOK_USER_ID_HERE', 
        'message.txt': 'नमस्ते! यह encrypted message है।\nयह message end-to-end encrypted है।\nसिर्फ sender और receiver ही इसे read कर सकते हैं।\nयह secure communication का example है।'
    }
    
    for filename, default_content in required_files.items():
        if not os.path.exists(filename):
            print(f"📝 Creating {filename} file...")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(default_content)
    
    print("\n" + "="*60)
    print("🔐 E2EE Facebook Messenger Auto Sender")
    print("="*60)
    print("1. Send single encrypted message")
    print("2. Start auto-sending encrypted messages") 
    print("3. Decrypt a message")
    print("4. Load new messages")
    print("5. Check status")
    print("6. Exit")
    
    while True:
        choice = input("\nChoose option (1-6): ").strip()
        
        if choice == '1':
            messenger.send_next_encrypted_message()
        
        elif choice == '2':
            try:
                interval = int(input("Enter interval in seconds (default 60): ") or 60)
            except ValueError:
                interval = 60
            
            thread = Thread(target=messenger.start_auto_encrypted_sending, args=(interval,))
            thread.daemon = True
            thread.start()
            
            input("Press Enter to stop...\n")
            messenger.stop_auto_sending()
        
        elif choice == '3':
            encrypted_msg = input("Enter encrypted message to decrypt: ")
            decrypted = messenger.decrypt_message(encrypted_msg)
            print(f"🔓 Decrypted message: {decrypted}")
        
        elif choice == '4':
            messenger.messages = messenger.load_messages()
            messenger.current_index = 0
            print("✅ Messages reloaded")
        
        elif choice == '5':
            print(f"✅ Token: {'LOADED' if messenger.token else 'MISSING'}")
            print(f"🔐 Encryption: {'ACTIVE' if messenger.fernet else 'INACTIVE'}")
            print(f"📱 Messages: {len(messenger.messages)} loaded")
            print(f"📍 Current index: {messenger.current_index}")
            print(f"👤 Target user: {messenger.target_user}")
            print(f"⚙️ Auto-restart: {messenger.settings.get('auto_restart', True)}")
        
        elif choice == '6':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
