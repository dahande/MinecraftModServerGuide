/* =====================================================
   main.js – のんびりサバイバル鯖 共通スクリプト
   ===================================================== */

/* ---- Copy to clipboard ---- */
document.addEventListener('click', function (e) {
  const btn = e.target.closest('.copy-btn');
  if (!btn) return;
  const text = btn.dataset.copy;
  if (!text) return;

  navigator.clipboard.writeText(text).then(function () {
    const original = btn.textContent;
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

/* ---- Countdown banner for scheduled server launches ---- */
(function () {
  /* 予定イベント一覧（複数登録可） */
  var events = [
    {
      title   : '🧟 7 Days to Die サーバー 稼働開始',
      target  : '2026-04-17T21:00:00+09:00',
      showFromDays : 30,    /* 何日前から表示開始 */
      hideAfterHrs : 2,     /* 開始何時間後まで表示 */
      href    : './server/7DaysStatus.html'
    }
  ];

  function resolveHref(ev) {
    var p = window.location.pathname;
    if (p.indexOf('/server/') >= 0) {
      return ev.href.replace(/^\.\//, '').replace(/^server\//, './');
    }
    return ev.href;
  }

  function pickActiveEvent() {
    var now = Date.now();
    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      var t  = Date.parse(ev.target);
      if (isNaN(t)) continue;
      var showFrom = t - ev.showFromDays * 86400000;
      var hideAt   = t + ev.hideAfterHrs * 3600000;
      if (now >= showFrom && now <= hideAt) {
        return { ev: ev, target: t };
      }
    }
    return null;
  }

  function fmt(n) { return n < 10 ? '0' + n : '' + n; }

  function buildBanner() {
    var b = document.createElement('a');
    b.className = 'countdown-banner';
    b.innerHTML =
      '<span class="countdown-banner__icon">⏰</span>' +
      '<span class="countdown-banner__text">' +
        '<span class="countdown-banner__title"></span>' +
        '<span class="countdown-banner__time" aria-live="polite"></span>' +
      '</span>' +
      '<span class="countdown-banner__arrow">→</span>';
    return b;
  }

  function render(banner, ev, target) {
    var diff = target - Date.now();
    var title = banner.querySelector('.countdown-banner__title');
    var time  = banner.querySelector('.countdown-banner__time');

    if (diff <= 0) {
      banner.classList.add('is-live');
      title.textContent = ev.title + ' 稼働中！';
      time.textContent  = '🟢 LIVE';
      return;
    }

    banner.classList.remove('is-live');
    var d = Math.floor(diff / 86400000);
    var h = Math.floor((diff % 86400000) / 3600000);
    var m = Math.floor((diff % 3600000) / 60000);
    var s = Math.floor((diff % 60000) / 1000);
    title.textContent = ev.title + 'まで';
    time.textContent  = (d > 0 ? d + '日 ' : '') +
                        fmt(h) + ':' + fmt(m) + ':' + fmt(s);
  }

  var active = pickActiveEvent();
  if (!active) return;

  var wrapper = document.querySelector('.wrapper');
  if (!wrapper) return;

  var banner = buildBanner();
  banner.href = resolveHref(active.ev);
  wrapper.insertBefore(banner, wrapper.firstChild);

  render(banner, active.ev, active.target);
  setInterval(function () {
    render(banner, active.ev, active.target);
  }, 1000);
})();
