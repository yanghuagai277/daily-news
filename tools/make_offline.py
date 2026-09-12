# -*- coding: utf-8 -*-
"""从 index.html 生成离线单文件 news-offline.html。

规则（务必遵守，历史踩坑见下）：
1. 去掉 manifest 引用（file:// 下无意义）。
2. 只【精确】移除 Service Worker 注销的那个 try 块（以 navigator.serviceWorker 为锚点）。
3. 绝对禁止按「脚本块是否含 serviceWorker 关键字」整块删除 <script>！

历史 Bug：旧版脚本只要某个 <script> 块里出现 "serviceWorker" 字样就整块删掉，
而 index.html 里「渲染逻辑 + SW 注销」恰好同处一个 <script> 块，
导致离线文件丢失全部渲染代码，打开只有标题、新闻区永远空白（用户多日"看不了"的根因）。

因此生成后做「渲染完整性校验」：结果必须仍包含核心渲染函数，否则中止写入（不产出坏文件）。
"""
import re
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
HTML = BASE / "index.html"
OUT = BASE / "news-offline.html"

h = HTML.read_text(encoding="utf-8")

# 1) 去掉 manifest 引用
h = re.sub(r"<link[^>]*manifest\.webmanifest[^>]*>", "", h, flags=re.I)

# 2) 只精确移除 SW 注销 try 块（不碰渲染脚本）
h = re.sub(
    r"try\s*\{\s*if\s*\(\s*navigator\.serviceWorker[\s\S]*?\}\s*catch\s*\(e\)\s*\{\s*\}",
    "",
    h,
)

# 3) 完整性校验：渲染逻辑必须仍在，否则判定失败
MUST = ["getElementById", "innerHTML", "addEventListener", "renderList", "window.__DATA__"]
missing = [k for k in MUST if k not in h]
if missing:
    print("FATAL: 渲染逻辑丢失，已中止写入（不产出坏文件）。缺失:", missing)
    sys.exit(1)

OUT.write_text(h, encoding="utf-8")
print("offline written, bytes =", len(h.encode("utf-8")))
print("manifest link removed:", "manifest.webmanifest" not in h)
print("serviceWorker removed:", "serviceWorker" not in h)
print("render intact:", all(k in h for k in MUST))
