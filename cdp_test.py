import json
import time
import websocket

PAGE_WS = "ws://127.0.0.1:9222/devtools/page/2AEB7B8C8CF2C455EBD9B3B37F16C51C"

class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=20, origin="http://127.0.0.1")
        self._id = 0
    def eval(self, expr):
        self._id += 1
        myid = self._id
        self.ws.send(json.dumps({"id": myid, "method": "Runtime.evaluate",
            "params": {"expression": expr, "returnByValue": True, "userGesture": True}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == myid:
                r = msg.get("result", {})
                if "exceptionDetails" in r:
                    return "EXC: " + r["exceptionDetails"].get("text", "")
                return r.get("result", {}).get("value")
    def close(self):
        self.ws.close()

c = CDP(PAGE_WS)

# Verify page loaded
print("Loaded:", c.eval("typeof V6 !== 'undefined' ? 'yes' : 'no'"))

# Enter home, switch attic, open puzzle
c.eval("HomeRoom.enter();")
time.sleep(1.5)
c.eval("document.querySelector('[data-wing=\"attic\"]').click();")
time.sleep(1.3)
c.eval("var n=G.nodes.find(function(n){return n.id==='v6r_v6_game_puzzle'});n.onClick(n);")
time.sleep(1.2)
print("Tiles:", c.eval("document.querySelectorAll('.v6a-tile').length"))

# Helper: get blank position and tile layout
def get_layout():
    return c.eval("""
    (function(){
      var grid=document.getElementById('v6aPGrid');
      var tiles=Array.from(grid.querySelectorAll('.v6a-tile'));
      var n=tiles.length===8?3:4;
      var cell=tiles[0].offsetWidth, gap=8;
      var occ={};
      tiles.forEach(function(t){
        var m=t.style.transform.match(/translate\\(([\\d.]+)px,\\s*([\\d.]+)px\\)/);
        var cc=Math.round((parseFloat(m[1])-gap)/(cell+gap));
        var rr=Math.round((parseFloat(m[2])-gap)/(cell+gap));
        occ[rr+','+cc]=t.textContent;
      });
      for(var r=0;r<n;r++)for(var q=0;q<n;q++){ if(!occ[r+','+q]) return {blank:r+','+q, n:n}; }
    })();
    """)

# Test single move
lay = get_layout()
print("Initial blank:", lay)
# Click tile adjacent to blank
clicked = c.eval("""
(function(){
  var grid=document.getElementById('v6aPGrid');
  var tiles=Array.from(grid.querySelectorAll('.v6a-tile'));
  var cell=tiles[0].offsetWidth, gap=8;
  var occ={};
  tiles.forEach(function(t){
    var m=t.style.transform.match(/translate\\(([\\d.]+)px,\\s*([\\d.]+)px\\)/);
    var cc=Math.round((parseFloat(m[1])-gap)/(cell+gap));
    var rr=Math.round((parseFloat(m[2])-gap)/(cell+gap));
    occ[rr+','+cc]=t;
  });
  var br=-1,bc=-1;
  for(var r=0;r<3;r++)for(var q=0;q<3;q++){ if(!occ[r+','+q]){br=r;bc=q;} }
  var t = br<2 ? occ[(br+1)+','+bc] : occ[(br-1)+','+bc];
  t.click();
  return t.textContent;
})();
""")
time.sleep(0.4)
print("Clicked tile:", clicked, "-> steps:", c.eval("document.getElementById('v6aPSteps').textContent"))
print("New blank:", get_layout())

# Test multi-tile chain (click tile 2 positions away, same column)
chain = c.eval("""
(function(){
  var grid=document.getElementById('v6aPGrid');
  var tiles=Array.from(grid.querySelectorAll('.v6a-tile'));
  var cell=tiles[0].offsetWidth, gap=8;
  var occ={};
  tiles.forEach(function(t){
    var m=t.style.transform.match(/translate\\(([\\d.]+)px,\\s*([\\d.]+)px\\)/);
    var cc=Math.round((parseFloat(m[1])-gap)/(cell+gap));
    var rr=Math.round((parseFloat(m[2])-gap)/(cell+gap));
    occ[rr+','+cc]=t;
  });
  var br=-1,bc=-1;
  for(var r=0;r<3;r++)for(var q=0;q<3;q++){ if(!occ[r+','+q]){br=r;bc=q;} }
  var t = br===2 ? occ['0,'+bc] : occ['2,'+bc];
  t.click();
  return {clicked:t.textContent, fromBlank:br+','+bc};
})();
""")
time.sleep(0.5)
print("3-chain click:", chain)
print("Steps after 3-chain:", c.eval("document.getElementById('v6aPSteps').textContent"))

# Check no console errors by verifying tiles still intact
print("Tiles after chain:", c.eval("document.querySelectorAll('.v6a-tile').length"))
c.close()
print("DONE")
