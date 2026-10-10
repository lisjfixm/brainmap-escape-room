import json
import time
import websocket
import urllib.request
import base64

def get_targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
        return json.load(r)

targets = get_targets()
page = next(t for t in targets if t["type"] == "page" and "about:blank" not in t["url"])
p = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=20, origin="http://127.0.0.1")
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
    if "exceptionDetails" in r: return "EXC"
    return r.get("result", {}).get("value")

# Verify transition style is applied
transition = peval("getComputedStyle(document.querySelector('.v6a-tile')).transition")
print("Tile transition:", transition)

# Reset then click and capture mid-animation
peval("document.querySelector('.v6a-modeseg [data-n=\"3\"]').click();")
time.sleep(1)
# click far tile and screenshot ~90ms later
peval("""
(function(){
  var grid=document.getElementById('v6aPGrid');
  var tiles=Array.from(grid.querySelectorAll('.v6a-tile'));
  var cell=tiles[0].offsetWidth, gap=8;
  var occ={};
  tiles.forEach(function(t){
    var m=t.style.transform.match(/translate\\(([\\d.]+)px,\\s*([\\d.]+)px\\)/);
    var cc=Math.round((parseFloat(m[1])-gap)/(cell+gap));
    var rr=Math.round((parseFloat(m[2])-gap)/(cell+gap));
    occ[rr+','+cc]=t;
  });
  var br=-1,bc=-1;
  for(var r=0;r<3;r++)for(var q=0;q<3;q++){ if(!occ[r+','+q]){br=r;bc=q;} }
  var t = br<=0 ? occ['2,'+bc] : occ['0,'+bc];
  t.click();
})();
""")
time.sleep(0.09)
r = pmsg("Page.captureScreenshot", {"format": "png"})
with open("/home/user/Doubao/chats/38443931837314306/puzzle_midanim.png", "wb") as f:
    f.write(base64.b64decode(r["data"]))
print("Mid-animation screenshot saved")
p.close()
