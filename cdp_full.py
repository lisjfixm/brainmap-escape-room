import json
import time
import websocket
import urllib.request

def get_browser_ws():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/version") as r:
        return json.load(r)["webSocketDebuggerUrl"]

def get_targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
        return json.load(r)

# --- 1) Reload page via browser-level CDP ---
bws = get_browser_ws()
b = websocket.create_connection(bws, timeout=15, origin="http://127.0.0.1")
mid = 0
def bsend(method, params=None, sid=None):
    global mid
    mid += 1
    m = {"id": mid, "method": method, "params": params or {}}
    if sid: m["sessionId"] = sid
    b.send(json.dumps(m))
    return mid
def bwait(want, sid=None):
    while True:
        d = json.loads(b.recv())
        if d.get("id") == want and (sid is None or d.get("sessionId") == sid):
            return d

targets = get_targets()
page = next(t for t in targets if t["type"] == "page" and "about:blank" not in t["url"])
PAGE_ID = page["id"]
r = bwait(bsend("Target.attachToTarget", {"targetId": PAGE_ID, "flatten": True}))
sess = r["result"]["sessionId"]
r = bwait(bsend("Page.navigate", {"url": "file:///home/user/Doubao/chats/38443931837314306/脑图密室逃脱 V6.0.0.html"}, sess), sess)
print("Reload:", r.get("result", r.get("error")))
b.close()

# Wait for load
time.sleep(7)

# --- 2) Test via page-level CDP ---
targets = get_targets()
page = next(t for t in targets if t["type"] == "page" and "about:blank" not in t["url"])
p = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=20, origin="http://127.0.0.1")
pid = 0
def peval(expr):
    global pid
    pid += 1
    myid = pid
    p.send(json.dumps({"id": myid, "method": "Runtime.evaluate",
        "params": {"expression": expr, "returnByValue": True, "userGesture": True}}))
    while True:
        d = json.loads(p.recv())
        if d.get("id") == myid:
            r = d.get("result", {})
            if "exceptionDetails" in r:
                return "EXC"
            return r.get("result", {}).get("value")

# Open puzzle
peval("HomeRoom.enter();")
time.sleep(1.5)
peval("document.querySelector('[data-wing=\"attic\"]').click();")
time.sleep(1.3)
peval("var n=G.nodes.find(function(n){return n.id==='v6r_v6_game_puzzle'});n.onClick(n);")
time.sleep(1.2)

def blank_and_occ():
    return peval("""
    (function(){
      var grid=document.getElementById('v6aPGrid');
      var tiles=Array.from(grid.querySelectorAll('.v6a-tile'));
      var nn=tiles.length===8?3:4;
      var cell=tiles[0].offsetWidth, gap=8;
      var occ={};
      tiles.forEach(function(t){
        var m=t.style.transform.match(/translate\\(([\\d.]+)px,\\s*([\\d.]+)px\\)/);
        var cc=Math.round((parseFloat(m[1])-gap)/(cell+gap));
        var rr=Math.round((parseFloat(m[2])-gap)/(cell+gap));
        occ[rr+','+cc]=t.textContent;
      });
      var bk=null;
      for(var r=0;r<nn;r++)for(var q=0;q<nn;q++){ if(!occ[r+','+q]&&!bk) bk=r+','+q; }
      return {blank:bk, occ:occ, nn:nn};
    })();
    """)

def click_at(r, c):
    return peval("""
    (function(){
      var grid=document.getElementById('v6aPGrid');
      var tiles=Array.from(grid.querySelectorAll('.v6a-tile'));
      var cell=tiles[0].offsetWidth, gap=8;
      var want=null;
      tiles.forEach(function(t){
        var m=t.style.transform.match(/translate\\(([\\d.]+)px,\\s*([\\d.]+)px\\)/);
        var cc=Math.round((parseFloat(m[1])-gap)/(cell+gap));
        var rr=Math.round((parseFloat(m[2])-gap)/(cell+gap));
        if(rr===%d&&cc===%d) want=t;
      });
      if(want){want.click(); return want.textContent;}
      return null;
    })();
    """ % (r, c))

def steps():
    return peval("document.getElementById('v6aPSteps').textContent")

print("\n=== Test 1: two consecutive single moves ===")
s0 = blank_and_occ()
br, bc = map(int, s0["blank"].split(","))
# click a neighbor
nr = br+1 if br < s0["nn"]-1 else br-1
print("blank", s0["blank"], "-> click", (nr,bc), "tile", click_at(nr, bc))
time.sleep(0.3)
print("steps", steps(), "blank now", blank_and_occ()["blank"])
# click another neighbor (same tile region) to prove fix
s1 = blank_and_occ()
br, bc = map(int, s1["blank"].split(","))
nr = br-1 if br > 0 else br+1
print("click", (nr,bc), "tile", click_at(nr, bc))
time.sleep(0.3)
print("steps", steps(), "blank now", blank_and_occ()["blank"])

print("\n=== Test 2: 3-tile horizontal/vertical chain ===")
s2 = blank_and_occ()
print("blank", s2["blank"])
br, bc = map(int, s2["blank"].split(","))
# choose a tile 2 positions away same column if possible
if br <= s2["nn"]-3:
    tr, tc = br+2, bc
elif br >= 2:
    tr, tc = br-2, bc
elif bc <= s2["nn"]-3:
    tr, tc = br, bc+2
else:
    tr, tc = br, bc-2
print("click far tile", (tr,tc), "=", click_at(tr, tc))
time.sleep(0.5)
print("steps", steps(), "blank now", blank_and_occ()["blank"])

p.close()
print("\nDONE")
