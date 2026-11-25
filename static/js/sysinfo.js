/**
 * sysinfo.js — System info bar polling + search sync + mobile search toggle
 * Loaded by base.html after all other JS includes.
 */
(function () {
  'use strict';

  /* ── Helpers ── */
  function set(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val;
  }
  function setColor(id, col) {
    var el = document.getElementById(id);
    if (el) el.style.color = col;
  }
  function fmtUptime(h) {
    if (h < 1) return Math.round(h * 60) + 'm';
    if (h < 24) return h.toFixed(1) + 'h';
    return Math.floor(h / 24) + 'd ' + Math.round(h % 24) + 'h';
  }
  function usageColor(pct) {
    if (pct > 85) return '#FFB4AB';  // dark-error
    if (pct > 70) return '#f59e0b';  // amber
    return '#64DCA0';                 // dark-tertiary (green)
  }

  /* ── System info polling ── */
  function updateSystemInfo() {
    fetch('/api/system-info')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.psutil_available === false) {
          set('ramStat',            'Install psutil');
          set('storageStat',        'pkg install python-psutil');
          set('transcodesStat',     '0 jobs');
          set('uptimeStat',         'N/A');
          set('ramStatMobile',      'Install psutil');
          set('storageStatMobile',  '--');
          set('transcodesStatMobile','0 jobs');
          set('uptimeStatMobile',   'N/A');
          return;
        }

        // RAM
        var ramPct  = data.memory.percent;
        var ramUsed = Math.round(data.memory.used_mb);
        var ramTot  = Math.round(data.memory.total_mb);
        var ramCol  = usageColor(ramPct);
        set('ramStat',       ramUsed + '/' + ramTot + ' MB (' + ramPct + '%)');
        set('ramStatMobile', ramUsed + '/' + ramTot + 'MB');
        setColor('ramStat',       ramCol);
        setColor('ramStatMobile', ramCol);

        // Storage
        var stPct  = data.storage.media_root.percent;
        var stFree = data.storage.media_root.free_gb.toFixed(1);
        var stTot  = data.storage.media_root.total_gb.toFixed(1);
        var stCol  = usageColor(stPct);
        set('storageStat',       stFree + '/' + stTot + ' GB free (' + (100 - stPct).toFixed(0) + '%)');
        set('storageStatMobile', stFree + '/' + stTot + 'GB');
        setColor('storageStat',       stCol);
        setColor('storageStatMobile', stCol);

        // Sidebar cache bar (storage %)
        var bar = document.getElementById('cacheBar');
        if (bar) bar.style.width = stPct + '%';
        set('cachePercent', Math.round(stPct) + '%');
        set('cacheUsed',    stFree + ' GB free of ' + stTot + ' GB');

        // Active transcodes
        var jobs = data.active_transcodes;
        set('transcodesStat',      jobs + ' jobs');
        set('transcodesStatMobile', jobs + ' jobs');

        // Uptime
        var ut = fmtUptime(data.uptime_hours);
        set('uptimeStat',      ut);
        set('uptimeStatMobile', ut);
      })
      .catch(function (err) {
        console.error('[sysinfo] fetch error:', err);
        set('ramStat',       'Error');
        set('storageStat',   'Error');
        set('ramStatMobile', 'Err');
        set('storageStatMobile', 'Err');
      });
  }

  updateSystemInfo();
  setInterval(updateSystemInfo, 5000);

  /* ── Mobile search toggle ── */
  window.toggleMobileSearch = function () {
    var bar = document.getElementById('mobileSearchBar');
    if (!bar) return;
    bar.classList.toggle('hidden');
    if (!bar.classList.contains('hidden')) {
      var inp = document.getElementById('searchInputMobile');
      if (inp) inp.focus();
    }
  };

  /* ── Synced search (desktop ↔ mobile) ── */
  document.addEventListener('DOMContentLoaded', function () {
    var desktop = document.getElementById('searchInput');
    var mobile  = document.getElementById('searchInputMobile');

    function runSearch(term) {
      var cards = document.querySelectorAll('.gallery-card');
      cards.forEach(function (card) {
        var nameEl = card.querySelector('.card-name') || card.querySelector('.card-title');
        var name   = nameEl ? nameEl.textContent.toLowerCase() : '';
        card.style.display = name.includes(term) ? '' : 'none';
      });
    }

    if (desktop) {
      desktop.addEventListener('input', function (e) {
        var t = e.target.value.toLowerCase();
        if (mobile) mobile.value = e.target.value;
        runSearch(t);
      });
    }
    if (mobile) {
      mobile.addEventListener('input', function (e) {
        var t = e.target.value.toLowerCase();
        if (desktop) desktop.value = e.target.value;
        runSearch(t);
      });
    }
  });

  /* ── Global Escape handler for modals ── */
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    ['deleteModal', 'renameModal', 'folderModal'].forEach(function (id) {
      var m = document.getElementById(id);
      if (m && m.classList.contains('show')) m.classList.remove('show');
    });
    if (window.pendingDelete !== undefined) window.pendingDelete = null;
  });

})();

