import os
import base64
from cryptography.fernet import Fernet
from datetime import datetime

class E2EEReceiver:
    def __init__(self):
        self.encryption_key = self.load_encryption_key()
        self.fernet = Fernet(self.encryption_key) if self.encryption_key else None
    
    def load_encryption_key(self):
        """Encryption key load करें"""
        try:
            if os.path.exists('encryption_key.txt'):
                with open('encryption_key.txt', 'rb') as f:
                    return f.read()
            else:
                print("❌ encryption_key.txt not found. Run main.py first.")
                return None
        except Exception as e:
            print(f"❌ Error loading key: {e}")
            return None
    
    def decrypt_message(self, encrypted_message):
        """Message decrypt करें"""
        if not self.fernet:
            return "❌ Decryption not available"
        
        try:
            # Facebook format से encrypted content extract करें
            if "ENCRYPTED_MESSAGE_START" in encrypted_message:
                lines = encrypted_message.split('\n')
                for i, line in enumerate(lines):
                    if "ENCRYPTED_MESSAGE_START" in line and i+1 < len(lines):
                        encrypted_content = lines[i+1].strip()
                        decrypted = self.fernet.decrypt(base64.urlsafe_b64decode(encrypted_content))
                        return decrypted.decode()
            
            # Direct encrypted message
            decrypted = self.fernet.decrypt(base64.urlsafe_b64decode(encrypted_message))
            return decrypted.decode()
            
        except Exception as e:
            return f"❌ Decryption failed: {e}"
    
    def log_decryption(self, encrypted, decrypted):
        """Decryption log करें"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] DECRYPTED: {decrypted}\n"
        
        try:
            with open('logs/decryption_log.txt', 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass

def monitor_messages():
    """Manual message monitoring के लिए"""
    receiver = E2EEReceiver()
    
    if not receiver.fernet:
        print("❌ Cannot start receiver. Encryption key missing.")
        return
    
    print("🔍 E2EE Message Receiver Started")
    print("="*50)
    print("Paste encrypted messages below (type 'exit' to stop):")
    print("- Paste full Facebook message with 🔐 tags")
    print("- Or paste just the encrypted string")
    print("="*50)
    
    while True:
        message = input("\n📥 Enter encrypted message: ").strip()
        
        if message.lower() in ['exit', 'quit', 'stop']:
            break
        
        if not message:
            continue
        
        decrypted = receiver.decrypt_message(message)
        print(f"🔓 Decrypted: {decrypted}")
        
        # Log successful decryptions
        if not decrypted.startswith("❌"):
            receiver.log_decryption(message[:50] + "..." if len(message) > 50 else message, decrypted)

if __name__ == "__main__":
    monitor_messages()
