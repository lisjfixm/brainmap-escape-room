import json
import time
import websocket
import urllib.request
import base64

def gv():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/version") as r:
        return json.load(r)["webSocketDebuggerUrl"]
def gt():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
        return json.load(r)

# fresh tab
b = websocket.create_connection(gv(), timeout=15, origin="http://127.0.0.1")
bid=0
def bsend(m,p=None):
    global bid
    bid+=1
    b.send(json.dumps({"id":bid,"method":m,"params":p or {}}))
    return bid
def bwait(w):
    while True:
        d=json.loads(b.recv())
        if d.get("id")==w: return d
r=bwait(bsend("Target.createTarget",{"url":"file:///home/user/Doubao/chats/38443931837314306/脑图密室逃脱 V6.0.1.html"}))
tid=r["result"]["targetId"]
b.close()
time.sleep(8)

p = websocket.create_connection("ws://127.0.0.1:9222/devtools/page/"+tid, timeout=20, origin="http://127.0.0.1")
pid=0
def peval(e):
    global pid
    pid+=1
    p.send(json.dumps({"id":pid,"method":"Runtime.evaluate","params":{"expression":e,"returnByValue":True,"userGesture":True}}))
    while True:
        d=json.loads(p.recv())
        if d.get("id")==pid:
            r=d.get("result",{})
            if "exceptionDetails" in r: return "EXC:"+str(r["exceptionDetails"].get("exception",{}).get("description","?"))[:200]
            return r.get("result",{}).get("value")
def shot(name):
    global pid
    pid+=1
    p.send(json.dumps({"id":pid,"method":"Page.captureScreenshot","params":{"format":"png"}}))
    while True:
        d=json.loads(p.recv())
        if d.get("id")==pid:
            with open(name,"wb") as f: f.write(base64.b64decode(d["result"]["data"]))
            return

peval("HomeRoom.enter();")
time.sleep(1.5)
peval("V6.Home.showWing('annex');")
time.sleep(1.5)
# Check overlays in DOM after switching wing (should be none)
print("overlays in DOM:", peval("document.querySelectorAll('.v6-overlay').length"))
# Now click item codex node and IMMEDIATELY check overlay count
peval("""
(function(){
  var n=G.nodes.find(function(n){return n.id==='v6r_v6_item_codex'});
  n.onClick(n);
})();
""")
time.sleep(0.3)
print("overlays 0.3s after click:", peval("document.querySelectorAll('.v6-overlay').length"))
print("overlay ids:", peval("Array.from(document.querySelectorAll('.v6-overlay')).map(function(o){return o.id+':'+o.classList.contains('show')}).join(',')"))
time.sleep(1)
shot("/home/user/Doubao/chats/38443931837314306/step_codex.png")
print("screenshot done")
p.close()
