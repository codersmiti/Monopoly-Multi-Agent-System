# events.py
import json, urllib.request

RELAY_URL = "http://localhost:8086/event"   #  adjust if you kept 8081

def emit(evt: dict):
    """Send an event to the React visualizer; ignore failures silently."""
    data = json.dumps(evt).encode("utf-8")
    req = urllib.request.Request(RELAY_URL, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=0.3).read()
    except Exception:
        pass
