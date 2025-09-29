import requests
import json
import time
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime

class E2EEFacebookMessenger:
    def __init__(self):
        self.setup_directories()
        self.token = self.load_token()
        self.api_url = "https://graph.facebook.com/v18.0/me/messages"
        self.messages = self.load_messages()
        self.current_index = 0
        self.is_running = True
        
        # E2EE Encryption setup
        self.encryption_key = self.load_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key) if self.encryption_key else None
        
        # Target user ID
        self.target_user = self.load_user_id()
        
        print("🔐 E2EE MESSENGER INITIALIZED")
        print(f"📝 Token Loaded: {self.token[:20]}...")
        print(f"👤 Target User: {self.target_user}")
        print(f"📨 Messages Loaded: {len(self.messages)}")
    
    def setup_directories(self):
        """Required directories create करें"""
        os.makedirs('logs', exist_ok=True)
        os.makedirs('config', exist_ok=True)
    
    def load_token(self):
        """token.txt से token load करें"""
        try:
            with open('token.txt', 'r') as f:
                token = f.read().strip()
            
            if not token or token == "YOUR_FACEBOOK_TOKEN_HERE":
                print("❌ Please update token.txt with your Facebook token")
                return None
            
            print(f"✅ Token loaded: {token[:25]}...")
            return token
            
        except FileNotFoundError:
            print("❌ token.txt file not found")
            return None
    
    def load_or_create_encryption_key(self):
        """Encryption key load या create करें"""
        try:
            if os.path.exists('encryption_key.txt'):
                with open('encryption_key.txt', 'rb') as f:
                    key = f.read()
                print("✅ Encryption key loaded")
            else:
                # New encryption key generate करें
                key = Fernet.generate_key()
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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message_type}: {content}\n"
        
        try:
            with open('logs/message_log.txt', 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    def load_user_id(self):
        """user_id.txt से target user ID load करें"""
        try:
            with open('user_id.txt', 'r') as f:
                user_id = f.read().strip()
            if user_id and user_id != "FACEBOOK_USER_ID_HERE":
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
            return messages
        except FileNotFoundError:
            print("❌ message.txt file not found")
            return []
    
    def verify_token(self):
        """Token verify करें"""
        print("🔍 Verifying token...")
        try:
            url = f"https://graph.facebook.com/v18.0/me?access_token={self.token}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ TOKEN VALID - User: {user_data.get('name')}")
                return True
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"❌ TOKEN ERROR: {error_msg}")
                
                # Specific error handling
                if 'expired' in error_msg.lower():
                    print("💡 Token expired! Get new token from MonokaiTool")
                elif 'permission' in error_msg.lower():
                    print("💡 Permission missing! Check page permissions")
                
                return False
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    def send_test_message(self):
        """Test message send करें"""
        print("\n🧪 Sending test message...")
        
        test_msg = "✅ Test message from E2EE Bot - " + datetime.now().strftime("%H:%M:%S")
        
        payload = {
            "recipient": {"id": self.target_user},
            "message": {"text": test_msg},
            "messaging_type": "MESSAGE_TAG",
            "tag": "NON_PROMOTIONAL_SUBSCRIPTION"
        }
        
        params = {"access_token": self.token}
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ TEST MESSAGE SENT SUCCESSFULLY!")
                return True
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"❌ TEST FAILED: {error_msg}")
                return False
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False
    
    def send_encrypted_message(self, message):
        """E2EE encrypted message send करें"""
        if not self.target_user:
            print("❌ User ID missing")
            return False
        
        # Message encrypt करें
        encrypted_msg = self.encrypt_message(message)
        
        # Facebook format में message तैयार करें
        fb_message = f"🔐 ENCRYPTED_MESSAGE\n{encrypted_msg}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        payload = {
            "recipient": {"id": self.target_user},
            "message": {"text": fb_message},
            "messaging_type": "MESSAGE_TAG",
            "tag": "NON_PROMOTIONAL_SUBSCRIPTION"
        }
        
        params = {"access_token": self.token}
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Message {self.current_index + 1} sent successfully!")
                print(f"   📧 Original: {message}")
                self.log_message("SENT", f"Message {self.current_index + 1}: {message}")
                return True
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"❌ Send failed: {error_msg}")
                self.log_message("ERROR", error_msg)
                return False
                
        except Exception as e:
            print(f"❌ Network error: {e}")
            self.log_message("ERROR", f"Network: {e}")
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
        print(f"🚀 STARTING AUTO-SEND (Interval: {interval_seconds}s)")
        print("=" * 50)
        
        # First verify token
        if not self.verify_token():
            print("❌ Cannot start: Token invalid")
            return
        
        if not self.target_user:
            print("❌ Cannot start: User ID missing")
            return
        
        # Test message send करें
        print("\n🧪 Sending test message first...")
        if not self.send_test_message():
            print("❌ Test failed. Cannot start auto-send.")
            return
        
        print("✅ Test successful! Starting auto-send...")
        
        message_count = 0
        while self.is_running:
            try:
                print(f"\n🎯 Sending message {self.current_index + 1}/{len(self.messages)}...")
                
                if self.send_next_encrypted_message():
                    message_count += 1
                    print(f"📊 Total sent: {message_count}")
                else:
                    print("💤 Waiting 30 seconds due to error...")
                    time.sleep(30)
                    continue
                
                print(f"⏰ Next message in {interval_seconds} seconds...")
                
                # Countdown
                for i in range(interval_seconds):
                    if not self.is_running:
                        break
                    if i % 30 == 0:
                        remaining = interval_seconds - i
                        print(f"   ⏳ {remaining}s remaining...")
                    time.sleep(1)
                
            except KeyboardInterrupt:
                print("🛑 Stopped by user")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                time.sleep(30)

def main():
    print("🔐 E2EE FACEBOOK MESSENGER BOT")
    print("=" * 50)
    
    bot = E2EEFacebookMessenger()
    
    if not bot.token or not bot.target_user:
        print("❌ Setup incomplete. Please check token.txt and user_id.txt")
        return
    
    # Auto-start with 2 minutes interval
    bot.start_auto_encrypted_sending(interval_seconds=120)

if __name__ == "__main__":
    main()
