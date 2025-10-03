#!/bin/bash
echo "🚀 Building Auto Messenger for Render.com..."

# Check PHP version
php -v

# Create necessary directories
mkdir -p tmp
mkdir -p logs

# Set permissions
chmod -R 755 .

# Install dependencies if using composer
if [ -f "composer.json" ]; then
    echo "Installing PHP dependencies..."
    composer install --no-dev --optimize-autoloader
fi

echo "✅ Build completed successfully!"
