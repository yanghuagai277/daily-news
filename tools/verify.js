// 真实执行页面 JS，验证渲染是否正常（抓白屏 / JS 崩溃）
// 运行: NODE_PATH=<workspace>/node_modules node tools/verify.js
const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const errors = [];

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  url: 'http://localhost:8000/',
  pretendToBeVisual: true,
  beforeParse(window) {
    window.addEventListener('error', (e) => errors.push('window.error: ' + (e.message || e.error)));
    const orig = window.console.error;
    window.console.error = (...a) => { errors.push('console.error: ' + a.join(' ')); orig.apply(window.console, a); };
  },
});

setTimeout(() => {
  const doc = dom.window.document;
  const cards = doc.querySelectorAll('#list .card').length;
  const chips = doc.querySelectorAll('#chips .chip').length;
  const datestr = doc.getElementById('datestr').textContent;
  const stat = doc.getElementById('stat').textContent;
  const firstTitle = (doc.querySelector('#list .card h2') || {}).textContent || '(无)';
  // 只检查可见列表区域；不能用 body.textContent，它会把 <script> 源码里的字符串也算进去
  const listText = doc.getElementById('list').textContent;
  const bad = /页面出错|加载失败/.test(listText);

  console.log('渲染卡片数     :', cards);
  console.log('分类 chip 数   :', chips);
  console.log('日期栏         :', datestr);
  console.log('统计栏(stat)   :', stat);
  console.log('首条标题       :', firstTitle);
  console.log('JS 错误        :', errors.length ? errors.join(' | ') : '无');

  const ok = cards > 0 && chips > 0 && errors.length === 0 && !bad;
  console.log(ok ? '\n[PASS] 渲染正常，无 JS 错误' : '\n[FAIL] 页面异常');
  process.exit(ok ? 0 : 1);
}, 800);
