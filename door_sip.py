#!/usr/bin/env python3
"""
SIP Door Opener - Send DTMF to open door via SIP call
"""

import sys
import subprocess
import time

def send_dtmf(sip_server, dtmf_code="00"):
    """
    Send DTMF to GDS via SIP call to trigger door relay
    Uses sipsak to make the call and send DTMF
    """
    # Method 1: Try using sipsak if available
    try:
        # Send SIP OPTIONS with DTMF in INFO (some devices respond to this)
        result = subprocess.run(
            ['sipsak', '-vv', '-s', f'sip:{sip_server}', '-M', '-B', dtmf_code],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, "DTMF sent via sipsak"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Method 2: Try using netcat to send raw SIP (fallback)
    sip_msg = f"""INVITE sip:{dtmf_code}@{sip_server} SIP/2.0
Via: SIP/2.0/UDP 192.168.1.100:5060
From: <sip:door@192.168.1.100>
To: <sip:{dtmf_code}@{sip_server}>
Call-ID: door-{int(time.time())}@192.168.1.100
CSeq: 1 INVITE
Content-Length: 0

"""
    try:
        result = subprocess.run(
            ['nc', '-u', sip_server, '5060'],
            input=sip_msg.encode(),
            capture_output=True,
            timeout=5
        )
        return True, "SIP packet sent"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return False, "No SIP tool available"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: door_sip.py <GDS_IP> [DTMF_CODE]")
        sys.exit(1)
    
    gds_ip = sys.argv[1]
    dtmf = sys.argv[2] if len(sys.argv) > 2 else "00"
    
    success, msg = send_dtmf(gds_ip, dtmf)
    print(msg)
    sys.exit(0 if success else 1)