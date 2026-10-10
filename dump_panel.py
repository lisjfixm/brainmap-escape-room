import json
import time
import websocket
import urllib.request

def get_targets():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
        return json.load(r)

targets = get_targets()
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
            if "exceptionDetails" in r:
                return "EXC:"+str(r["exceptionDetails"].get("exception",{}).get("description","?"))[:300]
            return r.get("result",{}).get("value")

peval("V6.Panel.closeAll();")
time.sleep(0.4)
peval("V6.Home.showWing('annex');")
time.sleep(1.2)
# Click item codex
peval("""
(function(){
  var n=G.nodes.find(function(n){return n.id==='v6r_v6_item_codex'});
  n.onClick(n);
})();
""")
time.sleep(1.2)

# Dump ALL visible fixed/absolute elements, no class filter
print("=== ALL visible positioned overlays ===")
print(peval("""
(function(){
  var out=[];
  document.querySelectorAll('body > *').forEach(function(el){
    var cs=getComputedStyle(el);
    if((cs.position==='fixed'||cs.position==='absolute') && el.offsetParent!==null){
      var r=el.getBoundingClientRect();
      if(r.width>50 && r.height>50){
        out.push(el.tagName+' class="'+el.className.toString().slice(0,60)+'" id="'+el.id+'" '+Math.round(r.width)+'x'+Math.round(r.height));
      }
    }
  });
  return out.join('\\n');
})();
"""))
p.close()
