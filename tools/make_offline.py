# -*- coding: utf-8 -*-
"""从 index.html 生成离线单文件 news-offline.html。

去掉 manifest 引用与 Service Worker 相关脚本块（含注册与注销逻辑），
其余（含内联 window.__DATA__）原样保留，确保 file:// 打开零网络依赖。
"""
import re
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
HTML = BASE / "index.html"
OUT = BASE / "news-offline.html"

h = HTML.read_text(encoding="utf-8")

# 1) 去掉 manifest 引用
h = re.sub(r"<link[^>]*manifest\.webmanifest[^>]*>", "", h, flags=re.I)

# 2) 逐块处理 <script>...</script>，仅剔除内容含 serviceWorker 的脚本块
SCRIPT_RE = re.compile(r"<script\b[^>]*>([\s\S]*?)</script>", re.I)

def _strip(m):
    return "" if "serviceWorker" in m.group(1) else m.group(0)

h = SCRIPT_RE.sub(_strip, h)

OUT.write_text(h, encoding="utf-8")
print("offline written, bytes =", len(h.encode("utf-8")))
print("manifest link removed:", "manifest.webmanifest" not in h)
print("no serviceWorker block:", "serviceWorker" not in h)
print("has inline __DATA__:", "window.__DATA__" in h)
