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
pid = 0
def pmsg(method, params=None):
    global pid
    pid += 1
    p.send(json.dumps({"id":pid,"method":method,"params":params or {}}))
    while True:
        d = json.loads(p.recv())
        if d.get("id")==pid:
            return d.get("result", d.get("error"))
def peval(expr):
    r = pmsg("Runtime.evaluate", {"expression":expr,"returnByValue":True,"userGesture":True})
    if "exceptionDetails" in r:
        return "EXC:" + json.dumps(r["exceptionDetails"].get("exception",{}).get("description","?"))[:200]
    return r.get("result",{}).get("value")

pmsg("Runtime.enable")
p.settimeout(0.3)
errors = []
def drain(seconds):
    end = time.time()+seconds
    while time.time()<end:
        try:
            d = json.loads(p.recv())
            if d.get("method")=="Runtime.exceptionThrown":
                ed = d["params"]["exceptionDetails"]
                errors.append(ed.get("exception",{}).get("description",ed.get("text","")))
        except Exception:
            pass
p.settimeout(20)

# Open room by clicking its node (id = v6r_<id>)
def open_room(wing, room_id):
    peval("V6.Home.showWing('"+wing+"');")
    time.sleep(1)
    peval("""
    (function(){
      var n=G.nodes.find(function(n){return n.id==='v6r_"""+room_id+"""' });
      if(n&&n.onClick)n.onClick(n);
    })();
    """)
    time.sleep(1)

def close_panels():
    # close all v6 panels
    peval("""
    (function(){
      if(typeof V6 !== 'undefined' && V6.Panel){ V6.Panel.closeAll(); }
    })();
    """)
    time.sleep(0.5)

# Test each annex room
annex_rooms = [
    ("v6_ach_hall","成就殿堂"),
    ("v6_item_codex","物品图鉴"),
    ("v6_lore_archive","档案室"),
    ("v6_memory_gallery","回忆长廊"),
    ("v6_mailbox","信箱"),
    ("v6_journal_milestone","每日纪要"),
    ("overview","旅程总览"),
]
attic_rooms = [
    ("v6_music_box","音乐盒"),
    ("v6_gacha","扭蛋机"),
    ("v6_fortune","占卜机"),
    ("v6_game_memory","记忆翻牌"),
    ("v6_game_reaction","反应考验"),
    ("v6_game_cipher","密室解谜"),
]

for wing, room_id, label in [("annex",r,l) for r,l in annex_rooms] + [("attic",r,l) for r,l in attic_rooms]:
    close_panels()
    err_before = len(errors)
    open_room(wing, room_id)
    # Check panel exists and content
    info = peval("""
    (function(){
      var panels=document.querySelectorAll('.v6-panel, .ach-overlay, [class*="panel"]');
      var openPanel=null;
      document.querySelectorAll('.v6-panel, .ach-overlay').forEach(function(p){ if(p.offsetParent!==null) openPanel=p; });
      var body = openPanel ? openPanel.querySelector('.v6-panel-body, .panel-body, .v6-body') : null;
      var contentLen = body ? body.innerHTML.length : 0;
      var title = openPanel ? (openPanel.querySelector('.v6-panel-title, .panel-title, .ach-panel-title')||{}).textContent : null;
      return JSON.stringify({found:!!openPanel, title:title, contentLen:contentLen});
    })();
    """)
    drain(0.3)
    new_err = errors[err_before:]
    status = "OK"
    if "EXC" in str(info) or new_err or (info and json.loads(info)["contentLen"]==0):
        status = "** PROBLEM **"
    print("%-8s %-22s %s %s" % (wing, room_id, status, info))
    if new_err:
        for e in new_err: print("     ERR:", str(e)[:200])
    # screenshot the first problem and a couple normal ones
    if status != "OK":
        r = pmsg("Page.captureScreenshot", {"format":"png"})
        fn = "/home/user/Doubao/chats/38443931837314306/problem_"+room_id+".png"
        with open(fn,"wb") as f: f.write(base64.b64decode(r["data"]))
        print("     screenshot:", fn)

close_panels()
p.close()
print("DONE")
