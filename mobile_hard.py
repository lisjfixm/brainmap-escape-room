import json, time, websocket, urllib.request, base64

def gt():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
        return json.load(r)
# find the mobile tab
targets = gt()
m = None
for t in targets:
    r = None
    # just try connecting; mobile tab is the one with V6.0.1 and small viewport
    pass
# We need to identify the mobile tab. There may be multiple game tabs.
# Let's just attach to the mobile one by checking window.innerWidth via quick eval
def quick(tid):
    try:
        pp = websocket.create_connection("ws://127.0.0.1:9222/devtools/page/"+tid, timeout=8, origin="http://127.0.0.1")
        pp._id=0
        def ev(e):
            pp._id+=1
            i=pp._id
            pp.send(json.dumps({"id":i,"method":"Runtime.evaluate","params":{"expression":e,"returnByValue":True}}))
            while True:
                d=json.loads(pp.recv())
                if d.get("id")==i:
                    r=d.get("result",{})
                    return r.get("result",{}).get("value")
        w = ev("window.innerWidth")
        pp.close()
        return w
    except Exception:
        return None

mobile_id=None
for t in targets:
    if t["type"]=="page" and "about:blank" not in t["url"]:
        w = quick(t["id"])
        if w == 375:
            mobile_id=t["id"]
            break
print("mobile tab:", mobile_id)

p = websocket.create_connection("ws://127.0.0.1:9222/devtools/page/"+mobile_id, timeout=20, origin="http://127.0.0.1")
pid=0
def pmsg(m,params=None):
    global pid
    pid+=1
    p.send(json.dumps({"id":pid,"method":m,"params":params or {}}))
    while True:
        d=json.loads(p.recv())
        if d.get("id")==pid:
            return d.get("result",d.get("error"))
def peval(e):
    r=pmsg("Runtime.evaluate",{"expression":e,"returnByValue":True,"userGesture":True})
    if "exceptionDetails" in r: return "EXC"
    return r.get("result",{}).get("value")
def shot(name):
    r=pmsg("Page.captureScreenshot",{"format":"png"})
    with open(name,"wb") as f: f.write(base64.b64decode(r["data"]))

# click hard 4x4
peval("""
(function(){
  var ov=null;
  document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
  var btns=ov.querySelectorAll('button');
  btns.forEach(function(b){ if((b.textContent||'').indexOf('困难')!==-1) b.click(); });
})();
""")
time.sleep(1)
print("hard 4x4:", peval("""
(function(){
  var ov=null;
  document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
  var body=ov.querySelector('.v6-sheet-body');
  var cards=ov.querySelectorAll('.v6a-memcard');
  return JSON.stringify({cards:cards.length, cardH:cards[0].offsetHeight,
    scrollH:body.scrollHeight, clientH:body.clientHeight, needScroll:body.scrollHeight>body.clientHeight});
})();
"""))
shot("/home/user/Doubao/chats/38443931837314306/mobile_mem_hard.png")
p.close()
