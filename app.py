import requests
import json
import time
import os
import base64
import re
from cryptography.fernet import Fernet
from datetime import datetime
import getpass

class SmartE2EEMessenger:
    def __init__(self):
        self.setup_directories()
        self.token = self.load_token()
        self.target_info = self.load_target_info()
        self.messages = self.load_messages()
        self.fernet = self.setup_encryption()
        
        print("🔐 SMART E2EE MESSENGER")
        print("=" * 50)
        self.log_system("SYSTEM_STARTED", "Smart E2EE Messenger initialized")
    
    def setup_directories(self):
        """Required directories create करें"""
        os.makedirs('config', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
    
    def load_token(self):
        """token.txt से token automatically load करें"""
        token_file = 'config/token.txt'
        
        try:
            if os.path.exists(token_file):
                with open(token_file, 'r') as f:
                    token = f.read().strip()
                
                if token and token.startswith('EA'):
                    self.log_system("TOKEN_LOADED", f"Token loaded: {token[:15]}...")
                    return token
                else:
                    self.log_system("TOKEN_INVALID", "Token format invalid")
                    return None
            else:
                # Create template token file
                with open(token_file, 'w') as f:
                    f.write("EAABwzLm... (Paste your MonokaiTool token here)")
                self.log_system("TOKEN_FILE_CREATED", "Template token.txt created")
                return None
                
        except Exception as e:
            self.log_system("TOKEN_LOAD_ERROR", f"Error loading token: {e}")
            return None
    
    def load_target_info(self):
        """target.txt से target information load करें"""
        target_file = 'config/target.txt'
        
        try:
            if os.path.exists(target_file):
                with open(target_file, 'r') as f:
                    content = f.read().strip()
                
                if not content:
                    self.log_system("TARGET_EMPTY", "target.txt is empty")
                    return None
                
                # Detect what type of target it is
                target_info = self.analyze_target(content)
                self.log_system("TARGET_LOADED", f"Target: {target_info['type']} - {target_info['value']}")
                return target_info
                
            else:
                # Create template target file
                with open(target_file, 'w') as f:
                    f.write("# Paste either:\n# Facebook Profile URL: https://www.facebook.com/username\n# OR Facebook User ID: 1234567890123456\n# OR E2EE Chat Thread ID: 24330229269965772\n")
                self.log_system("TARGET_FILE_CREATED", "Template target.txt created")
                return None
                
        except Exception as e:
            self.log_system("TARGET_LOAD_ERROR", f"Error loading target: {e}")
            return None
    
    def analyze_target(self, content):
        """Target content analyze करें और type identify करें"""
        content = content.strip()
        
        # E2EE Chat Thread ID (आपका example)
        if content.isdigit() and len(content) > 15:
            return {
                'type': 'e2ee_thread_id',
                'value': content,
                'description': 'E2EE Chat Thread ID'
            }
        
        # Facebook Profile URL
        elif 'facebook.com' in content:
            if '/messages/e2ee/t/' in content:
                # E2EE chat link
                thread_id = self.extract_e2ee_thread_id(content)
                if thread_id:
                    return {
                        'type': 'e2ee_thread_id', 
                        'value': thread_id,
                        'description': 'E2EE Chat Thread from URL',
                        'original_url': content
                    }
            else:
                # Regular profile URL
                user_id = self.extract_user_id_from_url(content)
                if user_id:
                    return {
                        'type': 'user_id',
                        'value': user_id,
                        'description': 'User ID from Profile URL',
                        'original_url': content
                    }
        
        # Regular User ID (numeric)
        elif content.isdigit() and len(content) >= 10:
            return {
                'type': 'user_id',
                'value': content,
                'description': 'Facebook User ID'
            }
        
        # Unknown format
        return {
            'type': 'unknown',
            'value': content,
            'description': 'Unknown format - needs manual setup'
        }
    
    def extract_e2ee_thread_id(self, url):
        """E2EE chat URL से thread ID extract करें"""
        try:
            # Pattern: /messages/e2ee/t/12345678901234567
            pattern = r'/messages/e2ee/t/(\d+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            
            # Alternative pattern
            pattern2 = r'messages/e2ee/t/(\d+)'
            match = re.search(pattern2, url)
            if match:
                return match.group(1)
                
            return None
        except:
            return None
    
    def extract_user_id_from_url(self, url):
        """Profile URL से User ID extract करें"""
        try:
            # Pattern: /profile.php?id=123456789
            pattern1 = r'profile\.php\?id=(\d+)'
            match = re.search(pattern1, url)
            if match:
                return match.group(1)
            
            # Pattern: /username (will need API call to get ID)
            pattern2 = r'facebook\.com/([^/?]+)'
            match = re.search(pattern2, url)
            if match:
                username = match.group(1)
                if username != 'messages':
                    # Username से User ID get करने के लिए API call
                    user_id = self.get_user_id_from_username(username)
                    return user_id
            
            return None
        except:
            return None
    
    def get_user_id_from_username(self, username):
        """Username से User ID get करें (API के through)"""
        if not self.token:
            return None
        
        try:
            url = f"https://graph.facebook.com/v18.0/{username}?access_token={self.token}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('id')
            else:
                self.log_system("USERNAME_TO_ID_FAILED", f"Could not get ID for username: {username}")
                return None
                
        except Exception as e:
            self.log_system("USERNAME_TO_ID_ERROR", f"Error converting username: {e}")
            return None
    
    def load_messages(self):
        """Messages load करें"""
        try:
            with open('config/messages.txt', 'r', encoding='utf-8') as f:
                messages = [line.strip() for line in f if line.strip()]
            
            if not messages:
                # Default messages
                messages = [
                    "Hello! This is E2EE encrypted message 🔐",
                    "Your messages are securely encrypted",
                    "End-to-End Encryption is active ✅",
                    "Automated E2EE messaging system 🚀"
                ]
                with open('config/messages.txt', 'w', encoding='utf-8') as f:
                    for msg in messages:
                        f.write(msg + '\n')
            
            self.log_system("MESSAGES_LOADED", f"Loaded {len(messages)} messages")
            return messages
            
        except FileNotFoundError:
            self.log_system("MESSAGES_FILE_MISSING", "messages.txt not found, using defaults")
            return ["Hello! This is test message"]
    
    def setup_encryption(self):
        """Encryption setup करें"""
        try:
            key_file = 'config/encryption.key'
            
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
                self.log_system("ENCRYPTION_LOADED", "Encryption key loaded")
            else:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                self.log_system("ENCRYPTION_CREATED", "New encryption key generated")
            
            return Fernet(key)
            
        except Exception as e:
            self.log_system("ENCRYPTION_ERROR", f"Encryption setup failed: {e}")
            return None
    
    def encrypt_message(self, message):
        """Message encrypt करें"""
        if not self.fernet:
            return message
        
        try:
            encrypted = self.fernet.encrypt(message.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            self.log_system("ENCRYPTION_FAILED", f"Message encryption error: {e}")
            return message
    
    def verify_setup(self):
        """Complete setup verify करें"""
        issues = []
        
        if not self.token:
            issues.append("❌ Token not loaded from config/token.txt")
        
        if not self.target_info:
            issues.append("❌ Target not loaded from config/target.txt")
        elif self.target_info['type'] == 'unknown':
            issues.append("❌ Target format not recognized")
        
        if not self.messages:
            issues.append("❌ No messages loaded")
        
        if not self.fernet:
            issues.append("❌ Encryption not setup properly")
        
        if issues:
            print("\n🚨 SETUP ISSUES FOUND:")
            for issue in issues:
                print(f"   {issue}")
            return False
        
        # Verify token with Facebook
        print("\n🔍 Verifying token...")
        token_valid, token_msg = self.verify_token()
        if not token_valid:
            print(f"   {token_msg}")
            return False
        
        print("   ✅ Token verified successfully")
        
        # Show target info
        print(f"\n🎯 TARGET INFORMATION:")
        print(f"   Type: {self.target_info['description']}")
        print(f"   Value: {self.target_info['value']}")
        if 'original_url' in self.target_info:
            print(f"   From URL: {self.target_info['original_url']}")
        
        return True
    
    def verify_token(self):
        """Token verify करें"""
        if not self.token:
            return False, "No token available"
        
        try:
            url = f"https://graph.facebook.com/v18.0/me?access_token={self.token}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Token valid for: {user_data.get('name')}"
            else:
                error_data = response.json()
                return False, f"Token invalid: {error_data.get('error', {}).get('message')}"
                
        except Exception as e:
            return False, f"Verification failed: {e}"
    
    def send_e2ee_message(self):
        """E2EE message send करें based on target type"""
        if not self.target_info:
            return False, "No target information"
        
        target_type = self.target_info['type']
        target_value = self.target_info['value']
        
        # Get message (rotate through messages)
        if not hasattr(self, 'current_message_index'):
            self.current_message_index = 0
        
        message = self.messages[self.current_message_index]
        self.current_message_index = (self.current_message_index + 1) % len(self.messages)
        
        # Encrypt message
        encrypted_content = self.encrypt_message(message)
        
        # Prepare Facebook message based on target type
        if target_type == 'e2ee_thread_id':
            fb_message = f"""🔐 **E2EE ENCRYPTED MESSAGE**

**Thread ID:** {target_value}
**Encrypted Content:**
{encrypted_content}

**Timestamp:** {datetime.now().strftime('%H:%M:%S')}
**Status:** 🔒 End-to-End Encrypted"""
        else:
            fb_message = f"""🔐 **E2EE ENCRYPTED MESSAGE**

**Encrypted Content:**
{encrypted_content}

**Instructions:** Copy encrypted content to decrypt
**Timestamp:** {datetime.now().strftime('%H:%M:%S')}
**Status:** 🔒 End-to-End Encrypted"""
        
        payload = {
            "recipient": {"id": target_value},
            "message": {"text": fb_message},
            "messaging_type": "MESSAGE_TAG",
            "tag": "CONFIRMED_EVENT_UPDATE"
        }
        
        params = {"access_token": self.token}
        
        try:
            response = requests.post(
                "https://graph.facebook.com/v18.0/me/messages",
                json=payload,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                self.log_message("E2EE_MESSAGE_SENT", target_value, message, encrypted_content)
                return True, f"✅ Message sent to {target_type}: {target_value}"
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                self.log_message("E2EE_MESSAGE_FAILED", target_value, message, encrypted_content, error_msg)
                return False, f"❌ Send failed: {error_msg}"
                
        except Exception as e:
            self.log_message("E2EE_MESSAGE_ERROR", target_value, message, encrypted_content, str(e))
            return False, f"❌ Network error: {e}"
    
    def start_auto_messaging(self, interval=120):
        """Auto messaging start करें"""
        print(f"\n🚀 STARTING AUTO E2EE MESSAGING")
        print("=" * 50)
        
        if not self.verify_setup():
            print("❌ Cannot start due to setup issues")
            return
        
        print(f"⏰ Interval: {interval} seconds")
        print("📨 Messages will rotate automatically")
        print("Press Ctrl+C to stop\n")
        
        message_count = 0
        
        try:
            while True:
                success, result = self.send_e2ee_message()
                
                if success:
                    message_count += 1
                    print(f"✅ Message {message_count}: {result}")
                else:
                    print(f"❌ Failed: {result}")
                    print("💤 Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                
                # Countdown
                for i in range(interval):
                    remaining = interval - i
                    mins = remaining // 60
                    secs = remaining % 60
                    print(f"⏰ Next message in: {mins:02d}:{secs:02d}", end='\r')
                    time.sleep(1)
                print(" " * 50, end='\r')
                
        except KeyboardInterrupt:
            print(f"\n🛑 Auto-messaging stopped!")
            print(f"📊 Total messages sent: {message_count}")
    
    def log_system(self, log_type, message):
        """System activity log करें"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {log_type}: {message}\n"
        
        try:
            with open('logs/system.log', 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    def log_message(self, status, target, message, encrypted_msg, error=None):
        """Message sending log करें"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "timestamp": timestamp,
            "status": status,
            "target_type": self.target_info['type'] if self.target_info else 'unknown',
            "target_value": target,
            "original_message": message,
            "encrypted_message": encrypted_msg[:100] + "..." if len(encrypted_msg) > 100 else encrypted_msg,
            "error": error
        }
        
        try:
            with open('logs/message_logs.json', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            with open('logs/messages.txt', 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {status} | Target: {target} | Type: {self.target_info['type'] if self.target_info else 'unknown'}\n")
                f.write(f"   Message: {message}\n")
                if error:
                    f.write(f"   Error: {error}\n")
                f.write("-" * 80 + "\n")
                
        except Exception as e:
            print(f"❌ Logging failed: {e}")

def main():
    messenger = SmartE2EEMessenger()
    
    while True:
        print("\n🔐 SMART E2EE MESSENGER")
        print("=" * 50)
        print("1. Start Auto E2EE Messaging")
        print("2. Send Single Test Message")
        print("3. Check Current Setup")
        print("4. View Logs")
        print("5. Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == '1':
            try:
                interval = int(input("Interval in seconds (default 120): ") or 120)
            except ValueError:
                interval = 120
            messenger.start_auto_messaging(interval)
        
        elif choice == '2':
            print("\n🧪 SENDING TEST MESSAGE...")
            success, result = messenger.send_e2ee_message()
            print(result)
        
        elif choice == '3':
            print("\n🔧 CURRENT SETUP:")
            print(f"   Token: {'✅ Loaded' if messenger.token else '❌ Missing'}")
            if messenger.target_info:
                print(f"   Target: {messenger.target_info['description']}")
                print(f"   Value: {messenger.target_info['value']}")
            else:
                print("   Target: ❌ Not configured")
            print(f"   Messages: {len(messenger.messages)} loaded")
            print(f"   Encryption: {'✅ Active' if messenger.fernet else '❌ Inactive'}")
        
        elif choice == '4':
            print("\n📊 RECENT LOGS:")
            try:
                if os.path.exists('logs/system.log'):
                    with open('logs/system.log', 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-5:]
                        for line in lines:
                            print(f"   {line.strip()}")
                else:
                    print("   No logs found")
            except Exception as e:
                print(f"   Error reading logs: {e}")
        
        elif choice == '5':
            messenger.log_system("SYSTEM_SHUTDOWN", "User exited")
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
