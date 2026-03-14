#!/usr/bin/env python3
"""
Camera Web Server - Configurable via Web UI
Edit camera settings at /settings
"""

import threading, os, json, cv2, argparse, subprocess
from flask import Flask, render_template_string, Response, request, jsonify, redirect, url_for

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=9090, help='Port to run server on')
args = parser.parse_args()

app = Flask(__name__)
CONFIG_FILE = 'config.json'
call_states = {}
call_states_lock = threading.Lock()

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"cameras": {}}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_cameras():
    return load_config().get('cameras', {})

def init_call_states():
    global call_states
    with call_states_lock:
        call_states = {cam_id: False for cam_id in get_cameras()}

init_call_states()

def generate_mjpeg(cam_id):
    cam = get_cameras().get(cam_id)
    if not cam or not cam.get('enabled'): return
    rtsp = cam.get('rtsp', '')
    if not rtsp: return
    cap = cv2.VideoCapture(rtsp)
    if not cap.isOpened(): return
    while True:
        ret, frame = cap.read()
        if not ret: cap.release(); cap = cv2.VideoCapture(rtsp); continue
        with call_states_lock:
            if call_states.get(cam_id):
                h, w = frame.shape[:2]
                cv2.rectangle(frame, (0,0), (w-1,h-1), (0,0,255), 20)
        ret, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ret: yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg.tobytes() + b'\r\n')
    cap.release()

@app.route('/')
def index(): 
    cams = get_cameras()
    enabled_count = sum(1 for c in cams.values() if c.get('enabled'))
    return render_template_string(HTML, cameras=cams, count=enabled_count)
@app.route('/video/<cam_id>') 
def video(cam_id): return Response(generate_mjpeg(cam_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        cams = {}
        for i in range(1, 5):
            cid = f'cam{i}'
            cams[cid] = {
                'name': request.form.get(f'name_{i}', f'Camera {i}'),
                'rtsp': request.form.get(f'rtsp_{i}', ''),
                'enabled': request.form.get(f'enabled_{i}') == 'on',
                'door': {
                    'enabled': request.form.get(f'door_enabled_{i}') == 'on',
                    'ip': request.form.get(f'door_ip_{i}', ''),
                    'auth': request.form.get(f'door_auth_{i}', '')
                }
            }
        save_config({'cameras': cams})
        init_call_states()
        return redirect(url_for('index'))
    return render_template_string(SETTINGS, config=load_config())

@app.route('/call-trigger/<cam_id>', methods=['GET', 'POST'])
def call_trigger(cam_id):
    if cam_id not in get_cameras(): return jsonify({'error': 'Unknown'}), 404
    with call_states_lock: call_states[cam_id] = True
    threading.Timer(30, lambda: call_states.update({cam_id: False})).start()
    return jsonify({'status': 'ok'})

@app.route('/call-clear/<cam_id>', methods=['GET', 'POST'])
def call_clear(cam_id):
    with call_states_lock: call_states[cam_id] = False
    return jsonify({'status': 'ok'})

@app.route('/door-open/<cam_id>', methods=['POST'])
def door_open(cam_id):
    import urllib.request, base64, ssl
    cam = get_cameras().get(cam_id)
    if not cam: return jsonify({'error': 'Unknown'}), 404
    door = cam.get('door', {})
    if not door.get('enabled') or not door.get('ip'): return jsonify({'error': 'No door'}), 400
    
    door_ip = door.get('ip', '')
    auth = door.get('auth', '')
    sip_dtmf = door.get('dtmf', '00')
    
    # Try SIP DTMF first (more reliable)
    try:
        result = subprocess.run(
            ['sipp', door_ip, '-s', sip_dtmf, '-d', sip_dtmf, '-l', '1', '-m', '1'],
            capture_output=True, timeout=20,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            return jsonify({'status': 'ok', 'door': 'opened', 'method': 'sip-dtmf'})
    except FileNotFoundError:
        print("sipp not found")
    except Exception as e:
        print(f"SIP error: {e}")
    
    # Fallback to HTTP API
    req = urllib.request.Request(f"http://{door_ip}/api/door/open")
    if auth:
        req.add_header('Authorization', f"Basic {base64.b64encode(auth.encode()).decode()}")
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    try:
        urllib.request.urlopen(req, timeout=5, context=ctx)
        return jsonify({'status': 'ok', 'door': 'opened', 'method': 'http'})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/states')
def api_states():
    with call_states_lock: return jsonify(call_states)

@app.route('/logo.png')
def logo():
    from flask import send_file
    return send_file('logo.png', mimetype='image/png')

HTML = '''<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width"><style>
*{box-sizing:border-box;margin:0;padding:0}body{background:#1a1a1a;color:#eee;font-family:sans-serif;min-height:100vh}
header{background:#2d2d2d;padding:15px 20px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #444}
.logo{display:flex;align-items:center;gap:10px}
.logo svg{vertical-align:middle}
.logo-text{font-size:1.2rem;font-weight:500}
.logo-text .edge{color:#4a90a4}
.logo-text .less{color:#ccc}
.btn-settings{padding:8px 16px;background:#444;color:#fff;text-decoration:none;border-radius:4px}
.grid{display:grid;gap:10px;padding:10px;max-width:1600px;margin:0 auto}
.grid-1{grid-template-columns:1fr}.grid-2{grid-template-columns:repeat(2,1fr)}
.grid-3,.grid-4{grid-template-columns:repeat(2,1fr)}
@media(max-width:900px){.grid-1,.grid-2,.grid-3,.grid-4{grid-template-columns:1fr}}
.camera{background:#222;border-radius:8px;overflow:hidden;position:relative;border:3px solid transparent}
.camera.calling{border-color:#f00;box-shadow:0 0 30px rgba(255,0,0,0.5)}
.camera-name{position:absolute;top:10px;left:10px;background:rgba(0,0,0,0.7);padding:5px 10px;border-radius:4px;font-size:0.9rem;z-index:10}
.camera-status{position:absolute;top:10px;right:10px;background:rgba(0,0,0,0.7);padding:5px 10px;border-radius:4px;font-size:0.8rem;z-index:10;color:#4f4}
.camera-status.calling{color:#f44}
.video{position:relative;width:100%;padding-top:56.25%}
.video img{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover}
.controls{padding:10px;display:flex;gap:10px;background:#2a2a2a;flex-wrap:wrap}
.btn{flex:1;min-width:90px;padding:8px;border:none;border-radius:4px;cursor:pointer;background:#444;color:#fff;font-size:0.85rem}
.btn-door{background:#2563eb}.btn-door:hover{background:#3b82f6}
.alert{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(255,0,0,0.95);color:#fff;padding:40px 60px;border-radius:10px;font-size:1.5rem;font-weight:bold;z-index:1000;display:none}
.alert.show{display:block}
.empty{background:#222;border-radius:8px;padding:40px;text-align:center;color:#666}
.empty h3{margin-bottom:10px}.empty p{font-size:0.9rem}
</style></head>
<body>
<header><div class="logo"><svg width="28" height="28" viewBox="0 0 28 28"><polygon points="14,1 27,8 27,20 14,27 1,20 1,8" fill="#2d3748"/><polygon points="14,1 14,27 27,20" fill="#4a90a4"/><polygon points="14,1 1,8 14,15" fill="#1a202c"/><line x1="5" y1="11" x2="23" y2="11" stroke="#4a90a4" stroke-width="1.5"/><line x1="5" y1="15" x2="23" y2="15" stroke="#4a90a4" stroke-width="1.5"/><line x1="5" y1="19" x2="23" y2="19" stroke="#4a90a4" stroke-width="1.5"/></svg><span class="logo-text"><span class="edge">EDGE</span><span class="less">LESS UC</span></span></div><a href="/settings" class="btn-settings">Settings</a></header>
<div class="grid grid-{{count}}">
{% for cam_id, cam in cameras.items() %}
{% if cam.enabled %}
<div class="camera" id="cam-{{cam_id}}">
<div class="camera-name">{{cam.name}}</div>
<div class="camera-status" id="status-{{cam_id}}">LIVE</div>
<div class="video"><img src="/video/{{cam_id}}"></div>
<div class="controls">
<button class="btn" onclick="testCall('{{cam_id}}')">Test Call</button>
<button class="btn" onclick="clearCall('{{cam_id}}')">Clear</button>
{% if cam.door and cam.door.enabled %}<button class="btn btn-door" onclick="openDoor('{{cam_id}}')">Open Door</button>{% endif %}
</div></div>
{% else %}
<div class="empty"><h3>{{cam.name}}</h3><p>Not configured. Go to Settings to enable.</p></div>
{% endif %}
{% endfor %}
</div>
<div class="alert" id="alert">DOORBELL RINGING!</div>
<script>
function testCall(id){fetch('/call-trigger/'+id,{method:'POST'})}
function clearCall(id){fetch('/call-clear/'+id,{method:'POST'})}
async function openDoor(id){
    try{
        let r=await fetch('/door-open/'+id,{method:'POST'});
        let j=await r.json();
        if(j.error){
            alert('Error: '+j.error);
        }else{
            alert('Door opened via '+j.method+'! 🔓');
        }
    }catch(e){
        alert('Error: '+e);
    }
}
async function check(){
    try{
        let r=await fetch('/api/states');
        let s=await r.json();
        let any=false;
        for(let[c,v]of Object.entries(s)){
            let e=document.getElementById('cam-'+c);
            let st=document.getElementById('status-'+c);
            if(v){
                e.classList.add('calling');
                st.classList.add('calling');
                st.textContent='RINGING';
                any=true;
            }else{
                e.classList.remove('calling');
                st.classList.remove('calling');
                st.textContent='LIVE';
            }
        }
        document.getElementById('alert').classList.toggle('show',any);
    }catch(e){}
}
setInterval(check,500);
check();
document.getElementById('alert').classList.toggle('show',any)}catch(e){}}setInterval(check,500);check();
</script></body></html>'''

SETTINGS = '''<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width"><style>
*{box-sizing:border-box;margin:0;padding:0}body{background:#1a1a1a;color:#eee;font-family:sans-serif;padding:20px}
h1{margin-bottom:20px}.back{color:#fff;display:inline-block;margin-bottom:20px}
.camera-form{background:#222;padding:20px;border-radius:8px;margin-bottom:20px}
.camera-form h2{margin-bottom:15px;padding-bottom:10px;border-bottom:1px solid #444}
.form-group{margin-bottom:15px}.form-group label{display:block;margin-bottom:5px;font-size:0.9rem;color:#aaa}
.form-group input[type="text"]{width:100%;padding:10px;border-radius:4px;border:1px solid #444;background:#333;color:#fff}
.form-group input[type="checkbox"]{width:auto;margin-right:10px}
.checkbox-group{display:flex;align-items:center;gap:10px}.door-config{margin-top:10px;padding:15px;background:#2a2a2a;border-radius:4px}
.btn-save{padding:12px 30px;background:#2563eb;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:1rem}
.btn-save:hover{background:#3b82f6}
</style></head>
<body>
<a href="/" class="back">← Back to Cameras</a>
<h1>Camera Settings</h1>
<form method="POST">
{% for cam_id, cam in config.cameras.items() %}
<div class="camera-form">
<h2>{{cam.name}} ({{cam_id}})</h2>
<div class="form-group"><label>Camera Name</label><input type="text" name="name_{{loop.index}}" value="{{cam.name}}"></div>
<div class="form-group"><label>RTSP URL</label><input type="text" name="rtsp_{{loop.index}}" value="{{cam.rtsp}}" placeholder="rtsp://user:pass@ip/stream"></div>
<div class="form-group checkbox-group"><input type="checkbox" name="enabled_{{loop.index}}" {% if cam.enabled %}checked{% endif %}><label>Enable this camera</label></div>
<div class="form-group checkbox-group"><input type="checkbox" name="door_enabled_{{loop.index}}" {% if cam.door and cam.door.enabled %}checked{% endif %}><label>Enable Door Unlock</label></div>
<div class="door-config">
<div class="form-group"><label>Door Device IP</label><input type="text" name="door_ip_{{loop.index}}" value="{{cam.door.ip if cam.door else ''}}" placeholder="192.168.1.x"></div>
<div class="form-group"><label>Auth (user:pass)</label><input type="text" name="door_auth_{{loop.index}}" value="{{cam.door.auth if cam.door else ''}}" placeholder="remote:Password!"></div>
</div></div>
{% endfor %}
<button type="submit" class="btn-save">Save Settings</button>
</form></body></html>'''

if __name__ == '__main__':
    print(f"Camera Server - http://0.0.0.0:{args.port}")
    print(f"Settings: http://0.0.0.0:{args.port}/settings")
    app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True)
