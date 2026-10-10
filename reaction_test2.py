import json, time, websocket, urllib.request, base64

def gt():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
        return json.load(r)
def quick(tid):
    try:
        pp=websocket.create_connection("ws://127.0.0.1:9222/devtools/page/"+tid,timeout=8,origin="http://127.0.0.1")
        pp._id=0
        def ev(e):
            pp._id+=1
            i=pp._id
            pp.send(json.dumps({"id":i,"method":"Runtime.evaluate","params":{"expression":e,"returnByValue":True}}))
            while True:
                d=json.loads(pp.recv())
                if d.get("id")==i: return d.get("result",{}).get("result",{}).get("value")
        w=ev("window.innerWidth"); pp.close(); return w
    except Exception: return None
mobile_id=None
for t in gt():
    if t["type"]=="page" and "about:blank" not in t["url"] and quick(t["id"])==375:
        mobile_id=t["id"]; break
p=websocket.create_connection("ws://127.0.0.1:9222/devtools/page/"+mobile_id,timeout=20,origin="http://127.0.0.1")
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
    if "exceptionDetails" in r: return "EXC:"+str(r["exceptionDetails"])[:150]
    return r.get("result",{}).get("value")
def shot(name):
    r=pmsg("Page.captureScreenshot",{"format":"png"})
    with open(name,"wb") as f: f.write(base64.b64decode(r["data"]))

# Reopen reaction
peval("V6.Panel.closeAll();")
time.sleep(0.5)
peval("V6.Home.showWing('attic');")
time.sleep(1)
peval("""
(function(){
  var n=G.nodes.find(function(n){return n.id==='v6r_v6_game_reaction'});
  n.onClick(n);
})();
""")
time.sleep(1.2)
# click the actual stage
print("stage found:", peval("document.getElementById('v6aRStage') ? document.getElementById('v6aRStage').className : 'MISSING'"))
peval("document.getElementById('v6aRStage').click();")
time.sleep(0.5)
print("After click stage:", peval("""
(function(){
  var s=document.getElementById('v6aRStage');
  return JSON.stringify({cls:s.className, big:document.getElementById('v6aRBig').textContent});
})();
"""))
shot("/home/user/Doubao/chats/38443931837314306/reaction_wait2.png")
# Wait for it to turn green (max 3.6s)
print("waiting for green...")
time.sleep(3)
print("State:", peval("""
(function(){
  var s=document.getElementById('v6aRStage');
  return JSON.stringify({cls:s.className, big:document.getElementById('v6aRBig').textContent});
})();
"""))
shot("/home/user/Doubao/chats/38443931837314306/reaction_go.png")
p.close()
