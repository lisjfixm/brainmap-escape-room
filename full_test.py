import json
import time
import websocket
import urllib.request
import base64

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

def reset():
    peval("V6.Panel.closeAll();")
    time.sleep(0.5)

def test_room(wing, rid, label):
    reset()
    err0=len(errors)
    peval("V6.Home.showWing('"+wing+"');")
    time.sleep(1)
    peval("""
    (function(){
      var n=G.nodes.find(function(n){return n.id==='v6r_"""+rid+"""' });
      if(n&&n.onClick)n.onClick(n);
    })();
    """)
    time.sleep(1.2)
    info = peval("""
    (function(){
      var ov=null;
      document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
      if(!ov) return JSON.stringify({open:false});
      var title=(ov.querySelector('.v6-sheet-title')||{}).textContent;
      var body=ov.querySelector('.v6-sheet-body');
      var btns=body.querySelectorAll('button');
      var inputs=body.querySelectorAll('input');
      return JSON.stringify({open:true,title:title,bodyLen:body.innerHTML.length,
        btns:btns.length,inputs:inputs.length});
    })();
    """)
    drain(0.3)
    new_err=errors[err0:]
    # Test closing via X
    peval("""
    (function(){
      var ov=null;
      document.querySelectorAll('.v6-overlay').forEach(function(o){ if(o.classList.contains('show')) ov=o; });
      if(ov){ var b=ov.querySelector('.v6-sheet-close'); b.click(); }
    })();
    """)
    time.sleep(0.5)
    closed = peval("document.querySelectorAll('.v6-overlay.show').length")
    problem = []
    d = json.loads(info)
    if not d.get("open"): problem.append("NOT OPEN")
    if d.get("bodyLen",0)==0: problem.append("EMPTY")
    if new_err: problem.append("JS ERR")
    if closed != 0: problem.append("X NOT CLOSE")
    print("%-22s %-8s %s" % (rid, wing, "PROBLEM:"+",".join(problem) if problem else "OK"))
    if new_err:
        for e in new_err: print("     ", str(e)[:250])
    if problem:
        print("     info:", info)

annex=[("v6_ach_hall","成就殿堂"),("v6_item_codex","物品图鉴"),("v6_lore_archive","档案室"),
       ("v6_memory_gallery","回忆长廊"),("v6_mailbox","信箱"),("v6_journal_milestone","每日纪要"),
       ("overview","旅程总览")]
attic=[("v6_music_box","音乐盒"),("v6_gacha","扭蛋机"),("v6_fortune","占卜机"),
       ("v6_game_memory","记忆翻牌"),("v6_game_reaction","反应考验"),("v6_game_puzzle","华容道"),
       ("v6_game_cipher","密室解谜")]

print("=== ANNEX ===")
for rid,l in annex: test_room("annex",rid,l)
print("=== ATTIC ===")
for rid,l in attic: test_room("attic",rid,l)
reset()
p.close()
print("DONE")
