import json, time, websocket, urllib.request, base64

def gv():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/version") as r:
        return json.load(r)["webSocketDebuggerUrl"]
b=websocket.create_connection(gv(),timeout=15,origin="http://127.0.0.1")
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
r=bwait(bsend("Target.createTarget",{"url":"about:blank"}))
tid=r["result"]["targetId"]
b.close()

p=websocket.create_connection("ws://127.0.0.1:9222/devtools/page/"+tid,timeout=20,origin="http://127.0.0.1")
pid=0
def pmsg(m,params=None):
    global pid
    pid+=1
    p.send(json.dumps({"id":pid,"method":m,"params":params or {}}))
    while True:
        d=json.loads(p.recv())
        if d.get("id")==pid: return d.get("result",d.get("error"))
def peval(e):
    r=pmsg("Runtime.evaluate",{"expression":e,"returnByValue":True,"userGesture":True})
    if "exceptionDetails" in r: return "EXC:"+str(r["exceptionDetails"].get("exception",{}).get("description","?"))[:200]
    return r.get("result",{}).get("value")
def shot(name):
    r=pmsg("Page.captureScreenshot",{"format":"png"})
    with open(name,"wb") as f: f.write(base64.b64decode(r["data"]))

pmsg("Emulation.setDeviceMetricsOverride",{"width":375,"height":812,"deviceScaleFactor":3,"mobile":True})
pmsg("Page.navigate",{"url":"file:///home/user/Doubao/chats/38443931837314306/脑图密室逃脱 V6.0.1.html"})
time.sleep(8)
peval("HomeRoom.enter();")
time.sleep(1.5)
peval("V6.Home.showWing('attic');")
time.sleep(1.2)
peval("""
(function(){
  var n=G.nodes.find(function(n){return n.id==='v6r_v6_gacha'});
  n.onClick(n);
})();
""")
time.sleep(1.5)
# check panels
print("panels:", peval("""
(function(){
  var out=[];
  document.querySelectorAll('.v6-overlay').forEach(function(o){
    out.push({id:o.id, show:o.classList.contains('show')});
  });
  return JSON.stringify(out);
})();
"""))
shot("/home/user/Doubao/chats/38443931837314306/g2_open.png")
# pull
clicked = peval("""
(function(){
  var btn=document.getElementById('v6aPull');
  if(!btn) return 'no btn';
  btn.click();
  return 'clicked';
})();
""")
print("pull:", clicked)
time.sleep(0.3)
print("panels 0.3s after pull:", peval("""
(function(){
  var out=[];
  document.querySelectorAll('.v6-overlay').forEach(function(o){
    out.push({id:o.id, show:o.classList.contains('show')});
  });
  return JSON.stringify(out);
})();
"""))
time.sleep(1.2)
print("panels 1.5s after pull:", peval("""
(function(){
  var out=[];
  document.querySelectorAll('.v6-overlay').forEach(function(o){
    out.push({id:o.id, show:o.classList.contains('show')});
  });
  return JSON.stringify(out);
})();
"""))
shot("/home/user/Doubao/chats/38443931837314306/g2_after.png")
p.close()
