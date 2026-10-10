import json
import websocket

BROWSER_WS = "ws://127.0.0.1:9222/devtools/browser/c9f73b22-d1df-49cf-bf0f-7341a9d0229c"
PAGE_ID = "2AEB7B8C8CF2C455EBD9B3B37F16C51C"

ws = websocket.create_connection(BROWSER_WS, timeout=15, origin="http://127.0.0.1")
mid = 0

def send(method, params=None, session_id=None):
    global mid
    mid += 1
    myid = mid
    msg = {"id": myid, "method": method, "params": params or {}}
    if session_id:
        msg["sessionId"] = session_id
    ws.send(json.dumps(msg))
    return myid

def wait_for(myid, session_id=None):
    while True:
        data = json.loads(ws.recv())
        if data.get("id") == myid and (session_id is None or data.get("sessionId") == session_id):
            return data

# Attach to the game page target
attach_id = send("Target.attachToTarget", {"targetId": PAGE_ID, "flatten": True})
r = wait_for(attach_id)
session_id = r["result"]["sessionId"]
print("Attached, session:", session_id)

# Force navigation via Page domain (browser-level, bypasses stuck JS)
nav_id = send("Page.navigate", {"url": "file:///home/user/Doubao/chats/38443931837314306/脑图密室逃脱 V6.0.0.html"}, session_id)
r = wait_for(nav_id, session_id)
print("Navigate result:", r.get("result", r.get("error")))

ws.close()
