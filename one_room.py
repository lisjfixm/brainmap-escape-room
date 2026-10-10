import json, sys, time, websocket, urllib.request, base64

def gv():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/version") as r:
        return json.load(r)["webSocketDebuggerUrl"]

def create_tab(url):
    b = websocket.create_connection(gv(), timeout=15, origin="http://127.0.0.1")
    bid=0
    def send(m,p=None):
        nonlocal bid
        bid+=1
        b.send(json.dumps({"id":bid,"method":m,"params":p or {}}))
        return bid
    def wait(w):
        while True:
            d=json.loads(b.recv())
            if d.get("id")==w: return d
    r=wait(send("Target.createTarget",{"url":url}))
    b.close()
    return r["result"]["targetId"]

def connect(tid):
    return websocket.create_connection("ws://127.0.0.1:9222/devtools/page/"+tid, timeout=15, origin="http://127.0.0.1")

def peval(p, e):
    p._id = getattr(p, "_id", 0) + 1
    myid = p._id
    p.send(json.dumps({"id":myid,"method":"Runtime.evaluate","params":{"expression":e,"returnByValue":True,"userGesture":True}}))
    while True:
        d=json.loads(p.recv())
        if d.get("id")==myid:
            r=d.get("result",{})
            if "exceptionDetails" in r:
                return "EXC:"+str(r["exceptionDetails"].get("exception",{}).get("description","?"))[:200]
            return r.get("result",{}).get("value")

def shot(p, name):
    p._id += 1
    myid = p._id
    p.send(json.dumps({"id":myid,"method":"Page.captureScreenshot","params":{"format":"png"}}))
    while True:
        d=json.loads(p.recv())
        if d.get("id")==myid:
            with open(name,"wb") as f: f.write(base64.b64decode(d["result"]["data"]))
            return

def is_alive(tid):
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
            targets = json.load(r)
        return any(t["id"]==tid for t in targets)
    except Exception:
        return False

wing, rid = sys.argv[1], sys.argv[2]
url = "file:///home/user/Doubao/chats/38443931837314306/脑图密室逃脱 V6.0.1.html"
tid = create_tab(url)
time.sleep(8)
if not is_alive(tid):
    print("CRASH ON LOAD")
    sys.exit(1)

p = connect(tid)
try:
    peval(p, "HomeRoom.enter();")
    time.sleep(1.5)
    peval(p, "V6.Home.showWing('"+wing+"');")
    time.sleep(1)
    peval(p, """
    (function(){
      var n=G.nodes.find(function(n){return n.id==='v6r_"""+rid+"""' });
      if(n&&n.onClick)n.onClick(n);
    })();
    """)
    time.sleep(1.3)
    info = peval(p, """
    (function(){
      var ov=null;
      document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
      if(!ov) return JSON.stringify({open:false});
      var b=ov.querySelector('.v6-sheet-body');
      return JSON.stringify({open:true,title:(ov.querySelector('.v6-sheet-title')||{}).textContent,
        bodyLen:b.innerHTML.length, btns:b.querySelectorAll('button').length, inputs:b.querySelectorAll('input').length});
    })();
    """)
    shot(p, "/home/user/Doubao/chats/38443931837314306/one_%s.png" % rid)
    print("ROOM", wing, rid, "->", info)
finally:
    p.close()
