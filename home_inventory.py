import json
import time
import websocket
import urllib.request

def get_version_ws():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/version") as r:
        return json.load(r)["webSocketDebuggerUrl"]

def get_targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
        return json.load(r)

# Find existing game tab or create one
targets = get_targets()
game = None
for t in targets:
    if t["type"] == "page" and "about:blank" not in t["url"] and "brainmap" not in t["url"] and "V6" in t["url"]:
        game = t
        break
if not game:
    b = websocket.create_connection(get_version_ws(), timeout=15, origin="http://127.0.0.1")
    bid = 0
    def bsend(method, params=None):
        global bid
        bid += 1
        b.send(json.dumps({"id": bid, "method": method, "params": params or {}}))
        return bid
    def bwait(w):
        while True:
            d = json.loads(b.recv())
            if d.get("id") == w:
                return d
    r = bwait(bsend("Target.createTarget", {"url": "file:///home/user/Doubao/chats/38443931837314306/脑图密室逃脱 V6.0.1.html"}))
    tid = r["result"]["targetId"]
    b.close()
    time.sleep(8)
    targets = get_targets()
    game = next(t for t in targets if t["id"] == tid)

p = websocket.create_connection(game["webSocketDebuggerUrl"], timeout=20, origin="http://127.0.0.1")
pid = 0
def pmsg(method, params=None):
    global pid
    pid += 1
    myid = pid
    p.send(json.dumps({"id": myid, "method": method, "params": params or {}}))
    while True:
        d = json.loads(p.recv())
        if d.get("id") == myid:
            return d.get("result", d.get("error"))
def peval(expr):
    r = pmsg("Runtime.evaluate", {"expression": expr, "returnByValue": True, "userGesture": True})
    if "exceptionDetails" in r:
        return "EXC: " + json.dumps(r["exceptionDetails"].get("exception", {}).get("description", "?"))[:200]
    return r.get("result", {}).get("value")

pmsg("Runtime.enable")
p.settimeout(0.3)
errors = []
def drain(seconds):
    end = time.time() + seconds
    while time.time() < end:
        try:
            d = json.loads(p.recv())
            if d.get("method") == "Runtime.exceptionThrown":
                ed = d["params"]["exceptionDetails"]
                errors.append(ed.get("exception", {}).get("description", ed.get("text", ""))[:300])
        except Exception:
            pass
p.settimeout(20)

# Ensure home entered
inHome = peval("document.body.classList.contains('home-mode')")
print("In home:", inHome)
if not inHome or inHome == "EXC":
    peval("HomeRoom.enter();")
    time.sleep(1.5)

# List all wings and rooms
wings = peval("V6.Home ? Object.keys(V6.Home.rooms).join(',') : 'no V6.Home'")
print("Wings:", wings)

# Get full inventory
inventory = peval("""
(function(){
  var out=[];
  Object.keys(V6.Home.rooms).forEach(function(w){
    V6.Home.rooms[w].forEach(function(r){
      out.push(w+'|'+r.id+'|'+r.label);
    });
  });
  return out.join('\\n');
})();
""")
print("All rooms:")
print(inventory)
p.close()
