import json
import time
import websocket
import urllib.request
import base64

def get_targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
        return json.load(r)

targets = get_targets()
game = next(t for t in targets if t["type"]=="page" and "about:blank" not in t["url"])
p = websocket.create_connection(game["webSocketDebuggerUrl"], timeout=20, origin="http://127.0.0.1")
pid=0
def pmsg(method, params=None):
    global pid
    pid+=1
    p.send(json.dumps({"id":pid,"method":method,"params":params or {}}))
    while True:
        d=json.loads(p.recv())
        if d.get("id")==pid:
            return d.get("result",d.get("error"))
def peval(expr):
    r=pmsg("Runtime.evaluate",{"expression":expr,"returnByValue":True,"userGesture":True})
    if "exceptionDetails" in r:
        return "EXC:"+str(r["exceptionDetails"].get("exception",{}).get("description","?"))[:150]
    return r.get("result",{}).get("value")

pmsg("Runtime.enable")
p.settimeout(0.3)
errors=[]
def drain(sec):
    end=time.time()+sec
    while time.time()<end:
        try:
            d=json.loads(p.recv())
            if d.get("method")=="Runtime.exceptionThrown":
                ed=d["params"]["exceptionDetails"]
                errors.append(ed.get("exception",{}).get("description",ed.get("text","")))
        except Exception: pass
p.settimeout(20)

# Open a panel and dump its DOM tag/class structure
def open_room(wing, rid):
    peval("V6.Home.showWing('"+wing+"');")
    time.sleep(1)
    peval("""
    (function(){
      var n=G.nodes.find(function(n){return n.id==='v6r_"""+rid+"""' });
      if(n&&n.onClick)n.onClick(n);
    })();
    """)
    time.sleep(1.2)

open_room("annex","v6_item_codex")
drain(0.5)
# Dump panel DOM structure
print("Panel DOM:")
print(peval("""
(function(){
  var out=[];
  document.querySelectorAll('body > *').forEach(function(el){
    if(el.offsetParent!==null && (el.className||'').toString().indexOf('v6')!==-1){
      out.push('<'+el.tagName.toLowerCase()+' class="'+el.className+'" id="'+el.id+'">');
    }
  });
  return out.join('\\n');
})();
"""))
print("Errors:", errors)
# Screenshot
r=pmsg("Page.captureScreenshot",{"format":"png"})
with open("/home/user/Doubao/chats/38443931837314306/shot_item_codex.png","wb") as f:
    f.write(base64.b64decode(r["data"]))
print("Screenshot saved")
p.close()
