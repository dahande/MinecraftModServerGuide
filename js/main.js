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
