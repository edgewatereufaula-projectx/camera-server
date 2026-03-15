#!/usr/bin/env python3
"""
ONVIF Camera Client - Get stream URL from ONVIF-enabled cameras
"""

import asyncio
from onvif import ONVIFCamera

async def get_onvif_stream(camera_ip, username, password):
    """Connect to camera via ONVIF and get streaming URL"""
    try:
        mycam = ONVIFCamera(camera_ip, 80, username, password, '/tmp/onvif')
        
        # Get media service
        media_service = mycam.create_media_service()
        
        # Get profiles
        profiles = await media_service.GetProfiles()
        
        if not profiles:
            return None, "No profiles found"
        
        # Get first profile's stream URI
        stream_uri = await media_service.GetStreamUri({
            'ProfileToken': profiles[0].token,
            'StreamSetup': {
                'Stream': 'RTP-Unicast',
                'Transport': {'Protocol': 'RTSP'}
            }
        })
        
        return stream_uri.Uri, None
        
    except Exception as e:
        return None, str(e)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: onvif_client.py <camera_ip> <username> <password>")
        sys.exit(1)
    
    uri, err = asyncio.run(get_onvif_stream(sys.argv[1], sys.argv[2], sys.argv[3]))
    if err:
        print(f"Error: {err}")
    else:
        print(f"Stream URL: {uri}")
