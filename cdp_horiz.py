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

# Reset puzzle to get a known layout
peval("document.getElementById('v6aPlReset').click();")
time.sleep(1)

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
          row.push(found||'.');
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

def blankpos():
    fs = full_state()
    for r, line in enumerate(fs.split("\n")):
        if "." in line.split():
            return r, line.split().index(".")
    return None

print("=== Horizontal chain test ===")
print("Before:\n" + full_state())
br, bc = blankpos()
# click tile 2 positions horizontally away
if bc <= 0:
    tc = bc+2
elif bc >= 2:
    tc = bc-2
else:
    tc = 0 if bc==2 else 2
print("blank", (br,bc), "click", (br,tc), "tile", click_at(br, tc))
time.sleep(0.5)
print("After horizontal chain:\n" + full_state())
print("steps:", peval("document.getElementById('v6aPSteps').textContent"))

print("\n=== Screenshot ===")
r = pmsg("Page.captureScreenshot", {"format": "png"})
img = base64.b64decode(r["data"])
with open("/home/user/Doubao/chats/38443931837314306/puzzle_3x3.png", "wb") as f:
    f.write(img)
print("Saved screenshot")

p.close()
