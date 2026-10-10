import json, time, websocket, urllib.request, base64

def gt():
    with urllib.request.urlopen("http://127.0.0.1:9222/json/list") as r:
        return json.load(r)
targets = gt()
game = next(t for t in targets if t["type"]=="page" and "about:blank" not in t["url"])
p = websocket.create_connection(game["webSocketDebuggerUrl"], timeout=20, origin="http://127.0.0.1")
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
    if "exceptionDetails" in r:
        return "EXC:"+str(r["exceptionDetails"].get("exception",{}).get("description","?"))[:250]
    return r.get("result",{}).get("value")
def shot(name):
    r=pmsg("Page.captureScreenshot",{"format":"png"})
    with open(name,"wb") as f: f.write(base64.b64decode(r["data"]))

# Open memory match
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

# Scroll to top, click first card
peval("""
(function(){
  var ov=null;
  document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
  var body=ov.querySelector('.v6-sheet-body');
  body.scrollTop=0;
  var card=body.querySelector('#v6aMGrid .v6a-memcard');
  card.click();
})();
""")
time.sleep(0.8)
# check first card flipped
flipped = peval("""
(function(){
  var ov=null;
  document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
  var cards=ov.querySelectorAll('#v6aMGrid .v6a-memcard');
  return Array.from(cards).map(function(c){return c.classList.contains('flip')||c.classList.contains('got')?'1':'0'}).join('');
})();
""")
print("Cards flipped state (1=flipped):", flipped)
shot("/home/user/Doubao/chats/38443931837314306/mem_flip.png")

# Click second card
peval("""
(function(){
  var ov=null;
  document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
  var cards=ov.querySelectorAll('#v6aMGrid .v6a-memcard');
  cards[1].click();
})();
""")
time.sleep(0.8)
shot("/home/user/Doubao/chats/38443931837314306/mem_flip2.png")
state = peval("""
(function(){
  var ov=null;
  document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
  var cards=ov.querySelectorAll('#v6aMGrid .v6a-memcard');
  return Array.from(cards).map(function(c){
    if(c.classList.contains('got'))return 'G';
    if(c.classList.contains('flip'))return 'F';
    return '0';
  }).join('');
})();
""")
print("After 2nd card (G=got/matched, F=flipped, 0=down):", state)
p.close()
