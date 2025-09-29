#!/bin/bash

echo "=========================================="
echo "🔐 E2EE Facebook Messenger Bot"
echo "=========================================="

# Check if required files exist
if [ ! -f "token.txt" ]; then
    echo "📝 Creating token.txt..."
    echo "YOUR_FACEBOOK_TOKEN_HERE" > token.txt
fi

if [ ! -f "user_id.txt" ]; then
    echo "📝 Creating user_id.txt..."
    echo "FACEBOOK_USER_ID_HERE" > user_id.txt
fi

if [ ! -f "message.txt" ]; then
    echo "📝 Creating message.txt..."
    cat > message.txt << EOL
नमस्ते! यह Render पर deployed E2EE bot से message है।
यह message automatically send हो रहा है।
End-to-end encryption से secure।
Render cloud platform पर running है।
EOL
fi

# Create necessary directories
mkdir -p logs
mkdir -p config

# Check if settings.json exists
if [ ! -f "config/settings.json" ]; then
    echo "📝 Creating config/settings.json..."
    cat > config/settings.json << EOL
{
    "interval_seconds": 300,
    "auto_restart": true,
    "max_retries": 3,
    "log_messages": true,
    "encryption_enabled": true
}
EOL
fi

echo "✅ Setup completed successfully"
echo "🚀 Starting Python application..."

# Start the application
python app.py
