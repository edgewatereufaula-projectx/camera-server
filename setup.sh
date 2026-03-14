#!/bin/bash
# Edgeless UC Camera Server - One-Command Setup
# Run: curl -sL https://raw.githubusercontent.com/YOUR_REPO/main/setup.sh | bash

set -e

echo "📹 Edgeless UC Camera Server Setup"
echo "===================================="

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

# Create app directory
APP_DIR="$HOME/camera-server"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Create default config if not exists
if [ ! -f config.json ]; then
    cat > config.json << 'EOF'
{
  "cameras": {
    "cam1": {"name": "Camera 1", "rtsp": "", "enabled": false, "door": {"enabled": false, "ip": "", "auth": ""}},
    "cam2": {"name": "Camera 2", "rtsp": "", "enabled": false, "door": {"enabled": false, "ip": "", "auth": ""}},
    "cam3": {"name": "Camera 3", "rtsp": "", "enabled": false, "door": {"enabled": false, "ip": "", "auth": ""}},
    "cam4": {"name": "Camera 4", "rtsp": "", "enabled": false, "door": {"enabled": false, "ip": "", "auth": ""}}
  }
}
EOF
fi

# Create camera_server.py if not exists (inline minimal version)
if [ ! -f camera_server.py ]; then
    echo "Error: camera_server.py not found!"
    echo "Please copy camera_server.py to the Pi first."
    exit 1
fi

# Create systemd service
echo "Creating auto-start service..."
cat > "$HOME/camera-server.service" << 'EOF'
[Unit]
Description=Edgeless UC Camera Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/camera-server
ExecStart=/usr/bin/python3 $HOME/camera-server/camera_server.py
Restart=always
RestartSec=10

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
    echo "Run 'python3 $APP_DIR/camera_server.py' to start manually"
fi

echo ""
echo "🎉 Setup complete!"
IP=$(hostname -I | awk '{print $1}')
echo "   Main view:   http://$IP:9090"
echo "   Settings:    http://$IP:9090/settings"
