# -*- coding: utf-8 -*-
"""
每日新闻速览 - 站点生成器

用法: python tools/gen.py
作用:
  1) 写入 data/news.json（当天新闻数据）
  2) 读取 data/yesterday.json（昨日数据，可缺失）
  3) 生成根目录 index.html，把两份数据内联进 <script>（首屏零依赖，手机秒开）
  4) 自动校验 HTML 中 JS 引用的 DOM id 是否都存在 —— 防止出现
     getElementById('stat') 但页面里没有该元素 这类导致整页白屏的崩溃
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
OUT_HTML = os.path.join(BASE, "index.html")

TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)
TODAY = NOW.strftime("%Y-%m-%d")
GENERATED_AT = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")

# ----------------------------------------------------------------------------
# 当天新闻（2026-09-09，来源：中国新闻网 RSS 实时抓取，均为原文报道页链接）
# ----------------------------------------------------------------------------
ITEMS = [
    {
        "category": "国际时事", "scope": "国内",
        "title": "香港首任行政长官董建华逝世，享年89岁",
        "summary": "据董建华办公室9月9日凌晨消息，全国政协前副主席、香港特别行政区首任行政长官董建华，于2026年9月8日晚10时许在亲人陪伴下于医院安详辞世，享年89岁。他1997年香港回归后出任首任特首，是“一国两制”实践的重要亲历者。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gn/2026/09-09/10692991.shtml",
    },
    {
        "category": "战争与自然灾害", "scope": "国际",
        "title": "尼泊尔泥石流灾害遇难人数升至1366人",
        "summary": "据尼泊尔警方修正后的最新数据，截至当地时间9月8日20时，该国泥石流灾害造成的遇难人数升至1366人。此前中方已向尼泊尔提供多批紧急援助物资，第四批物资由空军运-20运抵加德满都，救援与善后工作仍在持续推进。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gj/2026/09-09/10692998.shtml",
    },
    {
        "category": "国际时事", "scope": "国际",
        "title": "第81届联合国大会开幕",
        "summary": "当地时间9月8日，在第80届联合国大会闭幕后，第81届联合国大会在纽约联合国总部开幕。新一届联大将审议中东局势、气候与发展等一系列全球议题，各方关注多边机制在分裂加剧的世界中能否重振协调作用。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gj/2026/09-09/10692995.shtml",
    },
    {
        "category": "国际时事", "scope": "国际",
        "title": "美国对伊朗实施新一轮制裁 重点针对伊朗航空业",
        "summary": "据路透社报道，美国财政部当地时间9月8日宣布对伊朗实施新一轮制裁，共涉及36个制裁对象，重点针对伊朗航空业及相关企业。这是美伊围绕霍尔木兹海峡与军事冲突升级后，美方施加的又一经济施压举措。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gj/2026/09-09/10692992.shtml",
    },
    {
        "category": "战争与自然灾害", "scope": "国际",
        "title": "美国中央司令部：摧毁5艘伊朗原油运输船",
        "summary": "当地时间9月8日，美国中央司令部在社交媒体发文称，美军部队当天摧毁了5艘伊朗原油运输船。此前美军还在伊朗哈尔克岛附近袭击多艘油轮，霍尔木兹海峡航运安全与全球能源供应风险持续升高。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gj/2026/09-09/10692984.shtml",
    },
    {
        "category": "国际时事", "scope": "国际",
        "title": "持续约一小时 普京与特朗普通电话讨论解决乌克兰问题",
        "summary": "据俄新社及俄罗斯总统网站消息，俄罗斯总统助理乌沙科夫表示，当地时间8日俄总统普京与美国总统特朗普通电话，持续约一小时，重点讨论解决乌克兰问题。此前美特使已携“和平方案”访问俄乌，但核心症结仍待突破。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gj/2026/09-09/10692983.shtml",
    },
    {
        "category": "国际时事", "scope": "国际",
        "title": "贸易争端加剧 特朗普称加产品将被排除出美政府采购计划",
        "summary": "据路透社报道，美国总统特朗普8日在社交媒体发文称，已指示美国总务管理局与贸易代表办公室合作，采取一切必要措施把加拿大产品排除出美政府采购计划，直至加方对美农民和企业恢复“公平的互惠”。加方对美反制关税同日生效。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gj/2026/09-09/10692986.shtml",
    },
    {
        "category": "战争与自然灾害", "scope": "国际",
        "title": "马来西亚一直升机坠毁 机上5人罹难",
        "summary": "马来西亚一架执行医疗任务的直升机8日下午在沙捞越州龙里浪短距起降机场附近坠毁。马方当晚确认，机上1名飞行员和4名卫生部门工作人员全部遇难。该机场位于古晋以北约929公里处，事故原因有待进一步调查。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gj/2026/09-09/10692978.shtml",
    },
    {
        "category": "国际时事", "scope": "国内",
        "title": "习近平就朝鲜国庆78周年向金正恩致贺电",
        "summary": "9月9日新华社快讯：习近平就朝鲜国庆78周年向朝鲜最高领导人金正恩致贺电。同日，全国人大常委会副委员长彭清华出席朝鲜驻华使馆举行的国庆78周年招待会，双方一致表示将贯彻落实两党两国最高领导人共识，推动中朝关系高水平发展。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gn/2026/09-09/10693003.shtml",
    },
    {
        "category": "科技互联网与AI", "scope": "国内",
        "title": "十万卡集群将越来越多！事关国产算力，重磅部署",
        "summary": "工业和信息化部9月7日印发《信息通信行业发展“十五五”规划》，提出提升算力设施发展水平、深化算力协同、强化公共算力服务。到2030年，新建大型超大型算力设施PUE降至1.2以下，智能算力规模达到9800EFLOPS。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gn/2026/09-09/10692994.shtml",
    },
    {
        "category": "科技互联网与AI", "scope": "国内",
        "title": "“国家反诈AI”App正式上线 手把手教你用",
        "summary": "由公安部刑事侦查局指导、上海市公安局自主研发的“国家反诈AI”App正式上线。用户输入可疑场景即可随时查询、拆解诈骗手法，被视为用AI对抗电信网络诈骗的新工具，帮助公众识别层出不穷、越来越难辨真假的骗术。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/sh/2026/09-09/10693000.shtml",
    },
    {
        "category": "财经经济与就业", "scope": "国内",
        "title": "中国快递按下转型升级“换挡键” 新的增量从何而来",
        "summary": "主要快递上市公司“半年报”显示，利润增速普遍“跑赢”件量增速，行业按下转型升级“换挡键”。在价格竞争趋缓背景下，快递业新的增量正从时效、服务品质与供应链能力中寻求，行业由此迈向高质量发展阶段。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/cj/2026/09-09/10693007.shtml",
    },
    {
        "category": "财经经济与就业", "scope": "国际",
        "title": "韩国二季度实际GDP环比增长0.6%",
        "summary": "韩国银行（央行）8日发布数据显示，韩国2026年第二季度实际国内生产总值（GDP）环比增长0.6%，与7月公布的初步核算数据持平。在外部环境不确定性上升的背景下，韩国经济维持温和复苏态势，增长动能仍待巩固。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gj/2026/09-09/10692979.shtml",
    },
    {
        "category": "健康养生", "scope": "国际",
        "title": "南非卫生部：超5.5万人开始使用长效艾滋病预防药物",
        "summary": "南非政府新闻网8日报道，南非卫生部称长效艾滋病病毒预防药物来那卡帕韦（Lenacapavir）在南推广取得“显著进展”，截至9月7日已有55123人开始使用该药物。长效预防针剂被视为降低艾滋病感染率的重要公共卫生工具。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gj/2026/09-09/10692996.shtml",
    },
    {
        "category": "社会民生与教育", "scope": "国内",
        "title": "减少消费纠纷，经营更规范！消费治理模式迎来重大转变",
        "summary": "市场监管总局近日印发通知，全面启动“放心消费”主体培育工作，明确到2030年全国放心消费集聚区达5000个以上，重点领域放心消费单元广泛覆盖，“放心消费在中国”品牌基本形成，消费者获得感明显增强。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/sh/2026/09-09/10693001.shtml",
    },
    {
        "category": "环境气候", "scope": "国内",
        "title": "华中西南地区有降温过程 四川盆地有较强降水",
        "summary": "中央气象台9月9日消息，昨日四川、青海等地出现强降雨，内蒙古、辽宁、河南出现大风降温。预计未来三天冷空气将继续影响北方地区，陕西、甘肃、宁夏、四川等地有较强降雨，需防范山洪、地质灾害等次生灾害。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/sh/2026/09-09/10693005.shtml",
    },
    {
        "category": "娱乐影视", "scope": "国际",
        "title": "《欢迎来龙餐馆》在澳大利亚首映",
        "summary": "由文牧野执导、沈腾与蒋奇明领衔主演的中国影片《欢迎来龙餐馆》8日晚在澳大利亚墨尔本举行首映礼。该片此前已在马来西亚举行首映并将于9月11日正式公映，中国电影出海再进一步，吸引当地各族裔观众到场观影。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/gj/2026/09-09/10692977.shtml",
    },
    {
        "category": "体育赛事", "scope": "国内",
        "title": "辽宁省第十一届少数民族传统体育运动会开赛",
        "summary": "辽宁省第十一届少数民族传统体育运动会8日在本溪市举行，珍珠球、押加两个竞赛项目当日开赛。赛事以传统竞技项目搭建各民族交往交流交融的舞台，集中展现少数民族体育文化的活力与传承。",
        "source": "中国新闻网", "url": "https://www.chinanews.com.cn/ty/2026/09-09/10692976.shtml",
    },
]

# ----------------------------------------------------------------------------
TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1f6feb">
<meta name="format-detection" content="telephone=no">
<title>每日新闻速览</title>
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="新闻速览">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<style>
:root{--blue:#1f6feb;--bg:#f4f6fa;--card:#fff;--text:#16202e;--muted:#7b8698;--line:#e8ecf3}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Helvetica Neue",Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.65;-webkit-text-size-adjust:100%}
.wrap{max-width:720px;margin:0 auto;padding:0 12px calc(30px + env(safe-area-inset-bottom))}
header{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.94);backdrop-filter:saturate(180%) blur(10px);border-bottom:1px solid var(--line);padding-top:env(safe-area-inset-top)}
.hbar{max-width:720px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;padding:12px 14px 8px}
.title{font-size:20px;font-weight:800;letter-spacing:.5px}
.title small{display:block;font-size:12px;font-weight:500;color:var(--muted);letter-spacing:0;margin-top:3px}
.refresh{border:1px solid var(--line);background:#fff;color:var(--blue);font-size:13px;font-weight:600;padding:8px 14px;border-radius:999px;cursor:pointer}
.subbar{max-width:720px;margin:0 auto;display:flex;gap:8px;align-items:center;padding:0 14px 8px}
.tabs{display:flex;gap:4px;background:#eef1f6;border-radius:10px;padding:3px}
.tab{border:none;background:transparent;color:#6b7587;font-size:13px;font-weight:600;padding:6px 16px;border-radius:8px;cursor:pointer}
.tab.on{background:#fff;color:var(--blue);box-shadow:0 1px 3px rgba(20,30,60,.12)}
.stat{font-size:12px;color:var(--muted);margin-left:auto}
.chips{display:flex;gap:8px;overflow-x:auto;padding:8px 14px 10px;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex:0 0 auto;border:1px solid var(--line);background:#fff;color:#5b6577;font-size:13px;padding:7px 14px;border-radius:999px;cursor:pointer;white-space:nowrap}
.chip.on{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:600}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 15px;margin:12px 0;box-shadow:0 2px 10px rgba(20,30,60,.04)}
.tag{display:inline-block;font-size:11.5px;font-weight:700;color:#fff;padding:3px 10px;border-radius:999px}
.scope{font-size:11.5px;color:var(--muted);margin-left:8px}
.card h2{font-size:17px;margin:10px 0 7px;line-height:1.45}
.card p{font-size:14.5px;color:#39445a;margin:0 0 11px}
.meta{display:flex;align-items:center;justify-content:space-between;font-size:12.5px;color:var(--muted);border-top:1px solid var(--line);padding-top:9px}
.read{color:var(--blue);font-weight:600;text-decoration:none;padding:4px 0}
.empty{text-align:center;color:var(--muted);padding:48px 16px;font-size:15px}
.foot{text-align:center;color:var(--muted);font-size:12px;padding:16px 10px 6px}
</style>
<script>window.__DATA__ = __INITIAL_DATA__;</script>
</head>
<body>
<header>
  <div class="hbar">
    <div class="title">每日新闻速览<small id="datestr">加载中…</small></div>
    <button class="refresh" id="refreshBtn">&#8635; 刷新</button>
  </div>
  <div class="subbar">
    <div class="tabs">
      <button class="tab on" id="tabToday">今天</button>
      <button class="tab" id="tabYest">昨天</button>
    </div>
    <span class="stat" id="stat"></span>
  </div>
  <div class="chips" id="chips"></div>
</header>
<div class="wrap">
  <div id="list"></div>
  <div class="foot" id="foot"></div>
</div>
<script>
(function(){
  // 注销历史遗留的 Service Worker：旧版 SW 曾把空首页缓存住，导致手机端一直白屏
  try {
    if (navigator.serviceWorker && navigator.serviceWorker.getRegistrations) {
      navigator.serviceWorker.getRegistrations().then(function(regs){
        for (var i = 0; i < regs.length; i++) { regs[i].unregister(); }
      });
    }
  } catch (e) {}

  var D = window.__DATA__ || {};
  var data = D.today || null;
  var yest = D.yest || null;
  var view = "today";
  var cat = "全部";
  var CAT_KEY = "news_cat_v1";

  function $(id){ return document.getElementById(id); }
  function setText(id, t){ var el = $(id); if (el) el.textContent = t; }

  var COLORS = {"科技互联网与AI":"#1f6feb","国际时事":"#8b5cf6","财经经济与就业":"#f59e0b","社会民生与教育":"#10b981","战争与自然灾害":"#ef4444","科学探索":"#0ea5e9","体育赛事":"#14b8a6","健康养生":"#06b6d4","环境气候":"#22c55e","汽车出行":"#64748b","娱乐影视":"#ec4899","游戏电竞":"#6366f1","文化读书":"#a855f7","旅行出行":"#f97316"};
  function colorOf(n){ return COLORS[n] || "#7b8698"; }

  function esc(s){
    return String(s == null ? "" : s).replace(/[&<>"]/g, function(c){
      return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c];
    });
  }

  function current(){ return view === "today" ? data : yest; }

  function renderChips(){
    var box = $("chips"); if (!box) return;
    var d = current();
    var cats = [];
    if (d && d.items) {
      d.items.forEach(function(it){
        if (it.category && cats.indexOf(it.category) < 0) cats.push(it.category);
      });
    }
    if (!cats.length) { box.innerHTML = ""; return; }
    if (cat !== "全部" && cats.indexOf(cat) < 0) cat = "全部";
    var html = ['<button class="chip' + (cat === "全部" ? " on" : "") + '" data-c="全部">全部</button>'];
    cats.forEach(function(c){
      html.push('<button class="chip' + (cat === c ? " on" : "") + '" data-c="' + esc(c) + '">' + esc(c) + '</button>');
    });
    box.innerHTML = html.join("");
    var btns = box.querySelectorAll(".chip");
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener("click", (function(btn){
        return function(){
          cat = btn.getAttribute("data-c");
          try { localStorage.setItem(CAT_KEY, cat); } catch (e) {}
          renderChips(); renderList();
        };
      })(btns[i]));
    }
  }

  function renderList(){
    var list = $("list"); if (!list) return;
    var d = current();
    if (!d || !d.items || !d.items.length) {
      setText("stat", "");
      list.innerHTML = '<div class="empty">暂无数据。<br>请稍后点右上角「刷新」重试。</div>';
      return;
    }
    var items = d.items.filter(function(it){
      return cat === "全部" || it.category === cat;
    });
    setText("stat", (view === "today" ? "今日 " : "昨日 ") + items.length + " 条");
    setText("datestr", (d.date || "") + (view === "today" ? " · 每天更新" : " · 昨日回顾"));
    if (!items.length) {
      list.innerHTML = '<div class="empty">该分类暂无内容，换个分类看看。</div>';
      return;
    }
    var out = "";
    items.forEach(function(it){
      out += '<div class="card">'
        + '<div><span class="tag" style="background:' + colorOf(it.category) + '">' + esc(it.category) + '</span>'
        + '<span class="scope">' + esc(it.scope || "") + '</span></div>'
        + '<h2>' + esc(it.title) + '</h2>'
        + '<p>' + esc(it.summary) + '</p>'
        + '<div class="meta"><span>来源：' + esc(it.source || "未知") + '</span>'
        + '<a class="read" href="' + esc(it.url) + '" target="_blank" rel="noopener">阅读原文 &rsaquo;</a></div>'
        + '</div>';
    });
    list.innerHTML = out;
    setText("foot", "共 " + d.items.length + " 条 · 来源为公开报道");
  }

  function render(){ renderChips(); renderList(); }

  function switchView(v){
    view = v;
    var t = $("tabToday"), y = $("tabYest");
    if (t) t.className = "tab" + (v === "today" ? " on" : "");
    if (y) y.className = "tab" + (v === "yesterday" ? " on" : "");
    render();
  }

  function load(){
    // 任何情况下都不允许更新逻辑影响已渲染内容（老浏览器无 fetch 时同步抛错也要吞掉）
    try {
      return fetch("./data/news.json", { cache: "no-store" })
        .then(function(r){ if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .then(function(j){
          if (j && j.items && j.items.length) { data = j; render(); }
        })
        .catch(function(){ /* 静默：保留内联数据，绝不清空页面 */ });
    } catch (e) {
      return Promise.resolve();
    }
  }

  try {
    var saved = null;
    try { saved = localStorage.getItem(CAT_KEY); } catch (e) {}
    if (saved) cat = saved;
    var t = $("tabToday"); if (t) t.addEventListener("click", function(){ switchView("today"); });
    var y = $("tabYest"); if (y) y.addEventListener("click", function(){ switchView("yesterday"); });
    var r = $("refreshBtn");
    if (r) r.addEventListener("click", function(){
      r.textContent = "更新中…";
      load().then(function(){ r.textContent = "\u21BB 刷新"; });
    });
    render();
    try { load(); } catch (e2) {}
  } catch (e) {
    var l = $("list");
    if (l) l.innerHTML = '<div class="empty">页面出错：' + esc(e && e.message) + '</div>';
  }
})();
</script>
</body>
</html>
"""


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    news_path = os.path.join(DATA_DIR, "news.json")

    # 若已存在「当天」的数据则优先沿用，避免重复运行时把刚抓好的数据覆盖掉
    # 加 --force 则用脚本内置的最新数据强制覆盖
    force = "--force" in sys.argv
    news = None
    if force:
        print("[ok] --force：使用脚本内置最新数据覆盖")
    elif os.path.exists(news_path):
        try:
            with open(news_path, encoding="utf-8") as f:
                existing = json.load(f)
            if existing and existing.get("date") == TODAY and existing.get("items"):
                news = existing
                print("[ok] 沿用已有当天数据（%d 条）" % len(news["items"]))
        except Exception as e:
            print("[warn] 读取已有 news.json 失败，改用内置数据: %s" % e)

    if news is None:
        news = {
            "date": TODAY,
            "generatedAt": GENERATED_AT,
            "method": "混合（搜索引擎实时抓取 + RSS）",
            "items": [dict(it, id=i + 1) for i, it in enumerate(ITEMS)],
        }

    news["generatedAt"] = GENERATED_AT
    with open(news_path, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    print("[ok] 写入 %s（%d 条）" % (news_path, len(news["items"])))

    yest = None
    yp = os.path.join(DATA_DIR, "yesterday.json")
    if os.path.exists(yp):
        try:
            with open(yp, encoding="utf-8") as f:
                yest = json.load(f)
            if not (yest or {}).get("items"):
                yest = None
            elif yest.get("date") == TODAY:
                print("[warn] yesterday.json 日期与今天相同，已忽略")
                yest = None
        except Exception as e:
            print("[warn] yesterday.json 解析失败，忽略: %s" % e)
            yest = None
    print("[ok] 昨日数据: %s" % (yest["date"] if yest else "无"))

    payload = {"today": news, "yest": yest}
    data_js = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__INITIAL_DATA__", data_js)

    # ---- 自动校验：JS 里引用的 DOM id 必须在 HTML 中存在 ----
    declared = set(re.findall(r'id="([^"]+)"', html))
    used = set()
    used |= set(re.findall(r'\$\("([^"]+)"\)', html))
    used |= set(re.findall(r'getElementById\("([^"]+)"\)', html))
    used |= set(re.findall(r'setText\("([^"]+)"', html))
    missing = sorted(used - declared)
    if missing:
        print("[FAIL] 以下 id 在 JS 中被引用但 HTML 里不存在，会导致白屏: %s" % missing)
        sys.exit(1)
    print("[ok] DOM id 校验通过（引用 %d 个，全部存在）" % len(used))

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("[ok] 生成 %s（%.1f KB）" % (OUT_HTML, len(html.encode("utf-8")) / 1024.0))

    cats = {}
    for it in news["items"]:
        cats[it["category"]] = cats.get(it["category"], 0) + 1
    print("[ok] 专题覆盖 %d 类: %s" % (len(cats), "、".join(sorted(cats))))


if __name__ == "__main__":
    main()
