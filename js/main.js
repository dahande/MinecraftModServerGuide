/* =====================================================
   main.js – のんびりサバイバル鯖 共通スクリプト
   ===================================================== */

/* ---- Smart back button ---- */
document.querySelectorAll('.btn-back').forEach(function (btn) {
  btn.addEventListener('click', function (e) {
    if (document.referrer && document.referrer.startsWith(window.location.origin)) {
      e.preventDefault();
      history.back();
    }
    /* referrer なし or 外部サイト → href のホームURLへ遷移 */
  });
});

/* ---- Copy to clipboard ---- */
document.addEventListener('click', function (e) {
  var btn = e.target.closest('.copy-btn');
  if (!btn) return;
  var text = btn.dataset.copy;
  if (!text) return;

  navigator.clipboard.writeText(text).then(function () {
    var original = btn.textContent;
    btn.classList.add('copied');
    btn.textContent = '✓ コピー済み';
    showToast('📋 ' + text + ' をコピーしました');
    clearTimeout(btn._timer);
    btn._timer = setTimeout(function () {
      btn.classList.remove('copied');
      btn.textContent = original;
    }, 2000);
  }).catch(function () {
    showToast('⚠️ コピーに失敗しました');
  });
});

/* ---- Toast notification ---- */
function showToast(msg) {
  var toast = document.querySelector('.toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(function () {
    toast.classList.remove('show');
  }, 2400);
}

/* ---- Tooltip (tap toggle for mobile / outside-click & ESC closes) ---- */
document.addEventListener('click', function (e) {
  var tip = e.target.closest('.tooltip');
  /* 他に開いているツールチップは閉じる */
  document.querySelectorAll('.tooltip.is-open').forEach(function (t) {
    if (t !== tip) t.classList.remove('is-open');
  });
  if (tip) {
    tip.classList.toggle('is-open');
    /* span 内の他テキストクリックで吹き出しが即閉じするのを防止 */
    e.stopPropagation();
  }
});
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.tooltip.is-open').forEach(function (t) {
      t.classList.remove('is-open');
      if (t === document.activeElement) t.blur();
    });
  }
});

/* ---- Back to top button ---- */
(function () {
  var btn = document.createElement('a');
  btn.className = 'back-to-top';
  btn.href = '#';
  btn.textContent = '↑';
  btn.title = 'トップへ戻る';
  btn.setAttribute('aria-label', 'ページトップへ戻る');
  btn.addEventListener('click', function (e) {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  document.body.appendChild(btn);

  window.addEventListener('scroll', function () {
    btn.classList.toggle('visible', window.scrollY > 300);
  }, { passive: true });
})();

/* ---- Global fixed footer (logo / countdown / hamburger) ---- */
(function () {
  var inServer = window.location.pathname.indexOf('/server/') >= 0;
  var pre = inServer ? '../' : './';

  /* --- Countdown events --- */
  var events = [
    {
      icon: '🧟',
      label: '7DTD 稼働開始',
      target: '2026-04-17T21:00:00+09:00',
      showFromDays: 30,
      hideAfterHrs: 2,
      href: 'server/7DaysServerInfo.html#status'
    }
  ];

  function pickEvent() {
    var now = Date.now();
    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      var t = Date.parse(ev.target);
      if (isNaN(t)) continue;
      if (now >= t - ev.showFromDays * 86400000 && now <= t + ev.hideAfterHrs * 3600000) {
        return { ev: ev, target: t };
      }
    }
    return null;
  }

  function fmt(n) { return n < 10 ? '0' + n : '' + n; }

  /* --- Logo SVG (inline) --- */
  var logoSvg =
    '<svg viewBox="0 0 40 40" class="gf-logo-svg" xmlns="http://www.w3.org/2000/svg">' +
      '<defs><linearGradient id="gflg" x1="0" y1="0" x2="40" y2="40">' +
        '<stop stop-color="#1a2245"/><stop offset="1" stop-color="#0d1117"/>' +
      '</linearGradient></defs>' +
      '<rect width="40" height="40" rx="10" fill="url(#gflg)"/>' +
      '<path d="M11 17c0-2.2 1.8-4 4-4h10c2.2 0 4 1.8 4 4v2c0 4.4-2.8 8-6 8' +
        '-1.2 0-2.2-.5-3-1.2-.8.7-1.8 1.2-3 1.2-3.2 0-6-3.6-6-8v-2z" fill="#f87171"/>' +
      '<rect x="14" y="17" width="4" height="1.2" rx=".6" fill="#0d1117" opacity=".45"/>' +
      '<rect x="15.4" y="15.6" width="1.2" height="4" rx=".6" fill="#0d1117" opacity=".45"/>' +
      '<circle cx="25" cy="16.5" r="1" fill="#0d1117" opacity=".45"/>' +
      '<circle cx="23" cy="18.5" r="1" fill="#0d1117" opacity=".45"/>' +
    '</svg>';

  /* --- Menu items --- */
  var menuItems = [
    { icon: '🏠', text: 'ホーム', href: 'index.html' },
    { icon: '📢', text: 'お知らせ', href: 'news.html' },
    { sep: true },
    { icon: '🧟', text: '7 Days to Die', href: 'server/7DaysGuide.html' },
    { icon: '🔌', text: '接続手順', href: 'server/7DaysToDieConnect.html', sub: true },
    { icon: '📋', text: 'サーバー情報・ステータス', href: 'server/7DaysServerInfo.html', sub: true },
    { sep: true },
    { icon: '⛏️', text: 'Minecraft', href: 'server/MinecraftConnect.html' },
    { icon: '🦕', text: 'ARK', href: 'server/ARKConnect.html' },
    { icon: '🚀', text: 'Icarus', href: 'server/IcarusConnect.html' },
    { sep: true },
    { icon: '💬', text: 'Discord に参加', href: 'https://discord.gg/tfYDH6Q3Th', external: true }
  ];

  function link(item) {
    if (item.external) return item.href;
    return pre + item.href;
  }

  /* --- Build footer bar --- */
  var bar = document.createElement('nav');
  bar.className = 'gf';
  bar.setAttribute('aria-label', 'グローバルナビ');

  var logoA = document.createElement('a');
  logoA.className = 'gf__logo';
  logoA.href = pre + 'index.html';
  logoA.title = 'ホームへ';
  logoA.innerHTML = logoSvg;

  var center = document.createElement('div');
  center.className = 'gf__center';

  var hamBtn = document.createElement('button');
  hamBtn.className = 'gf__ham';
  hamBtn.setAttribute('aria-label', 'メニュー');
  hamBtn.innerHTML = '<span></span><span></span><span></span>';

  bar.appendChild(logoA);
  bar.appendChild(center);
  bar.appendChild(hamBtn);
  document.body.appendChild(bar);

  /* --- Build menu overlay + panel --- */
  var overlay = document.createElement('div');
  overlay.className = 'gm-overlay';

  var panel = document.createElement('div');
  panel.className = 'gm';

  var pHead = document.createElement('div');
  pHead.className = 'gm__head';
  pHead.innerHTML = '<span class="gm__htitle">メニュー</span>';
  var closeBtn = document.createElement('button');
  closeBtn.className = 'gm__close';
  closeBtn.textContent = '✕';
  closeBtn.setAttribute('aria-label', '閉じる');
  pHead.appendChild(closeBtn);
  panel.appendChild(pHead);

  var pBody = document.createElement('div');
  pBody.className = 'gm__body';

  menuItems.forEach(function (item) {
    if (item.sep) {
      var s = document.createElement('div');
      s.className = 'gm__sep';
      pBody.appendChild(s);
      return;
    }
    var a = document.createElement('a');
    a.className = 'gm__item' + (item.sub ? ' gm__item--sub' : '');
    a.href = link(item);
    if (item.external) { a.target = '_blank'; a.rel = 'noopener'; }
    a.innerHTML = '<span class="gm__icon">' + item.icon + '</span>' +
                  '<span class="gm__text">' + item.text + '</span>';
    if (item.external) a.innerHTML += '<span class="gm__ext">↗</span>';
    pBody.appendChild(a);
  });

  panel.appendChild(pBody);
  overlay.appendChild(panel);
  document.body.appendChild(overlay);

  /* --- Menu toggle --- */
  function openMenu() {
    overlay.classList.add('is-open');
    hamBtn.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }
  function closeMenu() {
    overlay.classList.remove('is-open');
    hamBtn.classList.remove('is-open');
    document.body.style.overflow = '';
  }

  hamBtn.addEventListener('click', function () {
    overlay.classList.contains('is-open') ? closeMenu() : openMenu();
  });
  closeBtn.addEventListener('click', closeMenu);
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) closeMenu();
  });

  /* --- Countdown in center --- */
  var active = pickEvent();

  function renderCD() {
    if (!active) {
      center.innerHTML = '<span class="gf__name">のんびりサバイバル鯖</span>';
      return;
    }
    var diff = active.target - Date.now();
    if (diff <= 0) {
      center.innerHTML =
        '<a href="' + pre + active.ev.href + '" class="gf__cd gf__cd--live">' +
          '<span class="gf__cd-label">' + active.ev.icon + ' ' + active.ev.label + '</span>' +
          '<span class="gf__cd-time gf__cd-time--live">LIVE</span>' +
        '</a>';
      return;
    }
    var d = Math.floor(diff / 86400000);
    var h = Math.floor((diff % 86400000) / 3600000);
    var m = Math.floor((diff % 3600000) / 60000);
    var s = Math.floor((diff % 60000) / 1000);
    var t = (d > 0 ? d + '日 ' : '') + fmt(h) + ':' + fmt(m) + ':' + fmt(s);
    center.innerHTML =
      '<a href="' + pre + active.ev.href + '" class="gf__cd">' +
        '<span class="gf__cd-label">' + active.ev.icon + ' ' + active.ev.label + 'まで</span>' +
        '<span class="gf__cd-time">' + t + '</span>' +
      '</a>';
  }

  renderCD();
  if (active) setInterval(renderCD, 1000);
})();
