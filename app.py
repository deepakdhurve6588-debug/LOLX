from flask import Flask, jsonify, request
import requests
import time
import threading
import os
from datetime import datetime

app = Flask(__name__)

class MessengerBot:
    def __init__(self):
        self.is_running = False
        self.sent_count = 0
        self.failed_count = 0
        self.cycle_count = 0
        self.load_config()
    
    def load_config(self):
        """Load configuration from files"""
        try:
            # Load token
            with open('config/token.txt', 'r') as f:
                self.token = f.read().strip()
            
            # Load targets
            with open('config/target.txt', 'r') as f:
                self.targets = [line.strip() for line in f.readlines() if line.strip()]
            
            # Load message
            with open('config/message.txt', 'r', encoding='utf-8') as f:
                self.message = f.read().strip()
            
            # Load time config
            with open('config/time.txt', 'r') as f:
                time_config = f.read().strip()
                if ':' in time_config:
                    delay_str, interval_str = time_config.split(':')
                    self.delay = int(delay_str)
                    self.interval = int(interval_str)
                else:
                    self.delay = int(time_config)
                    self.interval = 300
            
            print("✅ Config loaded successfully!")
            
        except Exception as e:
            print(f"❌ Config error: {e}")
    
    def send_message(self, user_id, message):
        """Send message to user"""
        try:
            url = "https://graph.facebook.com/v19.0/me/messages"
            
            data = {
                "recipient": {"id": user_id},
                "message": {"text": message},
                "messaging_type": "MESSAGE_TAG",
                "tag": "CONFIRMED_EVENT_UPDATE"
            }
            
            response = requests.post(
                url,
                json=data,
                params={"access_token": self.token},
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Sent to {user_id}")
                self.sent_count += 1
                return True
            else:
                print(f"❌ Failed to send to {user_id}")
                self.failed_count += 1
                return False
                
        except Exception as e:
            print(f"❌ Error sending to {user_id}: {e}")
            self.failed_count += 1
            return False
    
    def send_to_all(self):
        """Send message to all targets"""
        print(f"🚀 Sending to {len(self.targets)} targets...")
        
        for i, target in enumerate(self.targets, 1):
            print(f"📤 [{i}/{len(self.targets)}] Sending to: {target}")
            self.send_message(target, self.message)
            
            # Small delay between messages
            if i < len(self.targets):
                time.sleep(2)
        
        print(f"📊 Cycle completed: {self.sent_count} sent, {self.failed_count} failed")
    
    def start_bot(self):
        """Start the bot in background"""
        if self.is_running:
            return False
        
        self.is_running = True
        thread = threading.Thread(target=self._run_continuous)
        thread.daemon = True
        thread.start()
        return True
    
    def _run_continuous(self):
        """Run bot continuously in background"""
        print("🤖 Bot started!")
        
        # Initial delay
        if self.delay > 0:
            print(f"⏰ Waiting {self.delay} seconds...")
            time.sleep(self.delay)
        
        while self.is_running:
            self.cycle_count += 1
            print(f"\n🔄 CYCLE {self.cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            
            self.send_to_all()
            
            print(f"⏰ Waiting {self.interval} seconds...")
            
            # Check every second if still running
            for _ in range(self.interval):
                if not self.is_running:
                    break
                time.sleep(1)
        
        print("🛑 Bot stopped!")

# Global bot instance
bot = MessengerBot()

# Flask Routes
@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Messenger Bot</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .btn { padding: 10px 20px; margin: 10px; border: none; border-radius: 5px; cursor: pointer; }
                .start { background: #28a745; color: white; }
                .stop { background: #dc3545; color: white; }
                .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .running { background: #d4edda; color: #155724; }
                .stopped { background: #f8d7da; color: #721c24; }
            </style>
        </head>
        <body>
            <h1>🤖 Facebook Messenger Bot</h1>
            <div id="status" class="status stopped">Status: STOPPED</div>
            <button class="btn start" onclick="startBot()">▶ Start Bot</button>
            <button class="btn stop" onclick="stopBot()">⏹ Stop Bot</button>
            <button class="btn" onclick="getStats()">📊 Get Stats</button>
            
            <div id="stats" style="margin-top: 20px;"></div>
            
            <script>
                function updateStatus() {
                    fetch('/status')
                        .then(r => r.json())
                        .then(data => {
                            const statusDiv = document.getElementById('status');
                            statusDiv.className = data.is_running ? 'status running' : 'status stopped';
                            statusDiv.textContent = `Status: ${data.is_running ? 'RUNNING' : 'STOPPED'} | Cycles: ${data.cycle_count} | Sent: ${data.sent_count} | Failed: ${data.failed_count}`;
                        });
                }
                
                function startBot() {
                    fetch('/start', { method: 'POST' })
                        .then(r => r.json())
                        .then(data => {
                            alert(data.message);
                            updateStatus();
                        });
                }
                
                function stopBot() {
                    fetch('/stop', { method: 'POST' })
                        .then(r => r.json())
                        .then(data => {
                            alert(data.message);
                            updateStatus();
                        });
                }
                
                function getStats() {
                    fetch('/status')
                        .then(r => r.json())
                        .then(data => {
                            document.getElementById('stats').innerHTML = `
                                <h3>📊 Statistics</h3>
                                <p>Cycles Completed: ${data.cycle_count}</p>
                                <p>Messages Sent: ${data.sent_count}</p>
                                <p>Messages Failed: ${data.failed_count}</p>
                                <p>Targets: ${data.targets_count}</p>
                                <p>Interval: ${data.interval} seconds</p>
                            `;
                        });
                }
                
                // Auto-update status every 5 seconds
                setInterval(updateStatus, 5000);
                updateStatus();
            </script>
        </body>
    </html>
    """

@app.route('/start', methods=['POST'])
def start_bot():
    success = bot.start_bot()
    return jsonify({
        'message': 'Bot started successfully!' if success else 'Bot is already running!',
        'success': success
    })

@app.route('/stop', methods=['POST'])
def stop_bot():
    bot.is_running = False
    return jsonify({
        'message': 'Bot stopped successfully!',
        'success': True
    })

@app.route('/status')
def get_status():
    return jsonify({
        'is_running': bot.is_running,
        'cycle_count': bot.cycle_count,
        'sent_count': bot.sent_count,
        'failed_count': bot.failed_count,
        'targets_count': len(bot.targets),
        'interval': bot.interval
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
