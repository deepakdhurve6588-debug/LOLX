import os

def setup_configuration():
    """Initial configuration setup करें"""
    print("🔧 E2EE MESSENGER SETUP")
    print("=" * 40)
    
    # Create config directory
    os.makedirs('config', exist_ok=True)
    
    # Facebook Token
    token = input("Enter Facebook Page Access Token: ").strip()
    with open('config/token.txt', 'w') as f:
        f.write(token)
    
    # Target User ID
    user_id = input("Enter Target Facebook User ID: ").strip()
    with open('config/user_id.txt', 'w') as f:
        f.write(user_id)
    
    # Messages
    print("\n📝 Enter messages (one per line, Ctrl+D to finish):")
    messages = []
    while True:
        try:
            line = input()
            if line.strip():
                messages.append(line.strip())
        except EOFError:
            break
    
    with open('config/messages.txt', 'w', encoding='utf-8') as f:
        for msg in messages:
            f.write(msg + '\n')
    
    print(f"✅ Setup complete! {len(messages)} messages saved.")

if __name__ == "__main__":
    setup_configuration()
