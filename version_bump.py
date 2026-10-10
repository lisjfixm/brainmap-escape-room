path = "/home/user/Doubao/chats/38443931837314306/脑图密室逃脱 V6.0.0.html"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

# Player-visible version strings (6 spots)
repls = [
    ('<title>幽冥密室 · 脑图密室逃脱 V6.0.0</title>',
     '<title>幽冥密室 · 脑图密室逃脱 V6.0.1</title>'),
    ('<span id="aboutVersionSpan" style="color:#fff;cursor:pointer;user-select:none;">V6.0.0</span>',
     '<span id="aboutVersionSpan" style="color:#fff;cursor:pointer;user-select:none;">V6.0.1</span>'),
    ('<div class="loading-version" id="loadingVersion">V6.0.0</div>',
     '<div class="loading-version" id="loadingVersion">V6.0.1</div>'),
    ('// Version: V6.0.0  (2026-10-04)',
     '// Version: V6.0.1  (2026-10-08)'),
    ('<div class="version-display">脑图密室逃脱 V6.0.0</div>',
     '<div class="version-display">脑图密室逃脱 V6.0.1</div>'),
    ('<div id="versionWatermark">幽冥密室 V6.0.0</div>',
     '<div id="versionWatermark">幽冥密室 V6.0.1</div>'),
]
for old, new in repls:
    assert old in c, "missing: " + old
    c = c.replace(old, new, 1)

# Insert V6.0.1 changelog before the V6.0.0 entry in About dialog
anchor = '            <b style="color:#a8d8ff;">【V6.0.0 更新日誌】'
new_entry = ('            <b style="color:#a8d8ff;">【V6.0.1 更新日誌】閣樓「數字華容道」體驗優化</b><br>'
    '· 方塊移動改為平滑滑動動畫（絕對定位 + transform，0.2s 緩動），不再瞬間跳變<br>'
    '· 支援同行／同列多個方塊聯動：點擊遠處方塊時，2 個、3 個方塊一起滑動過去<br>'
    '· 修復方塊移動後再次點擊失效的問題（點擊時動態定位）<br><br>')
assert anchor in c
c = c.replace(anchor, new_entry + anchor, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(c)
print("Version updated to V6.0.1")
