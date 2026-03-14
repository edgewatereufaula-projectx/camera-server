# Edgeless UC Camera Server - Pi Setup Guide

## What You Need
- Raspberry Pi 5 (4GB or 8GB)
- MicroSD card (32GB+)
- Power supply
- Network connection

---

## Step 1: Flash Raspberry Pi OS

1. Download Raspberry Pi Imager: https://www.raspberrypi.com/software/
2. Run the imager
3. Choose: Raspberry Pi OS (64-bit) - **Lite** (no desktop, smaller)
4. Write to SD card
5. Enable SSH: Create empty file named `ssh` on the boot partition

---

## Step 2: Initial Pi Setup

1. Insert SD card, power on Pi
2. Find Pi's IP (check your router or use "raspberrypi.local")
3. SSH in: `ssh pi@<ip>` (password: raspberry)

Run these commands:
```bash
# Change password
passwd

# Update everything
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip libopencv-dev ffmpeg

# Create app folder
mkdir -p ~/camera-server
cd ~/camera-server
```

---

## Step 3: Copy App Files

From your computer, copy the files:
```bash
# On your laptop, in the camera-server folder:
scp camera_server.py config.json pi@<pi-ip>:~/camera-server/
scp requirements.txt pi@<pi-ip>:~/camera-server/
```

Or use WinSCP/FileZilla to drag & drop.

---

## Step 4: Install & Run

SSH back into Pi:
```bash
cd ~/camera-server
pip3 install --user -r requirements.txt
python3 camera_server.py
```

---

## Step 5: Access the App

- **Main View:** http://<pi-ip>:9090
- **Settings:** http://<pi-ip>:9090/settings

---

## Step 6: Auto-Start (Optional)

```bash
# Create service
sudo nano /etc/systemd/system/camera-server.service
```

Paste this:
```ini
[Unit]
Description=Edgeless UC Camera Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/camera-server
ExecStart=/usr/bin/python3 /home/pi/camera-server/camera_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable camera-server
sudo systemctl start camera-server
```

---

## Configure Cameras

1. Go to http://<pi-ip>:9090/settings
2. Enter RTSP URL for each camera
3. Check "Enable this camera"
4. Configure door unlock if needed
5. Save

---

## Troubleshooting

**Can't connect?**
- Check IP: `hostname -I`
- Check service: `sudo systemctl status camera-server`
- Check logs: `journalctl -u camera-server -f`

**Camera not showing?**
- Verify RTSP URL works
- Check firewall: `sudo ufw allow 9090`

**Need to edit config manually?**
```bash
nano ~/camera-server/config.json
```

---

## Port Forwarding (For Remote Access)

If you need access from outside the site:
- Forward port 9090 to Pi's IP
- Or use Tailscale/VPN for secure remote access
