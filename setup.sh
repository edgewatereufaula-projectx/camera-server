#!/bin/bash
# Edgeless UC Camera Server - One-Command Setup
# Run: curl -sL https://raw.githubusercontent.com/edgewatereufaula-projectx/camera-server/main/setup.sh | bash

set -e

echo "📹 Edgeless UC Camera Server Setup"
echo "===================================="

# Ask for hostname
echo ""
read -p "Enter hostname for this device (e.g., doorcam, camera1): " -r hostname
hostname="${hostname:-doorcam}"
echo "Setting hostname to: $hostname"

# Change hostname
sudo hostnamectl set-hostname "$hostname"
echo "127.0.1.1 $hostname" | sudo tee -a /etc/hosts > /dev/null
echo "✅ Hostname set to: $hostname"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    sudo apt update && sudo apt install -y python3 python3-pip
fi

# Install system dependencies
echo "Installing dependencies..."
sudo apt install -y libopencv-dev ffmpeg 2>/dev/null || true

# Install Python packages
echo "Installing Python packages..."
pip3 install --user opencv-python-headless flask numpy 2>/dev/null || true

# Ask for port
echo ""
read -p "Use port 80 (requires sudo) or 9090 (default)? [80/9090]: " -r port
port="${port:-9090}"

# Validate port
if [ "$port" = "80" ]; then
    echo "Note: Port 80 requires running the server with sudo"
    sudo apt install -y authbind 2>/dev/null || true
fi

# Create app directory
APP_DIR="$HOME/camera-server"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Copy files from GitHub or local
echo ""
read -p "Download from GitHub? (y/n): " -r github
if [[ $github =~ ^[Yy]$ ]]; then
    curl -sL https://raw.githubusercontent.com/edgewatereufaula-projectx/camera-server/main/camera_server.py -o camera_server.py
    curl -sL https://raw.githubusercontent.com/edgewatereufaula-projectx/camera-server/main/requirements.txt -o requirements.txt
    curl -sL https://raw.githubusercontent.com/edgewatereufaula-projectx/camera-server/main/config.json -o config.json
    echo "✅ Downloaded from GitHub"
else
    echo "Please copy camera_server.py manually to the Pi first."
    exit 1
fi

# Create systemd service
echo "Creating auto-start service..."
cat > "$HOME/camera-server.service" << EOF
[Unit]
Description=Edgeless UC Camera Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3 $APP_DIR/camera_server.py --port $port
Restart=always
RestartSec=10
Environment=PORT=$port

[Install]
WantedBy=multi-user.target
EOF

# Ask about auto-start
echo ""
read -p "Enable auto-start on boot? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cp "$HOME/camera-server.service" /tmp/
    sudo cp /tmp/camera-server.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable camera-server
    sudo systemctl start camera-server
    echo "✅ Service enabled and started"
else
    if [ "$port" = "80" ]; then
        echo "Run with sudo: sudo python3 $APP_DIR/camera_server.py --port 80"
    else
        echo "Run: python3 $APP_DIR/camera_server.py --port $port"
    fi
fi

echo ""
echo "🎉 Setup complete!"
echo "   Hostname:     $hostname.local"
echo "   Main view:    http://$hostname.local:$port"
echo "   Settings:     http://$hostname.local:$port/settings"
