import json, time, websocket, urllib.request

def gt():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
        return json.load(r)
targets = gt()
# open memory match fresh - find existing tab with the game or create
game = None
for t in targets:
    if t["type"]=="page" and "about:blank" not in t["url"]:
        game = t
        break
if not game:
    print("no game tab")
    raise SystemExit
p = websocket.create_connection(game["webSocketDebuggerUrl"], timeout=20, origin="http://127.0.0.1")
pid=0
def peval(e):
    global pid
    pid+=1
    p.send(json.dumps({"id":pid,"method":"Runtime.evaluate","params":{"expression":e,"returnByValue":True,"userGesture":True}}))
    while True:
        d=json.loads(p.recv())
        if d.get("id")==pid:
            r=d.get("result",{})
            if "exceptionDetails" in r: return "EXC:"+str(r["exceptionDetails"])[:200]
            return r.get("result",{}).get("value")

# ensure memory match open
peval("V6.Panel.closeAll();")
time.sleep(0.5)
peval("V6.Home.showWing('attic');")
time.sleep(1)
peval("""
(function(){
  var n=G.nodes.find(function(n){return n.id==='v6r_v6_game_memory'});
  n.onClick(n);
})();
""")
time.sleep(1.2)

# measure
info = peval("""
(function(){
  var ov=null;
  document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
  var sheet=ov.querySelector('.v6-sheet');
  var body=ov.querySelector('.v6-sheet-body');
  var cards=body.querySelectorAll('.v6m-card, [class*="card"]');
  var grid=body.querySelector('.v6m-grid, [class*="grid"]');
  return JSON.stringify({
    sheetH: sheet.offsetHeight,
    winH: window.innerHeight,
    bodyScrollH: body.scrollHeight,
    bodyClientH: body.clientHeight,
    canScroll: body.scrollHeight > body.clientHeight,
    cardCount: cards.length,
    firstCard: cards[0] ? {w:cards[0].offsetWidth, h:cards[0].offsetHeight} : null,
    gridClass: grid ? grid.className : null
  });
})();
""")
print(info)

# Try scrolling to bottom
peval("""
(function(){
  var ov=null;
  document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
  var body=ov.querySelector('.v6-sheet-body');
  body.scrollTop = body.scrollHeight;
})();
""")
time.sleep(0.5)
print("after scroll, scrollTop:", peval("""
(function(){
  var ov=null;
  document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
  var body=ov.querySelector('.v6-sheet-body');
  return body.scrollTop;
})();
"""))
p.close()
