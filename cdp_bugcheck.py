import json
import time
import websocket
import urllib.request

def get_version_ws():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/version") as r:
        return json.load(r)["webSocketDebuggerUrl"]

bws = get_version_ws()
b = websocket.create_connection(bws, timeout=15, origin="http://127.0.0.1")
bid = 0
def bsend(method, params=None, sid=None):
    global bid
    bid += 1
    m = {"id": bid, "method": method, "params": params or {}}
    if sid: m["sessionId"] = sid
    b.send(json.dumps(m))
    return bid
def bwait(w, sid=None):
    while True:
        d = json.loads(b.recv())
        if d.get("id") == w and (sid is None or d.get("sessionId") == sid):
            return d

# Create a new tab and navigate
r = bwait(bsend("Target.createTarget", {"url": "file:///home/user/Doubao/chats/38443931837314306/脑图密室逃脱 V6.0.1.html"}))
target_id = r["result"]["targetId"]
print("New target:", target_id)
b.close()
time.sleep(8)

# Attach to it
b = websocket.create_connection(get_version_ws(), timeout=15, origin="http://127.0.0.1")
bid = 0
r = bwait(bsend("Target.attachToTarget", {"targetId": target_id, "flatten": True}))
sess = r["result"]["sessionId"]

p = websocket.create_connection("ws://127.0.0.1:9222/devtools/page/" + target_id, timeout=20, origin="http://127.0.0.1")
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
p.settimeout(20)
print("Loaded:", peval("typeof V6 !== 'undefined' ? 'yes' : 'no'"))

# Open puzzle
peval("HomeRoom.enter();")
time.sleep(1.5)
peval("document.querySelector('[data-wing=\"attic\"]').click();")
time.sleep(1.3)
peval("var n=G.nodes.find(function(n){return n.id==='v6r_v6_game_puzzle'});n.onClick(n);")
time.sleep(1.2)
print("Tiles:", peval("document.querySelectorAll('.v6a-tile').length"))

# Reset
peval("document.getElementById('v6aPlReset').click();")
time.sleep(1)
print("After reset - tiles:", peval("document.querySelectorAll('.v6a-tile').length"))

# 6 rapid clicks
for i in range(6):
    peval("""
    (function(){
      var grid=document.getElementById('v6aPGrid');
      var tiles=Array.from(grid.querySelectorAll('.v6a-tile'));
      if(!tiles.length) return;
      var cell=tiles[0].offsetWidth, gap=8;
      var occ={};
      tiles.forEach(function(t){
        var m=t.style.transform.match(/translate\\(([\\d.]+)px,\\s*([\\d.]+)px\\)/);
        if(!m) return;
        var cc=Math.round((parseFloat(m[1])-gap)/(cell+gap));
        var rr=Math.round((parseFloat(m[2])-gap)/(cell+gap));
        occ[rr+','+cc]=t;
      });
      var br=-1,bc=-1;
      for(var r=0;r<3;r++)for(var q=0;q<3;q++){ if(!occ[r+','+q]){br=r;bc=q;} }
      var t = br<2 ? occ[(br+1)+','+bc] : occ[(br-1)+','+bc];
      if(t) t.click();
    })();
    """)
    time.sleep(0.25)
print("After 6 clicks - steps:", peval("document.getElementById('v6aPSteps').textContent"))
print("Tiles after clicks:", peval("document.querySelectorAll('.v6a-tile').length"))

# 4x4 then back
peval("document.querySelector('.v6a-modeseg [data-n=\"4\"]').click();")
time.sleep(1)
print("4x4 tiles:", peval("document.querySelectorAll('.v6a-tile').length"))
peval("document.querySelector('.v6a-modeseg [data-n=\"3\"]').click();")
time.sleep(1)
print("Back 3x3 tiles:", peval("document.querySelectorAll('.v6a-tile').length"))

# Close panel and reopen
peval("""
(function(){
  var b=document.querySelector('.ach-panel-close, .v6-panel-close, .v6a-panel-close');
  if(b) b.click();
})();
""")
time.sleep(0.5)
peval("var n=G.nodes.find(function(n){return n.id==='v6r_v6_game_puzzle'});n.onClick(n);")
time.sleep(1)
print("Reopen tiles:", peval("document.querySelectorAll('.v6a-tile').length"))
p.close()
print("DONE")
