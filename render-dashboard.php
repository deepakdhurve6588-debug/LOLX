<?php
// render-dashboard.php - Render.com optimized
session_start();

// Render.com specific configuration
class RenderAutoMessenger {
    private $token;
    private $uids;
    private $messages;
    private $delay;
    private $currentIndex;
    
    public function __construct() {
        $this->loadConfiguration();
        $this->currentIndex = 0;
    }
    
    private function loadConfiguration() {
        // Render environment variables
        $this->token = getenv('FB_TOKEN') ?: 
            (file_exists('token.txt') ? trim(file_get_contents('token.txt')) : '');
        
        // UIDs
        if (getenv('FB_UIDS')) {
            $this->uids = explode(',', getenv('FB_UIDS'));
        } else if (file_exists('uid.txt')) {
            $this->uids = file('uid.txt', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        } else {
            $this->uids = [];
        }
        
        // Messages
        if (getenv('FB_MESSAGES')) {
            $this->messages = explode('|', getenv('FB_MESSAGES'));
        } else if (file_exists('message.txt')) {
            $this->messages = file('message.txt', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        } else {
            $this->messages = ["Hello from Render.com!"];
        }
        
        // Delay
        $this->delay = getenv('FB_DELAY') ?: 
            (file_exists('time.txt') ? trim(file_get_contents('time.txt')) : '5');
        $this->delay = intval($this->delay) * 1000;
    }
    
    public function sendMessage($uid, $message) {
        $url = "https://graph.facebook.com/v18.0/me/messages";
        
        $data = [
            'recipient' => ['id' => $uid],
            'message' => ['text' => $message],
            'messaging_type' => 'MESSAGE_TAG',
            'tag' => 'ACCOUNT_UPDATE',
            'access_token' => $this->token
        ];
        
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => json_encode($data),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_TIMEOUT => 30,
            CURLOPT_USERAGENT => 'Render-Auto-Messenger/1.0'
        ]);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlError = curl_error($ch);
        curl_close($ch);
        
        $this->log("Message to $uid: " . ($httpCode === 200 ? 'SUCCESS' : 'FAILED'));
        
        return [
            'success' => $httpCode === 200,
            'http_code' => $httpCode,
            'response' => json_decode($response, true),
            'error' => $curlError ?: ($httpCode !== 200 ? 'HTTP ' . $httpCode : null)
        ];
    }
    
    public function getNextMessage() {
        if (empty($this->messages)) return "Hello from Render!";
        $message = $this->messages[$this->currentIndex];
        $this->currentIndex = ($this->currentIndex + 1) % count($this->messages);
        return $message;
    }
    
    public function runBatch($count = 5) {
        $results = [];
        $sentCount = 0;
        
        foreach ($this->uids as $uid) {
            if ($sentCount >= $count) break;
            
            $uid = trim($uid);
            if (empty($uid)) continue;
            
            $message = $this->getNextMessage();
            $result = $this->sendMessage($uid, $message);
            
            $results[] = [
                'uid' => $uid,
                'message' => $message,
                'success' => $result['success'],
                'error' => $result['error'] ?? $result['response']['error']['message'] ?? null,
                'timestamp' => time()
            ];
            
            $sentCount++;
            
            // Delay between messages
            if ($sentCount < min($count, count($this->uids))) {
                usleep($this->delay * 1000);
            }
        }
        
        return $results;
    }
    
    public function testConnection() {
        if (empty($this->uids)) {
            return ['success' => false, 'error' => 'No UIDs configured'];
        }
        
        $testUid = $this->uids[0];
        return $this->sendMessage($testUid, "🧪 Test message from Render.com");
    }
    
    private function log($message) {
        $timestamp = date('Y-m-d H:i:s');
        $logMessage = "[$timestamp] $message\n";
        
        // Log to file (Render provides persistent storage)
        file_put_contents('logs/messenger.log', $logMessage, FILE_APPEND | LOCK_EX);
        
        // Also output to stdout for Render logs
        error_log($message);
    }
    
    public function getLogs($lines = 50) {
        if (!file_exists('logs/messenger.log')) {
            return ['No logs available yet'];
        }
        
        $logContent = file('logs/messenger.log', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        return array_slice($logContent, -$lines);
    }
    
    public function getConfig() {
        return [
            'platform' => 'Render.com',
            'uids_count' => count($this->uids),
            'messages_count' => count($this->messages),
            'delay_seconds' => $this->delay / 1000,
            'render_region' => getenv('RENDER_REGION') ?: 'unknown',
            'render_service_id' => getenv('RENDER_SERVICE_ID') ?: 'unknown'
        ];
    }
}

// Initialize messenger
try {
    $messenger = new RenderAutoMessenger();
    $config = $messenger->getConfig();
    $error = null;
} catch (Exception $e) {
    $error = $e->getMessage();
    $config = [];
}
?>
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto Messenger - Render.com</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%); color: white; padding: 30px; text-align: center; }
        .render-badge { background: #00c6ff; padding: 8px 20px; border-radius: 25px; font-size: 14px; margin: 10px 0; display: inline-block; }
        .content { padding: 30px; }
        .card { background: #f8f9fa; padding: 25px; border-radius: 12px; margin-bottom: 25px; border-left: 5px solid #0072ff; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #0072ff; margin: 10px 0; }
        button { background: #0072ff; color: white; padding: 14px 28px; border: none; border-radius: 8px; cursor: pointer; margin: 8px; font-size: 16px; font-weight: 600; transition: all 0.3s; }
        button:hover { background: #0056cc; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .btn-success { background: #28a745; }
        .btn-danger { background: #dc3545; }
        .btn-warning { background: #ffc107; color: #333; }
        .result { padding: 20px; border-radius: 10px; margin: 20px 0; }
        .success { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
        .warning { background: #fff3cd; color: #856404; border: 2px solid #ffeaa7; }
        .info { background: #e7f3ff; color: #0c5460; border: 2px solid #b8daff; }
        .log-container { background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; font-size: 12px; max-height: 300px; overflow-y: auto; margin: 15px 0; }
        .tab-container { margin: 20px 0; }
        .tabs { display: flex; background: #f0f2f5; border-radius: 10px; padding: 5px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab { flex: 1; padding: 15px; text-align: center; cursor: pointer; border-radius: 8px; transition: all 0.3s; min-width: 150px; }
        .tab.active { background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); font-weight: bold; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .progress { width: 100%; background: #f0f2f5; border-radius: 10px; overflow: hidden; margin: 15px 0; }
        .progress-bar { height: 20px; background: linear-gradient(90deg, #0072ff, #00c6ff); transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Auto Messenger</h1>
            <div class="render-badge">☁️ Powered by Render.com</div>
            <p>Free Tier • Instant Deploy • Auto Scaling</p>
        </div>

        <div class="content">
            <?php if ($error): ?>
                <div class="result error">
                    <h3>❌ Configuration Error</h3>
                    <p><?php echo htmlspecialchars($error); ?></p>
                    <p>Please check your environment variables in Render dashboard.</p>
                </div>
            <?php else: ?>
                
                <!-- Stats Grid -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div>👥 UIDs</div>
                        <div class="stat-number"><?php echo $config['uids_count']; ?></div>
                    </div>
                    <div class="stat-card">
                        <div>💬 Messages</div>
                        <div class="stat-number"><?php echo $config['messages_count']; ?></div>
                    </div>
                    <div class="stat-card">
                        <div>⏰ Delay</div>
                        <div class="stat-number"><?php echo $config['delay_seconds']; ?>s</div>
                    </div>
                    <div class="stat-card">
                        <div>🌐 Region</div>
                        <div class="stat-number"><?php echo strtoupper($config['render_region']); ?></div>
                    </div>
                </div>

                <div class="tab-container">
                    <div class="tabs">
                        <div class="tab active" onclick="showTab('control')">🎮 Control Panel</div>
                        <div class="tab" onclick="showTab('config')">⚙️ Configuration</div>
                        <div class="tab" onclick="showTab('logs')">📋 Logs</div>
                        <div class="tab" onclick="showTab('about')">ℹ️ About</div>
                    </div>

                    <!-- Control Panel Tab -->
                    <div id="controlTab" class="tab-content active">
                        <div class="card">
                            <h3>🚀 Quick Actions</h3>
                            <button onclick="testConnection()" class="btn-success">🧪 Test Connection</button>
                            <button onclick="sendBatch(3)">📨 Send 3 Messages</button>
                            <button onclick="sendBatch(5)" class="btn-success">📨 Send 5 Messages</button>
                            <button onclick="sendBatch(10)" class="btn-warning">📨 Send 10 Messages</button>
                            <button onclick="viewLiveLogs()">🔍 Live Logs</button>
                        </div>

                        <div id="progressSection" style="display: none;">
                            <h4>Progress</h4>
                            <div class="progress">
                                <div id="progressBar" class="progress-bar" style="width: 0%"></div>
                            </div>
                            <p id="progressText">Initializing...</p>
                        </div>

                        <div id="actionResults"></div>
                    </div>

                    <!-- Configuration Tab -->
                    <div id="configTab" class="tab-content">
                        <div class="card">
                            <h3>⚙️ Current Configuration</h3>
                            <div class="result info">
                                <p><strong>Platform:</strong> <?php echo $config['platform']; ?></p>
                                <p><strong>Service ID:</strong> <?php echo $config['render_service_id']; ?></p>
                                <p><strong>Region:</strong> <?php echo $config['render_region']; ?></p>
                                <p><strong>UIDs:</strong> <?php echo $config['uids_count']; ?> configured</p>
                                <p><strong>Messages:</strong> <?php echo $config['messages_count']; ?> in rotation</p>
                                <p><strong>Delay:</strong> <?php echo $config['delay_seconds']; ?> seconds</p>
                            </div>
                        </div>

                        <div class="card">
                            <h3>🔧 Environment Variables</h3>
                            <p>Configure these in your Render.com dashboard:</p>
                            <div class="log-container">
                                FB_TOKEN=your_facebook_page_token<br>
                                FB_UIDS=123456789,987654321,555555555<br>
                                FB_MESSAGES=Message 1|Message 2|Message 3<br>
                                FB_DELAY=5
                            </div>
                        </div>
                    </div>

                    <!-- Logs Tab -->
                    <div id="logsTab" class="tab-content">
                        <div class="card">
                            <h3>📋 System Logs</h3>
                            <button onclick="refreshLogs()">🔄 Refresh Logs</button>
                            <button onclick="clearLogs()" class="btn-danger">🗑️ Clear Logs</button>
                            
                            <div id="logsContainer" class="log-container">
                                Loading logs...
                            </div>
                        </div>
                    </div>

                    <!-- About Tab -->
                    <div id="aboutTab" class="tab-content">
                        <div class="card">
                            <h3>ℹ️ About Render.com Auto Messenger</h3>
                            <p>This application is optimized for Render.com's free tier with:</p>
                            <ul style="margin: 15px 0; padding-left: 20px;">
                                <li>✅ 750 free hours per month</li>
                                <li>✅ Automatic SSL certificates</li>
                                <li>✅ Global CDN</li>
                                <li>✅ Persistent disk storage</li>
                                <li>✅ Auto deployment from Git</li>
                                <li>✅ Custom domains</li>
                            </ul>
                            <p><strong>Render.com Benefits:</strong></p>
                            <div class="result success">
                                <p>• No credit card required for free tier</p>
                                <p>• Better free tier than Heroku</p>
                                <p>• Easy environment variables setup</p>
                                <p>• Built-in monitoring and logs</p>
                            </div>
                        </div>
                    </div>
                </div>

            <?php endif; ?>
        </div>
    </div>

    <script>
        // Tab navigation
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.getElementById(tabName + 'Tab').classList.add('active');
            event.target.classList.add('active');
            
            // Auto-refresh logs when logs tab is opened
            if (tabName === 'logs') {
                refreshLogs();
            }
        }

        // Test connection
        async function testConnection() {
            document.getElementById('actionResults').innerHTML = 
                '<div class="result warning">Testing connection...</div>';
            
            try {
                const response = await fetch('render-handler.php?action=test');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('actionResults').innerHTML = 
                        '<div class="result success">✅ Connection test successful! Facebook API is responding.</div>';
                } else {
                    document.getElementById('actionResults').innerHTML = 
                        `<div class="result error">❌ Connection failed: ${data.error}</div>`;
                }
            } catch (error) {
                document.getElementById('actionResults').innerHTML = 
                    `<div class="result error">❌ Request failed: ${error.message}</div>`;
            }
        }

        // Send message batch
        async function sendBatch(count) {
            document.getElementById('progressSection').style.display = 'block';
            document.getElementById('actionResults').innerHTML = 
                `<div class="result warning">Preparing to send ${count} messages...</div>`;
            
            // Simulate progress
            simulateProgress();
            
            try {
                const response = await fetch(`render-handler.php?action=send_batch&count=${count}`);
                const data = await response.json();
                
                document.getElementById('progressSection').style.display = 'none';
                
                if (data.success) {
                    const successCount = data.results.filter(r => r.success).length;
                    const errorCount = data.results.filter(r => !r.success).length;
                    
                    let resultsHtml = `<div class="result success">
                        <h4>✅ Batch Completed!</h4>
                        <p>Success: ${successCount}, Failed: ${errorCount}</p>`;
                    
                    if (data.results.length > 0) {
                        resultsHtml += '<div style="margin-top: 15px;"><strong>Recent results:</strong><br>';
                        data.results.slice(0, 3).forEach(result => {
                            resultsHtml += `${result.success ? '✅' : '❌'} ${result.uid}: ${result.message.substring(0, 30)}...<br>`;
                        });
                        if (data.results.length > 3) {
                            resultsHtml += `... and ${data.results.length - 3} more`;
                        }
                        resultsHtml += '</div>';
                    }
                    
                    resultsHtml += '</div>';
                    document.getElementById('actionResults').innerHTML = resultsHtml;
                } else {
                    document.getElementById('actionResults').innerHTML = 
                        `<div class="result error">❌ Batch failed: ${data.error}</div>`;
                }
            } catch (error) {
                document.getElementById('progressSection').style.display = 'none';
                document.getElementById('actionResults').innerHTML = 
                    `<div class="result error">❌ Request failed: ${error.message}</div>`;
            }
        }

        // Progress simulation
        function simulateProgress() {
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress > 95) progress = 95;
                
                document.getElementById('progressBar').style.width = progress + '%';
                document.getElementById('progressText').textContent = 
                    `Processing... ${Math.round(progress)}%`;
            }, 500);
            
            // Clear interval after 30 seconds
            setTimeout(() => clearInterval(interval), 30000);
        }

        // Logs management
        async function refreshLogs() {
            const logsContainer = document.getElementById('logsContainer');
            logsContainer.textContent = 'Loading logs...';
            
            try {
                const response = await fetch('render-handler.php?action=get_logs');
                const data = await response.json();
                
                if (data.success) {
                    logsContainer.textContent = data.logs.join('\n');
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                } else {
                    logsContainer.textContent = 'Error loading logs: ' + data.error;
                }
            } catch (error) {
                logsContainer.textContent = 'Failed to load logs: ' + error.message;
            }
        }

        async function clearLogs() {
            if (confirm('Are you sure you want to clear all logs?')) {
                try {
                    const response = await fetch('render-handler.php?action=clear_logs');
                    const data = await response.json();
                    
                    if (data.success) {
                        refreshLogs();
                    } else {
                        alert('Failed to clear logs: ' + data.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }
        }

        function viewLiveLogs() {
            showTab('logs');
            refreshLogs();
        }

        // Auto-refresh logs every 10 seconds when on logs tab
        setInterval(() => {
            if (document.getElementById('logsTab').style.display !== 'none') {
                refreshLogs();
            }
        }, 10000);

        // Load logs when page loads if on logs tab
        document.addEventListener('DOMContentLoaded', function() {
            if (window.location.hash === '#logs') {
                showTab('logs');
            }
        });
    </script>
</body>
</html>
