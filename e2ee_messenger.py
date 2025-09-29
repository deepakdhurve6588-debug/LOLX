import requests
import json
import time
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime
import getpass

class E2EELoginSystem:
    def __init__(self):
        self.users_file = 'data/users.json'
        self.setup_directories()
    
    def setup_directories(self):
        """Required directories create करें"""
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('keys', exist_ok=True)
    
    def hash_password(self, password):
        """Password को securely hash करें"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self):
        """Users data load करें"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_users(self, users):
        """Users data save करें"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=4)
    
    def register_user(self, email, password):
        """New user register करें"""
        users = self.load_users()
        
        if email in users:
            return False, "User already exists"
        
        users[email] = {
            'password_hash': self.hash_password(password),
            'registered_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        self.save_users(users)
        return True, "Registration successful"
    
    def login_user(self, email, password):
        """User login करें"""
        users = self.load_users()
        
        if email not in users:
            return False, "User not found"
        
        user_data = users[email]
        
        if user_data['password_hash'] != self.hash_password(password):
            return False, "Invalid password"
        
        # Update last login
        user_data['last_login'] = datetime.now().isoformat()
        self.save_users(users)
        
        return True, "Login successful"

class E2EEMessenger:
    def __init__(self):
        self.setup_directories()
        self.login_system = E2EELoginSystem()
        self.current_user = None
        
        # Facebook configuration
        self.token = None
        self.target_user = None
        self.messages = []
        
        # E2EE Encryption
        self.fernet = None
    
    def setup_directories(self):
        """Required directories create करें"""
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('keys', exist_ok=True)
        os.makedirs('config', exist_ok=True)
    
    def generate_encryption_key(self, password, salt=None):
        """Encryption key generate करें"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def setup_user_encryption(self, email, password):
        """User के लिए encryption setup करें"""
        user_key_file = f'keys/{email}.key'
        user_salt_file = f'keys/{email}.salt'
        
        if os.path.exists(user_key_file) and os.path.exists(user_salt_file):
            # Existing user - load key
            with open(user_salt_file, 'rb') as f:
                salt = f.read()
            key, _ = self.generate_encryption_key(password, salt)
            with open(user_key_file, 'rb') as f:
                stored_key = f.read()
            
            if key != stored_key:
                return False, "Invalid password for decryption"
            
            self.fernet = Fernet(key)
            return True, "Encryption setup successful"
        
        else:
            # New user - create key
            key, salt = self.generate_encryption_key(password)
            
            with open(user_key_file, 'wb') as f:
                f.write(key)
            with open(user_salt_file, 'wb') as f:
                f.write(salt)
            
            self.fernet = Fernet(key)
            return True, "New encryption key created"
    
    def encrypt_message(self, message):
        """Message encrypt करें"""
        if not self.fernet:
            return message
        
        encrypted = self.fernet.encrypt(message.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_message(self, encrypted_message):
        """Message decrypt करें"""
        if not self.fernet:
            return encrypted_message
        
        try:
            decrypted = self.fernet.decrypt(base64.urlsafe_b64decode(encrypted_message))
            return decrypted.decode()
        except Exception as e:
            return f"❌ Decryption failed: {e}"
    
    def log_activity(self, activity_type, details):
        """Activity log करें"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {activity_type}: {details}\n"
        
        try:
            with open('logs/activity.log', 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    def load_facebook_config(self):
        """Facebook configuration load करें"""
        try:
            with open('config/token.txt', 'r') as f:
                self.token = f.read().strip()
            with open('config/user_id.txt', 'r') as f:
                self.target_user = f.read().strip()
            with open('config/messages.txt', 'r', encoding='utf-8') as f:
                self.messages = [line.strip() for line in f if line.strip()]
            
            return True
        except FileNotFoundError as e:
            print(f"❌ Configuration missing: {e}")
            return False
    
    def verify_facebook_token(self):
        """Facebook token verify करें"""
        if not self.token:
            return False, "Token not loaded"
        
        try:
            url = f"https://graph.facebook.com/v18.0/me?access_token={self.token}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Token valid - {user_data.get('name')}"
            else:
                error_data = response.json()
                return False, error_data.get('error', {}).get('message', 'Unknown error')
                
        except Exception as e:
            return False, f"Verification failed: {e}"
    
    def send_encrypted_message(self, message):
        """Encrypted message Facebook पर send करें"""
        if not self.token or not self.target_user:
            return False, "Configuration missing"
        
        # Message encrypt करें
        encrypted_msg = self.encrypt_message(message)
        
        # Facebook format
        fb_message = f"🔐 E2EE ENCRYPTED MESSAGE\n{encrypted_msg}\n\n💡 Decrypt using your E2EE key\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        payload = {
            "recipient": {"id": self.target_user},
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
                self.log_activity("MESSAGE_SENT", f"To: {self.target_user} | Encrypted: {encrypted_msg[:30]}...")
                return True, "Message sent successfully"
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                self.log_activity("MESSAGE_FAILED", error_msg)
                return False, error_msg
                
        except Exception as e:
            self.log_activity("NETWORK_ERROR", str(e))
            return False, f"Network error: {e}"
    
    def send_test_message(self):
        """Test message send करें"""
        test_msg = "🧪 Test message from E2EE Messenger - " + datetime.now().strftime("%H:%M:%S")
        return self.send_encrypted_message(test_msg)
    
    def start_auto_messaging(self, interval=120):
        """Auto messaging start करें"""
        if not self.messages:
            return False, "No messages loaded"
        
        print(f"🚀 Starting auto-messaging (Interval: {interval}s)")
        
        message_count = 0
        current_index = 0
        
        try:
            while True:
                message = self.messages[current_index]
                success, result = self.send_encrypted_message(message)
                
                if success:
                    message_count += 1
                    print(f"✅ Message {message_count}: {message}")
                else:
                    print(f"❌ Failed: {result}")
                    time.sleep(60)  # Error के बाद wait
                    continue
                
                current_index = (current_index + 1) % len(self.messages)
                
                # Countdown
                for i in range(interval):
                    print(f"⏰ Next in {interval - i}s...", end='\r')
                    time.sleep(1)
                print(" " * 50, end='\r')
                
        except KeyboardInterrupt:
            return True, f"Auto-messaging stopped. Total sent: {message_count}"
    
    def decrypt_received_message(self):
        """Received message decrypt करें"""
        print("\n🔓 MESSAGE DECRYPTION")
        encrypted_msg = input("Paste encrypted message: ").strip()
        
        if not encrypted_msg:
            return False, "No message provided"
        
        # Extract encrypted content
        if "E2EE ENCRYPTED MESSAGE" in encrypted_msg:
            lines = encrypted_msg.split('\n')
            for i, line in enumerate(lines):
                if line.strip() and "E2EE ENCRYPTED MESSAGE" not in line and "🔐" not in line and "💡" not in line and "⏰" not in line:
                    encrypted_content = line.strip()
                    decrypted = self.decrypt_message(encrypted_content)
                    return True, decrypted
        
        # Direct encrypted message
        decrypted = self.decrypt_message(encrypted_msg)
        return True, decrypted

def main():
    messenger = E2EEMessenger()
    
    print("🔐 E2EE MESSENGER SYSTEM")
    print("=" * 50)
    
    while True:
        if not messenger.current_user:
            # Login/Register Menu
            print("\n🔐 AUTHENTICATION")
            print("1. Login")
            print("2. Register")
            print("3. Exit")
            
            choice = input("Choose option: ").strip()
            
            if choice == '1':
                email = input("Email: ").strip().lower()
                password = getpass.getpass("Password: ")
                
                success, message = messenger.login_user.login_user(email, password)
                if success:
                    # Setup encryption
                    enc_success, enc_message = messenger.setup_user_encryption(email, password)
                    if enc_success:
                        messenger.current_user = email
                        print(f"✅ {message} | {enc_message}")
                        messenger.log_activity("USER_LOGIN", f"User: {email}")
                    else:
                        print(f"❌ {enc_message}")
                else:
                    print(f"❌ {message}")
            
            elif choice == '2':
                email = input("Email: ").strip().lower()
                password = getpass.getpass("Password: ")
                confirm_password = getpass.getpass("Confirm Password: ")
                
                if password != confirm_password:
                    print("❌ Passwords do not match")
                    continue
                
                if len(password) < 6:
                    print("❌ Password must be at least 6 characters")
                    continue
                
                success, message = messenger.login_system.register_user(email, password)
                print(f"✅ {message}" if success else f"❌ {message}")
            
            elif choice == '3':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice")
        
        else:
            # Main Menu (Authenticated)
            print(f"\n👤 Welcome, {messenger.current_user}")
            print("=" * 50)
            print("1. Load Facebook Config")
            print("2. Verify Token")
            print("3. Send Test Message")
            print("4. Start Auto-Messaging")
            print("5. Decrypt Message")
            print("6. Logout")
            
            choice = input("Choose option: ").strip()
            
            if choice == '1':
                if messenger.load_facebook_config():
                    print("✅ Facebook configuration loaded")
                else:
                    print("❌ Failed to load configuration")
            
            elif choice == '2':
                success, message = messenger.verify_facebook_token()
                print(f"✅ {message}" if success else f"❌ {message}")
            
            elif choice == '3':
                success, message = messenger.send_test_message()
                print(f"✅ {message}" if success else f"❌ {message}")
            
            elif choice == '4':
                try:
                    interval = int(input("Interval in seconds (default 120): ") or 120)
                except ValueError:
                    interval = 120
                
                success, message = messenger.start_auto_messaging(interval)
                print(f"✅ {message}" if success else f"❌ {message}")
            
            elif choice == '5':
                success, message = messenger.decrypt_received_message()
                if success:
                    print(f"🔓 Decrypted: {message}")
                else:
                    print(f"❌ {message}")
            
            elif choice == '6':
                messenger.log_activity("USER_LOGOUT", f"User: {messenger.current_user}")
                messenger.current_user = None
                messenger.fernet = None
                print("✅ Logged out successfully")
            
            else:
                print("❌ Invalid choice")

if __name__ == "__main__":
    main()
