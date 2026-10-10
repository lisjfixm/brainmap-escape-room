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
                return "EXC:"+str(r["exceptionDetails"].get("exception",{}).get("description","?"))[:200]
            return r.get("result",{}).get("value")

# Close panels
peval("V6.Panel.closeAll();")
time.sleep(0.5)
# Show annex
peval("V6.Home.showWing('annex');")
time.sleep(1.2)

# For each v6r node, read its index in G.nodes and the room id mapping
print("=== Current v6r nodes and their geometric position ===")
print(peval("""
(function(){
  var list=G.nodes.filter(function(n){return (n.id||'').indexOf('v6r_')!==-1});
  return list.map(function(n){
    return n.id + ' @ x='+Math.round(n.x)+',y='+Math.round(n.y);
  }).join('\\n');
})();
"""))

# Now check the room order in ROOMS.annex
print("\n=== ROOMS.annex order (this drives addV6Nodes) ===")
print(peval("""
(function(){
  return V6.Home.rooms.annex.map(function(r,i){
    return i+': '+r.id+' ('+r.label+')';
  }).join('\\n');
})();
"""))

# Manually click each node and read the resulting panel title
print("\n=== Click each node -> actual panel title ===")
def click_and_title(node_id):
    peval("V6.Panel.closeAll();")
    time.sleep(0.4)
    peval("""
    (function(){
      var n=G.nodes.find(function(n){return n.id==='"""+node_id+"""' });
      if(n&&n.onClick)n.onClick(n);
    })();
    """)
    time.sleep(0.9)
    return peval("""
    (function(){
      var t=null;
      document.querySelectorAll('.v6-panel-title, .panel-title, [class*="title"]').forEach(function(el){
        if(el.offsetParent!==null && !t) t=el.textContent;
      });
      return t;
    })();
    """)

node_ids = peval("""
G.nodes.filter(function(n){return (n.id||'').indexOf('v6r_')!==-1}).map(function(n){return n.id}).join(',');
""")
for nid in node_ids.split(","):
    title = click_and_title(nid)
    print(nid + "  ->  " + str(title))

peval("V6.Panel.closeAll();")
p.close()
