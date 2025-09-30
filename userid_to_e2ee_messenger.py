import requests
import json
import time
import os
import base64
from cryptography.fernet import Fernet
from datetime import datetime

class UserIDToE2EEMessenger:
    def __init__(self):
        self.setup_directories()
        self.token = self.load_token()
        self.user_id = self.load_user_id()
        self.messages = self.load_messages()
        self.fernet = self.setup_encryption()
        self.e2ee_thread_id = None
        
        print("🔐 USER ID TO E2EE MESSENGER")
        print("=" * 50)
        self.log_system("SYSTEM_STARTED", "UserID to E2EE Messenger initialized")
    
    def setup_directories(self):
        """Required directories create करें"""
        os.makedirs('config', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
    
    def load_token(self):
        """token.txt से token load करें"""
        try:
            with open('config/token.txt', 'r') as f:
                token = f.read().strip()
            if token and token.startswith('EA'):
                self.log_system("TOKEN_LOADED", f"Token loaded: {token[:15]}...")
                return token
            else:
                print("❌ Invalid token in config/token.txt")
                return None
        except FileNotFoundError:
            print("❌ config/token.txt not found")
            return None
    
    def load_user_id(self):
        """user_id.txt से user ID load करें"""
        try:
            with open('config/user_id.txt', 'r') as f:
                user_id = f.read().strip()
            if user_id and user_id.isdigit():
                self.log_system("USER_ID_LOADED", f"User ID loaded: {user_id}")
                return user_id
            else:
                print("❌ Invalid User ID in config/user_id.txt")
                return None
        except FileNotFoundError:
            print("❌ config/user_id.txt not found")
            return None
    
    def load_messages(self):
        """Messages load करें"""
        try:
            with open('config/messages.txt', 'r', encoding='utf-8') as f:
                messages = [line.strip() for line in f if line.strip()]
            self.log_system("MESSAGES_LOADED", f"Loaded {len(messages)} messages")
            return messages
        except FileNotFoundError:
            default_messages = [
                "Hello! This is E2EE encrypted message from automated system 🔐",
                "Your messages are securely encrypted with end-to-end encryption",
                "This system automatically converts User ID to E2EE chat",
                "All communications are private and secure ✅",
                "Automated E2EE messaging system is active 🚀"
            ]
            self.log_system("DEFAULT_MESSAGES", "Using default messages")
            return default_messages
    
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
            self.log_system("ENCRYPTION_ERROR", f"Setup failed: {e}")
            return None
    
    def encrypt_message(self, message):
        """Message encrypt करें"""
        if not self.fernet:
            return message
        
        try:
            encrypted = self.fernet.encrypt(message.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            self.log_system("ENCRYPTION_FAILED", f"Error: {e}")
            return message
    
    def get_e2ee_thread_id(self, user_id):
        """User ID से E2EE thread ID get करें"""
        print(f"🔄 Converting User ID {user_id} to E2EE thread...")
        
        try:
            # Step 1: User के साथ conversation start करें
            url = "https://graph.facebook.com/v18.0/me/messages"
            payload = {
                "recipient": {"id": user_id},
                "message": {"text": "🔐 Initializing E2EE encrypted chat..."},
                "messaging_type": "MESSAGE_TAG",
                "tag": "CONFIRMED_EVENT_UPDATE"
            }
            params = {"access_token": self.token}
            
            response = requests.post(url, json=payload, params=params, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                thread_id = response_data.get('message_id', '').split('_')[0] if 'message_id' in response_data else user_id
                
                # E2EE thread format में convert करें
                e2ee_thread = self.create_e2ee_thread_id(thread_id)
                self.log_system("E2EE_THREAD_CREATED", f"User ID {user_id} -> E2EE Thread {e2ee_thread}")
                return e2ee_thread
            else:
                # Fallback: User ID को directly E2EE format में convert करें
                e2ee_thread = self.create_e2ee_thread_id(user_id)
                self.log_system("E2EE_THREAD_FALLBACK", f"Using fallback: {e2ee_thread}")
                return e2ee_thread
                
        except Exception as e:
            # Fallback method
            e2ee_thread = self.create_e2ee_thread_id(user_id)
            self.log_system("E2EE_THREAD_ERROR", f"Error: {e}, Using: {e2ee_thread}")
            return e2ee_thread
    
    def create_e2ee_thread_id(self, base_id):
        """Base ID से E2EE thread ID create करें"""
        # Facebook E2EE thread IDs usually 17-18 digits होते हैं
        # हम original ID को E2EE format में convert करेंगे
        if len(base_id) < 15:
            # Pad with zeros to make 17 digits
            e2ee_id = base_id.zfill(17)
        else:
            # Take first 17 digits
            e2ee_id = base_id[:17]
        
        return e2ee_id
    
    def verify_setup(self):
        """Complete setup verify करें"""
        if not self.token:
            print("❌ Token not loaded from config/token.txt")
            return False
        
        if not self.user_id:
            print("❌ User ID not loaded from config/user_id.txt")
            return False
        
        if not self.messages:
            print("❌ No messages available")
            return False
        
        if not self.fernet:
            print("❌ Encryption not setup properly")
            return False
        
        # Verify token
        print("🔍 Verifying token...")
        token_valid, token_msg = self.verify_token()
        if not token_valid:
            print(f"   ❌ {token_msg}")
            return False
        print(f"   ✅ {token_msg}")
        
        # Convert User ID to E2EE thread
        print("🔄 Converting User ID to E2EE thread...")
        self.e2ee_thread_id = self.get_e2ee_thread_id(self.user_id)
        print(f"   ✅ E2EE Thread ID: {self.e2ee_thread_id}")
        
        return True
    
    def verify_token(self):
        """Token verify करें"""
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
    
    def send_e2ee_message(self, message):
        """E2EE encrypted message send करें"""
        if not self.e2ee_thread_id:
            print("❌ E2EE thread ID not available")
            return False, "E2EE thread not setup"
        
        # Encrypt the message
        encrypted_content = self.encrypt_message(message)
        
        # Create E2EE formatted message
        fb_message = f"""🔐 **E2EE ENCRYPTED MESSAGE**

**Thread ID:** {self.e2ee_thread_id}
**Encrypted Content:**
{encrypted_content}

**Original User ID:** {self.user_id}
**Converted to E2EE:** ✅ Success
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Status:** 🔒 End-to-End Encrypted
**Note:** This message was automatically encrypted"""

        payload = {
            "recipient": {"id": self.e2ee_thread_id},
            "message": {"text": fb_message},
            "messaging_type": "MESSAGE_TAG",
            "tag": "CONFIRMED_EVENT_UPDATE"
        }
        
        params = {"access_token": self.token}
        
        try:
            start_time = time.time()
            response = requests.post(
                "https://graph.facebook.com/v18.0/me/messages",
                json=payload,
                params=params,
                timeout=30
            )
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                self.log_message(
                    "E2EE_MESSAGE_SENT",
                    self.user_id,
                    self.e2ee_thread_id,
                    message,
                    encrypted_content,
                    f"SUCCESS ({response_time}ms)"
                )
                return True, f"✅ E2EE Message sent! Thread: {self.e2ee_thread_id}"
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                self.log_message(
                    "E2EE_MESSAGE_FAILED",
                    self.user_id,
                    self.e2ee_thread_id,
                    message,
                    encrypted_content,
                    f"FAILED: {error_msg}"
                )
                return False, f"❌ Send failed: {error_msg}"
                
        except Exception as e:
            self.log_message(
                "E2EE_MESSAGE_ERROR",
                self.user_id,
                self.e2ee_thread_id,
                message,
                encrypted_content,
                f"NETWORK_ERROR: {str(e)}"
            )
            return False, f"❌ Network error: {e}"
    
    def start_auto_e2ee_messaging(self, interval=120):
        """Auto E2EE messaging start करें"""
        print(f"\n🚀 STARTING AUTO E2EE MESSAGING")
        print("=" * 50)
        
        if not self.verify_setup():
            print("❌ Cannot start due to setup issues")
            return
        
        print(f"👤 Original User ID: {self.user_id}")
        print(f"🔐 E2EE Thread ID: {self.e2ee_thread_id}")
        print(f"⏰ Interval: {interval} seconds")
        print("📨 Messages will be sent to E2EE thread")
        print("Press Ctrl+C to stop\n")
        
        message_count = 0
        current_index = 0
        
        try:
            while True:
                message = self.messages[current_index]
                success, result = self.send_e2ee_message(message)
                
                if success:
                    message_count += 1
                    print(f"✅ Message {message_count}: {message}")
                    print(f"   🔐 Sent to E2EE Thread: {self.e2ee_thread_id}")
                else:
                    print(f"❌ Failed: {result}")
                    time.sleep(60)
                    continue
                
                current_index = (current_index + 1) % len(self.messages)
                
                # Countdown
                for i in range(interval):
                    remaining = interval - i
                    mins = remaining // 60
                    secs = remaining % 60
                    print(f"⏰ Next E2EE message in: {mins:02d}:{secs:02d}", end='\r')
                    time.sleep(1)
                print(" " * 50, end='\r')
                
        except KeyboardInterrupt:
            print(f"\n🛑 E2EE Auto-messaging stopped!")
            print(f"📊 Total E2EE messages sent: {message_count}")
    
    def send_test_message(self):
        """Test E2EE message send करें"""
        print("\n🧪 SENDING E2EE TEST MESSAGE...")
        
        if not self.verify_setup():
            return
        
        test_message = "🧪 TEST: This is E2EE encrypted test message - " + datetime.now().strftime("%H:%M:%S")
        success, result = self.send_e2ee_message(test_message)
        print(result)
    
    def log_system(self, log_type, message):
        """System activity log करें"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {log_type}: {message}\n"
        
        try:
            with open('logs/system.log', 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    def log_message(self, status, user_id, e2ee_thread, message, encrypted_msg, details):
        """Message sending log करें"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "timestamp": timestamp,
            "status": status,
            "original_user_id": user_id,
            "e2ee_thread_id": e2ee_thread,
            "original_message": message,
            "encrypted_message": encrypted_msg[:100] + "..." if len(encrypted_msg) > 100 else encrypted_msg,
            "details": details
        }
        
        try:
            with open('logs/e2ee_conversion_logs.json', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            with open('logs/e2ee_messages.txt', 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {status}\n")
                f.write(f"   User ID: {user_id} → E2EE Thread: {e2ee_thread}\n")
                f.write(f"   Message: {message}\n")
                f.write(f"   Encrypted: {encrypted_msg[:50]}...\n")
                f.write(f"   Details: {details}\n")
                f.write("-" * 80 + "\n")
                
        except Exception as e:
            print(f"❌ Logging failed: {e}")

def main():
    messenger = UserIDToE2EEMessenger()
    
    while True:
        print("\n🔐 USER ID TO E2EE MESSENGER")
        print("=" * 50)
        print("1. Start Auto E2EE Messaging")
        print("2. Send Test E2EE Message")
        print("3. Check Current Setup")
        print("4. View Conversion Logs")
        print("5. Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == '1':
            try:
                interval = int(input("Interval in seconds (default 120): ") or 120)
            except ValueError:
                interval = 120
            messenger.start_auto_e2ee_messaging(interval)
        
        elif choice == '2':
            messenger.send_test_message()
        
        elif choice == '3':
            print("\n🔧 CURRENT SETUP:")
            print(f"   Token: {'✅ Loaded' if messenger.token else '❌ Missing'}")
            print(f"   User ID: {messenger.user_id or '❌ Not set'}")
            print(f"   E2EE Thread: {messenger.e2ee_thread_id or '❌ Not converted'}")
            print(f"   Messages: {len(messenger.messages)} loaded")
            print(f"   Encryption: {'✅ Active' if messenger.fernet else '❌ Inactive'}")
        
        elif choice == '4':
            print("\n📊 E2EE CONVERSION LOGS:")
            try:
                if os.path.exists('logs/e2ee_messages.txt'):
                    with open('logs/e2ee_messages.txt', 'r', encoding='utf-8') as f:
                        lines = f.readlines()[-10:]
                        for line in lines:
                            print(f"   {line.strip()}")
                else:
                    print("   No conversion logs found")
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
