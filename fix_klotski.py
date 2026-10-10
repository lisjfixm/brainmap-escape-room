import re

path = "/home/user/Doubao/chats/38443931837314306/脑图密室逃脱 V6.0.0.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Anchor the puzzle block uniquely using its comment, then locate the
# registerRoom block that follows, up to the next cipher section comment.
start_marker = "     6) 數字華容 v6_game_puzzle"
end_marker = "  /* ============================================================\n     7) 密室解謎 v6_game_cipher"

si = content.find(start_marker)
assert si != -1, "puzzle start marker not found"
ei = content.find(end_marker, si)
assert ei != -1, "puzzle end marker not found"

block = content[si:ei]

# ---- 1) render() -> absolute positioning + helpers ----
new_render = '''      const GAP = 8;
      let gridEl=null, tileEls={}, cellSize=0, done=false;
      function posOf(i){
        const r=Math.floor(i/n), c=i%n;
        return { x: GAP + c*(cellSize+GAP), y: GAP + r*(cellSize+GAP) };
      }
      function render(){
        body.innerHTML =
          '<div class="v6a-modeseg">'
          + '<button data-n="3" class="'+(n===3?'on':'')+'">3×3</button>'
          + '<button data-n="4" class="'+(n===4?'on':'')+'">4×4</button>'
          + '<button id="v6aPlReset">'+V6.icon(I.refresh,15)+'打乱重开</button></div>'
          + '<div class="v6-stage-hud" style="border:1px solid rgba(255,200,120,.16);border-radius:8px;margin-bottom:10px;">'
          + '<span>步数 <b id="v6aPSteps">0</b></span><span>时间 <b id="v6aPSec">0</b>s</span>'
          + '<span style="margin-left:auto">最佳 <b id="v6aPBest"></b></span></div>'
          + '<div class="v6a-slidegrid g'+n+'" id="v6aPGrid"></div>'
          + '<div id="v6aPResult"></div>';
        body.querySelector('#v6aPBest').textContent = best['n'+n] ? best['n'+n].steps+'步/'+best['n'+n].time+'s' : '—';
        gridEl = body.querySelector('#v6aPGrid');
        tileEls = {};
        const gridW = Math.min(340, body.clientWidth - 40);
        cellSize = (gridW - GAP*(n+1)) / n;
        gridEl.style.width = gridW+'px';
        gridEl.style.height = gridW+'px';
        arr.forEach(function(v, i){
          if (v===0) return;
          const tile = document.createElement('div');
          tile.className = 'v6a-tile';
          tile.textContent = v;
          tile.style.width = cellSize+'px';
          tile.style.height = cellSize+'px';
          const p = posOf(i);
          tile.style.transform = 'translate('+p.x+'px,'+p.y+'px)';
          tile.addEventListener('click', function(){ onTile(i); });
          gridEl.appendChild(tile);
          tileEls[v] = tile;
        });
        body.querySelectorAll('.v6a-modeseg [data-n]').forEach(function(b){
          b.addEventListener('click', function(){ n=parseInt(b.getAttribute('data-n'),10); sfx('click'); init(); });
        });
        body.querySelector('#v6aPlReset').addEventListener('click', function(){ sfx('click'); init(); });
      }
      // 平滑更新：只改 transform，不重建 DOM
      function updateTiles(){
        arr.forEach(function(v, i){
          if (v===0) return;
          const tile = tileEls[v];
          if (!tile) return;
          const p = posOf(i);
          tile.style.transform = 'translate('+p.x+'px,'+p.y+'px)';
        });
      }'''

pat_render = re.compile(r'      function render\(\).*?(?=      function onTile)', re.DOTALL)
assert pat_render.search(block), "render pattern not found in block"
block = pat_render.sub(new_render + "\n", block, count=1)

# ---- 2) onTile() -> supports row/column chained sliding ----
new_onTile = '''      function onTile(i){
        if (done) return;
        if (!started){ started=true; timerId=st.every(function(){ secs++; body.querySelector('#v6aPSec').textContent=secs; },1000); }
        const blank = arr.indexOf(0);
        const r1=Math.floor(i/n), c1=i%n, r2=Math.floor(blank/n), c2=blank%n;
        if (r1===r2 && c1!==c2){
          // 同行：横向联动
          const dir = c1>c2 ? 1 : -1;
          const count = Math.abs(c1-c2);
          for (let k=0;k<count;k++){
            if (dir===1){
              const from=r1*n+(c2+k+1), to=r1*n+(c2+k);
              arr[to]=arr[from];
            } else {
              const from=r1*n+(c2-k-1), to=r1*n+(c2-k);
              arr[to]=arr[from];
            }
          }
          arr[i]=0; steps+=count;
          body.querySelector('#v6aPSteps').textContent=steps;
          sfx('click');
          updateTiles();
          if (isSolved()) win();
        } else if (c1===c2 && r1!==r2){
          // 同列：纵向联动
          const dir = r1>r2 ? 1 : -1;
          const count = Math.abs(r1-r2);
          for (let k=0;k<count;k++){
            if (dir===1){
              const from=(r2+k+1)*n+c1, to=(r2+k)*n+c1;
              arr[to]=arr[from];
            } else {
              const from=(r2-k-1)*n+c1, to=(r2-k)*n+c1;
              arr[to]=arr[from];
            }
          }
          arr[i]=0; steps+=count;
          body.querySelector('#v6aPSteps').textContent=steps;
          sfx('click');
          updateTiles();
          if (isSolved()) win();
        } else {
          sfx('error');
        }
      }'''

pat_on = re.compile(r'      function onTile\(i\).*?(?=      function win)', re.DOTALL)
assert pat_on.search(block), "onTile pattern not found in block"
block = pat_on.sub(new_onTile + "\n", block, count=1)

# ---- 3) win(): add done flag ----
block = block.replace(
    "      function win(){\n        if (timerId){ clearInterval(timerId); timerId=null; }",
    "      function win(){\n        done=true;\n        if (timerId){ clearInterval(timerId); timerId=null; }",
    1)

# ---- 4) init(): reset done ----
block = block.replace(
    "        steps=0; secs=0; started=false; shuffle(); render();",
    "        steps=0; secs=0; started=false; done=false; shuffle(); render();",
    1)

content = content[:si] + block + content[ei:]

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Puzzle block replaced correctly (within anchored range).")
