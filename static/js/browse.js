/**
 * browse.js — Gallery page logic
 * Covers: filter chips, star/unstar, folder open, file click,
 *         folder ZIP download, file download, delete modal, star status init.
 * Loaded by browse.html after base JS includes.
 */
(function () {
  'use strict';

  /* ── File type extension lists ── */
  var VIDEO_EXTS = ['mp4','mkv','avi','mov','webm','flv','m4v','wmv','mpeg','mpg','3gp','ts','m2ts'];
  var IMAGE_EXTS = ['jpg','jpeg','png','gif','webp','bmp','svg','ico','tiff','tif'];
  var AUDIO_EXTS = ['mp3','flac','wav','ogg','m4a','aac','opus','wma'];
  var DOC_EXTS   = [
    'pdf','doc','docx','txt','rtf','odt','xls','xlsx','ppt','pptx','csv',
    'sh','md','json','xml','yml','yaml','log','py','js','ts','html','css',
    'conf','ini','cfg'
  ];

  /* ── Navigation ──
   * openFolder and clickFile are owned by menu.js which loads before browse.js.
   * menu.js has smart preview logic (image/text/PDF/audio) so we do NOT override
   * those functions here. browse.js only owns gallery-specific features below.
   * ─────────────────────────────────────────────────────────────────────────── */

  /* ── Filter chips ── */
  window.filterItems = function (type, btnEl) {
    // Update chip active styles
    document.querySelectorAll('.filter-chip').forEach(function (b) {
      b.classList.remove('bg-dark-primary-container', 'text-dark-on-primary-container');
      b.classList.add(
        'bg-dark-surface-container', 'border', 'border-dark-outline-variant/30',
        'text-dark-on-surface-variant'
      );
    });
    if (btnEl) {
      btnEl.classList.remove(
        'bg-dark-surface-container', 'border', 'border-dark-outline-variant/30',
        'text-dark-on-surface-variant'
      );
      btnEl.classList.add('bg-dark-primary-container', 'text-dark-on-primary-container');
    }

    var cards = document.querySelectorAll('.gallery-card');
    var shown = 0;

    cards.forEach(function (card) {
      var itype    = (card.dataset.itemType || '').toLowerCase().replace(/^\./, '');
      var isFolder = itype === 'folder';
      var isVideo  = card.dataset.isVideo === 'True' || card.dataset.isVideo === 'true';

      var show = false;
      if      (type === 'all')      { show = true; }
      else if (type === 'folder')   { show = isFolder; }
      else if (type === 'video')    { show = !isFolder && (isVideo || VIDEO_EXTS.indexOf(itype) !== -1); }
      else if (type === 'image')    { show = !isFolder && IMAGE_EXTS.indexOf(itype) !== -1; }
      else if (type === 'audio')    { show = !isFolder && AUDIO_EXTS.indexOf(itype) !== -1; }
      else if (type === 'document') { show = !isFolder && DOC_EXTS.indexOf(itype) !== -1; }

      card.style.display = show ? '' : 'none';
      if (show) shown++;
    });

    // Hide section headings when all cards in that section are hidden
    ['section-folders', 'section-files'].forEach(function (sid) {
      var sec = document.getElementById(sid);
      if (!sec) return;
      var anyVisible = false;
      sec.querySelectorAll('.gallery-card').forEach(function (c) {
        if (c.style.display !== 'none') anyVisible = true;
      });
      sec.style.display = anyVisible ? '' : 'none';
    });

    // Update summary count
    var summary = document.getElementById('item-summary');
    if (summary) summary.textContent = shown + ' items';
  };

  /* ── Star / Unstar ── */
  window.toggleStar = function (filePath, element) {
    return fetch('/api/star/' + encodeURIComponent(filePath), { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.success) return;
        var icon = element.querySelector('.star-icon');
        if (icon) {
          // Pop animation — remove first to allow replay on repeated clicks
          icon.classList.remove('pop');
          void icon.offsetWidth; // force reflow so animation restarts
          icon.classList.add('pop');
          icon.addEventListener('animationend', function () {
            icon.classList.remove('pop');
          }, { once: true });

          if (data.is_starred) {
            // Filled star: glyph swap + inline FILL=1 (beats all CSS) + heavy weight + pink
            icon.textContent = 'star';
            icon.style.fontVariationSettings = "'FILL' 1,'wght' 700,'GRAD' 0,'opsz' 24";
            icon.style.color = '#FFB2B7';
            icon.classList.add('starred');
            element.classList.add('starred');
            element.title = 'Unstar';
          } else {
            // Hollow star: glyph swap + reset all inline styles
            icon.textContent = 'star_border';
            icon.style.fontVariationSettings = '';
            icon.style.color = '';
            icon.classList.remove('starred');
            element.classList.remove('starred');
            element.title = 'Star';

            // If we are on the Starred page, remove the unstarred card immediately
            if (document.body.dataset.currentPath === 'starred' || window.location.pathname.startsWith('/starred')) {
              var card = element.closest('.gallery-card');
              if (card) {
                card.style.transition = 'opacity 180ms ease, transform 180ms ease';
                card.style.opacity = '0';
                card.style.transform = 'scale(0.95)';
                setTimeout(function () {
                  card.remove();
                  var remainingFolders = document.querySelectorAll('#section-folders .gallery-card').length;
                  var remainingFiles = document.querySelectorAll('#section-files .gallery-card').length;
                  var secFolders = document.getElementById('section-folders');
                  var secFiles = document.getElementById('section-files');
                  if (secFolders && remainingFolders === 0) secFolders.remove();
                  if (secFiles && remainingFiles === 0) secFiles.remove();
                  var summary = document.getElementById('item-summary');
                  if (summary) summary.textContent = remainingFolders + ' folders \u00B7 ' + remainingFiles + ' files';
                  if (remainingFolders === 0 && remainingFiles === 0) {
                    window.location.reload();
                  }
                }, 180);
              }
            }
          }
        }
      })
      .catch(function (err) { console.error('[browse] toggleStar error:', err); });
  };

  /* ── Download folder as ZIP ── */
  window.downloadFolder = function (folderPath, folderName) {
    var notification = document.getElementById('zipNotification');
    var fileNameEl   = document.getElementById('zipFileName');
    var titleEl      = notification ? notification.querySelector('.zip-notification-title') : null;

    if (fileNameEl)  fileNameEl.textContent = folderName + '.zip';
    if (titleEl)     { titleEl.textContent = 'Creating ZIP archive…'; titleEl.style.color = ''; }
    if (notification) notification.classList.add('show');

    fetch('/download-folder/' + encodeURIComponent(folderPath))
      .then(function (response) {
        if (!response.ok) {
          if (response.status === 413) {
            return response.json().then(function (d) {
              throw new Error('Folder too large (' + d.size_mb + ' MB). Max: ' + d.limit_mb + ' MB');
            });
          }
          throw new Error('Failed to create ZIP (HTTP ' + response.status + ')');
        }
        if (titleEl) titleEl.textContent = 'Downloading…';
        return response.blob();
      })
      .then(function (blob) {
        var url = window.URL.createObjectURL(blob);
        var a   = document.createElement('a');
        a.href  = url; a.download = folderName + '.zip';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        if (titleEl) { titleEl.textContent = '✓ Download started'; titleEl.style.color = '#64DCA0'; }
        setTimeout(function () {
          if (notification) notification.classList.remove('show');
        }, 2000);
      })
      .catch(function (err) {
        if (titleEl) { titleEl.textContent = '✗ ' + err.message; titleEl.style.color = '#FFB4AB'; }
        setTimeout(function () {
          if (notification) notification.classList.remove('show');
        }, 5000);
      });
  };

  /* ── Download individual file ──
   * Route: /download/<path>?download=true  (force-attachment mode in browse.py)
   * NOTE: do NOT redefine window.downloadFile here — menu.js defines it correctly.
   * ─────────────────────────────────────────────────────────────────────────── */

  /* ── Delete confirmation modal ── */
  window.pendingDelete = null;

  window.confirmDelete = function (path, name, type) {
    window.pendingDelete = { path: path, name: name, type: type };
    var modal   = document.getElementById('deleteModal');
    var message = document.getElementById('deleteModalMessage');
    if (!modal || !message) {
      console.error('[browse] deleteModal elements not found');
      alert('Delete modal not found. Please refresh the page.');
      return;
    }
    message.innerHTML = type === 'folder'
      ? 'Are you sure you want to delete the folder <strong>"' + name + '"</strong> and all its contents?'
      : 'Are you sure you want to delete <strong>"' + name + '"</strong>?';
    modal.classList.add('show');
  };

  window.closeDeleteModal = function () {
    var modal = document.getElementById('deleteModal');
    if (modal) modal.classList.remove('show');
    window.pendingDelete = null;
  };

  window.performDelete = function () {
    if (!window.pendingDelete) return;
    var path = window.pendingDelete.path;
    var name = window.pendingDelete.name;
    var type = window.pendingDelete.type;
    window.closeDeleteModal();
    if (typeof deleteFolder !== 'function' || typeof deleteFile !== 'function') {
      alert('Delete functionality not loaded. Please refresh the page.');
      return;
    }
    if (type === 'folder') { deleteFolder(path, name); }
    else                   { deleteFile(path, name); }
  };

  /* ── Load star status on page load ── */
  document.addEventListener('DOMContentLoaded', function () {
    var toggles = Array.from(document.querySelectorAll('.star-toggle'));

    // Use Promise.all for parallel fetching — much faster with many files
    Promise.all(toggles.map(function (el) {
      // Skip items pre-marked as starred from server (Starred page)
      if (el.dataset.preStarred === 'true') return Promise.resolve();
      return fetch('/api/is_starred/' + encodeURIComponent(el.dataset.path))
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.is_starred) return;
          var icon = el.querySelector('.star-icon');
          if (icon) {
            icon.textContent = 'star';
            icon.style.fontVariationSettings = "'FILL' 1,'wght' 700,'GRAD' 0,'opsz' 24";
            icon.style.color = '#FFB2B7';
            icon.classList.add('starred');
            el.classList.add('starred');
          }
          el.title = 'Unstar';
        })
        .catch(function () {/* ignore individual failures */});
    }));

    // Debug: confirm all functions loaded correctly
    console.log('[browse.js] loaded — confirmDelete:', typeof confirmDelete,
                '| deleteFile:', typeof deleteFile,
                '| showUploadModal:', typeof showUploadModal);
  });

})();

