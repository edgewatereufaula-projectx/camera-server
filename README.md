# Camera Web Server - Grandstream GDS 3727

Lightweight Flask server to display multiple RTSP camera feeds in a 4-grid layout with call button integration.

## Quick Start

### 1. Install Dependencies

```bash
cd camera-server
pip install -r requirements.txt
```

### 2. Configure Cameras

Edit `camera_server.py` and add your cameras:

```python
CAMERAS = {
    'cam1': {
        'name': 'Front Door',
        'rtsp': 'rtsp://remote:Lollipop!@192.168.10.1.32/live',
        'callbacks': []
    },
    'cam2': {
        'name': 'Back Entrance',
        'rtsp': 'rtsp://user:password@192.168.10.x/live',
        'callbacks': []
    },
    # Add up to 4 cameras
}
```

### 3. Run the Server

```bash
python3 camera_server.py
```

Server starts on `http://0.0.0.0:9090`

---

## GDS 3727 Call Button Configuration

To make the camera trigger the web UI when someone presses the call button:

### Option A: HTTP Callback (Recommended)

In the GDS 3727 web interface:

1. **Settings → Call Settings → Call Button Action**
2. Enable HTTP callback
3. Set URL to: `http://<server-ip>:9090/call-trigger/cam1`
4. Set method to POST

### Option B: Using the Test Buttons

The web UI has "Test Call" buttons to simulate a call button press for testing.

---

## Architecture

- **OpenCV** pulls RTSP streams from cameras
- **Flask** serves MJPEG streams to browser
- **Polling** (500ms) checks call states
- **Call trigger** endpoint receives HTTP POST from GDS cameras
- **Visual feedback** — red pulsing border + fullscreen alert when call active

---

## Performance Notes

- OpenCV is lighter than FFmpeg for simple RTSP→MJPEG
- Uses threading per camera (each camera = 1 thread)
- Auto-reconnect on stream failure
- Call state auto-clears after 30 seconds

---

## Adding More Cameras

1. Add entry to `CAMERAS` dict
2. Grid automatically adapts (2x2 for 4 cameras, 1 column for 1-2)

---

## Troubleshooting

### Camera won't connect
- Check RTSP URL credentials
- Ensure camera is reachable from Pi (ping test)
- Verify RTSP port is open on camera

### Streams are laggy
- Use wired Ethernet instead of WiFi
- Lower resolution on camera side
- Reduce `cv2.IMWRITE_JPEG_QUALITY` (line ~50)

### Call button not working
- Verify HTTP callback URL is correct
- Check camera can reach server (firewall)
- Use "Test Call" button to verify server is receiving requests