# -*- coding: utf-8 -*-
"""从 index.html 生成离线单文件 news-offline.html。

去掉 manifest 引用与 Service Worker 注册脚本块，其余（含内联 window.__DATA__）
原样保留，确保 file:// 打开零网络依赖。
"""
import re
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
HTML = BASE / "index.html"
OUT = BASE / "news-offline.html"

h = HTML.read_text(encoding="utf-8")
h = re.sub(r"<link[^>]*manifest\.webmanifest[^>]*>", "", h, flags=re.I)
h = re.sub(
    r"<script>\s*if\(['\"]serviceWorker['\"] in navigator\)[\s\S]*?</script>",
    "",
    h,
    flags=re.I,
)
OUT.write_text(h, encoding="utf-8")
print("offline written, bytes =", len(h.encode("utf-8")))
print("manifest link removed:", "manifest.webmanifest" not in h)
print("has inline __DATA__:", "window.__DATA__" in h)
