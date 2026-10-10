import json, websocket, urllib.request
with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
    targets = json.load(r)
game = next(t for t in targets if t["type"]=="page" and "about:blank" not in t["url"])
p = websocket.create_connection(game["webSocketDebuggerUrl"], timeout=20, origin="http://127.0.0.1")
pid=0
def peval(expr):
    global pid
    pid+=1
    p.send(json.dumps({"id":pid,"method":"Runtime.evaluate","params":{"expression":expr,"returnByValue":True,"userGesture":True}}))
    while True:
        d=json.loads(p.recv())
        if d.get("id")==pid:
            r=d.get("result",{})
            if "exceptionDetails" in r: return "EXC:"+str(r["exceptionDetails"])[:200]
            return r.get("result",{}).get("value")
# List all top-level overlays and their classes
print("Visible overlays:")
print(peval("""
(function(){
  var out=[];
  document.querySelectorAll('body > *').forEach(function(el){
    var cs=getComputedStyle(el);
    if((cs.position==='fixed'||cs.position==='absolute') && el.offsetParent!==null){
      out.push(el.className.toString().slice(0,50)+' | id='+el.id);
    }
  });
  return out.join('\\n');
})();
"""))
p.close()
