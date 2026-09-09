#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 data/news.json 与 data/yesterday.json 嵌入 index.html，
保证页面打开瞬间即可渲染，不依赖额外网络请求。

注意：当前页面读取的是 window.__DATA__（不是旧版的 __INITIAL_DATA__）。
本脚本会替换已存在的 window.__DATA__ 数据块；若不存在则插入 </head> 之前。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
INDEX = ROOT / "index.html"
NEWS = ROOT / "data" / "news.json"
YEST = ROOT / "data" / "yesterday.json"


def read_json(path):
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    if not INDEX.exists():
        raise FileNotFoundError("%s 不存在" % INDEX)

    html = INDEX.read_text(encoding="utf-8")
    today = read_json(NEWS)
    yest = read_json(YEST)

    payload = json.dumps(
        {"today": today, "yest": yest}, ensure_ascii=False
    ).replace("</", "<\\/")
    script = "<script>window.__DATA__ = %s;</script>" % payload

    new_html, n = re.subn(
        r"<script>window\.__DATA__ = .*?;</script>",
        lambda _m: script,
        html,
        count=1,
        flags=re.S,
    )
    if n:
        html = new_html
    else:
        html = html.replace("</head>", script + "\n</head>", 1)

    INDEX.write_text(html, encoding="utf-8")
    print("已嵌入: today=%s, yest=%s -> %s" % (bool(today), bool(yest), INDEX))


if __name__ == "__main__":
    main()
