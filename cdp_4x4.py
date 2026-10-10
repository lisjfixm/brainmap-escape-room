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

# Switch to 4x4
peval("document.querySelector('.v6a-modeseg [data-n=\"4\"]').click();")
time.sleep(1.2)
print("Tiles in 4x4:", peval("document.querySelectorAll('.v6a-tile').length"))

def full_state():
    return peval("""
    (function(){
      var grid=document.getElementById('v6aPGrid');
      var tiles=Array.from(grid.querySelectorAll('.v6a-tile'));
      var nn=tiles.length===8?3:4;
      var cell=tiles[0].offsetWidth, gap=8;
      var rows=[];
      for(var r=0;r<nn;r++){
        var row=[];
        for(var q=0;q<nn;q++){
          var found=null;
          tiles.forEach(function(t){
            var m=t.style.transform.match(/translate\\(([\\d.]+)px,\\s*([\\d.]+)px\\)/);
            var cc=Math.round((parseFloat(m[1])-gap)/(cell+gap));
            var rr=Math.round((parseFloat(m[2])-gap)/(cell+gap));
            if(rr===r&&cc===q) found=t.textContent;
          });
          row.push((found||'.').padStart(2));
        }
        rows.push(row.join(' '));
      }
      return rows.join('\\n');
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

print("Before:\n" + full_state())
# Find blank
fs = full_state()
for r, line in enumerate(fs.split("\n")):
    cells = line.split()
    if "." in cells[0] or "." in cells:
        br, bc = r, cells.index([c for c in cells if "." in c][0])
        break
print("blank:", (br, bc))
# click a tile 3 positions away (4-chain)
if br <= 0:
    tr, tc = br+3, bc
elif br >= 3:
    tr, tc = br-3, bc
elif bc <= 0:
    tr, tc = br, bc+3
else:
    tr, tc = br, bc-3
print("click far tile", (tr,tc), "=", click_at(tr, tc))
time.sleep(0.5)
print("After:\n" + full_state())
print("steps:", peval("document.getElementById('v6aPSteps').textContent"))

# Screenshot
r = pmsg("Page.captureScreenshot", {"format": "png"})
with open("/home/user/Doubao/chats/38443931837314306/puzzle_4x4.png", "wb") as f:
    f.write(base64.b64decode(r["data"]))
print("Screenshot saved")
p.close()
