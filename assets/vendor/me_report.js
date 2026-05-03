/* Materialized Enhancements — client-side Share & Report helpers.
 * Loaded as plain <script src="/vendor/me_report.js"> after html-to-image,
 * jspdf and qrcode-generator so their globals are available here.
 */
(function () {
  'use strict';
  if (window.__meReportBooted) return;
  window.__meReportBooted = true;

  /* ------------------------------------------------------------------ helpers */

  function sharePath() {
    var el = document.getElementById('report-share-path');
    return el ? el.value : '';
  }
  function publishedReportUrl() {
    var el = document.getElementById('report-published-url');
    return el && el.value ? String(el.value).trim() : '';
  }
  function generatedShareUrl() {
    return window.__mePendingPublishedReportUrl || publishedReportUrl();
  }
  /** Server-provided canonical origin (DEPLOY_URL / PUBLIC_APP_URL); falls back to browser. */
  function canonicalOrigin() {
    var el = document.getElementById('report-canonical-base');
    var v = el && el.value ? String(el.value).trim().replace(/\/+$/, '') : '';
    if (v) return v;
    return window.location.origin;
  }
  function absoluteShareUrl() {
    var p = sharePath();
    var origin = canonicalOrigin();
    if (!p) return origin + '/';
    if (/^https?:\/\//i.test(p)) return p;
    if (p.charAt(0) === '/') return origin + p;
    return origin + '/' + (p.charAt(0) === '?' ? '' : '') + p;
  }
  function reportTargetUrl() {
    return generatedShareUrl();
  }
  function browserAbsoluteUrl(pathOrUrl) {
    var v = String(pathOrUrl || '').trim();
    if (!v) return '';
    if (/^https?:\/\//i.test(v)) return v;
    if (v.charAt(0) === '/') return window.location.origin + v;
    return window.location.origin + '/' + v;
  }
  function safeName() {
    var raw = (document.getElementById('report-share-name') || {}).value || 'anon';
    return raw.replace(/[^a-zA-Z0-9_-]+/g, '_').slice(0, 40) || 'anon';
  }
  function safeSeed() {
    return (document.getElementById('report-share-seed') || {}).value || '0';
  }
  function userpicDataUrl() {
    var el = document.getElementById('report-userpic-data-url');
    return el && el.value ? String(el.value).trim() : '';
  }
  function characterNote() {
    var el = document.getElementById('report-character-note');
    return el && el.value ? String(el.value).trim() : '';
  }

  /* ---------------------------------------------------------- painters */

  function paintShareUrl() {
    var urlEl = document.getElementById('report-share-url');
    if (!urlEl) return;
    var url = reportTargetUrl();
    urlEl.textContent = url || 'Generate a sharable folder to create a public QR/link.';
  }

  function qrPlaceholder(el) {
    if (!el) return false;
    el.innerHTML = '';
    var span = document.createElement('span');
    span.textContent = 'Generate sharable folder';
    span.style.cssText =
      'font-size:10px;line-height:1.2;text-align:center;color:#9ca3af;';
    el.appendChild(span);
    return false;
  }

  function qrFallback(el, url, message) {
    if (!el) return false;
    el.innerHTML = '';
    var a = document.createElement('a');
    a.href = url;
    a.textContent = message || 'Open report link';
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.style.cssText =
      'font-size:10px;line-height:1.2;text-align:center;word-break:break-word;color:#7c3aed;';
    el.appendChild(a);
    return false;
  }

  function renderQrInto(el) {
    var url = reportTargetUrl();
    if (!el) return false;
    if (!url) return qrPlaceholder(el);
    if (typeof qrcode === 'undefined') return qrFallback(el, url, 'QR library missing. Open link.');
    try {
      var qr = qrcode(0, 'M');
      qr.addData(url);
      qr.make();
      el.innerHTML = qr.createImgTag(4, 0);
      var img = el.querySelector('img');
      if (img) {
        img.alt = 'QR code for ' + url;
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.display = 'block';
        img.style.objectFit = 'contain';
      }
      if (!img || !img.getAttribute('src')) return qrFallback(el, url, 'Open report link');
      return true;
    } catch (_e) {
      return qrFallback(el, url, 'Open report link');
    }
  }
  function paintQr() {
    /* PNG export card has no QR; PDF cover uses QR from this same on-screen element. */
    return renderQrInto(document.getElementById('report-qr'));
  }

  function paintViews() {
    var v = window.__reportViews;
    if (!v) return false;
    var ids = [
      ['report-view-front', v.front],
      ['report-view-side',  v.side],
      ['report-view-back',  v.back],
      ['png-view-front',    v.front],
      ['png-view-side',     v.side],
      ['png-view-back',     v.back],
    ];
    var painted = 0;
    for (var i = 0; i < ids.length; i++) {
      var el = document.getElementById(ids[i][0]);
      var src = ids[i][1];
      if (el && src) { el.src = src; painted++; }
    }
    return painted > 0;
  }

  window.addEventListener('message', function (e) {
    if (e.data && e.data.type === 'report_views_ready') {
      window.__reportViews = e.data.views || window.__reportViews;
      paintViews();
    }
  });

  var lastShareUrl = '';
  var lastViewsSig = '';

  window.__mePaintReport = function () {
    var url = reportTargetUrl();
    if (url !== lastShareUrl) {
      paintShareUrl();
      paintQr();
      lastShareUrl = url;
    }
    var v = window.__reportViews;
    var sig = v ? ((v.front || '').length + '|' + (v.side || '').length + '|' + (v.back || '').length) : '';
    if (sig && sig !== lastViewsSig) {
      if (paintViews()) lastViewsSig = sig;
    }
  };

  /* --------------------------------------- mutation observer (debounced) */

  var scheduled = false;
  var observer = null;
  var observerActive = false;

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(function () {
      scheduled = false;
      if (document.getElementById('me-report-card')) window.__mePaintReport();
    });
  }

  function startObserver() {
    if (observerActive || !document.body) return;
    observer = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var n = mutations[i].target;
        while (n && n !== document.body) {
          if (n.id === 'report-qr' ||
              n.id === 'me-report-pdf-long' || n.id === 'me-report-png-card' ||
              n.id === 'report-export-animals-json' ||
              n.id === 'report-export-composition-genes-json') return;
          n = n.parentNode;
        }
      }
      schedule();
    });
    observer.observe(document.body, { childList: true, subtree: true });
    observerActive = true;
  }
  function stopObserver() {
    if (observer) { observer.disconnect(); observer = null; }
    observerActive = false;
  }

  if (document.body) startObserver();
  else document.addEventListener('DOMContentLoaded', startObserver);
  document.addEventListener('DOMContentLoaded', schedule);
  window.addEventListener('load', schedule);

  /* ----------------------------------------------------- download helpers */

  function downloadDataUrl(dataUrl, filename) {
    var a = document.createElement('a');
    a.href = dataUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { document.body.removeChild(a); }, 0);
  }

  function feedback(text, color) {
    var fb = document.getElementById('report-copy-feedback');
    if (!fb) return;
    fb.style.color = color || '#16a085';
    fb.textContent = text || '';
    if (text) setTimeout(function () { if (fb.textContent === text) fb.textContent = ''; }, 3500);
  }

  function missingLib(name) {
    console.warn('[materialized] skipping action: ' + name + ' is not loaded yet');
    feedback(name + ' not loaded — reload the page.', '#b91c1c');
  }

  function dataUrlBase64(dataUrl, label) {
    var s = String(dataUrl || '');
    var commaIdx = s.indexOf('base64,');
    if (commaIdx < 0) throw new Error(label + ' output did not contain base64 payload.');
    return s.slice(commaIdx + 7);
  }

  /**
   * jsPDF's built-in Helvetica uses WinAnsiEncoding. Strings containing
   * Unicode outside Latin-1 are emitted as UTF-16BE PDF literals; many viewers
   * then show garbage (spacing that looks like "&" between glyphs) and long
   * tokens may not wrap. Normalize to Latin-1 before text() / splitTextToSize.
   */
  function pdfSafeWinAnsi(input) {
    if (input == null || input === '') return '';
    var s = String(input);
    s = s
      .replace(/\r\n/g, '\n')
      .replace(/\u00a0/g, ' ')
      .replace(/[\u2018\u2019\u201A\u201B\u2032\u2035]/g, "'")
      .replace(/[\u201C\u201D\u201E\u2033]/g, '"')
      .replace(/[\u2013\u2014\u2015\u2212\u2010\u2011\uFE58\uFE63\uFF0D]/g, '-')
      .replace(/\u2192/g, '->')
      .replace(/\u2190/g, '<-')
      .replace(/\u2026/g, '...')
      .replace(/\u00b7/g, ' ')
      .replace(/\u00d7/g, 'x');
    try {
      if (typeof s.normalize === 'function') {
        s = s.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      }
    } catch (_e) {}
    var out = '';
    for (var i = 0; i < s.length; i++) {
      var code = s.charCodeAt(i);
      out += code <= 255 ? s.charAt(i) : '?';
    }
    return out;
  }

  /**
   * Shared defaults for every html-to-image call we make.
   *
   * `skipFonts: true` is CRITICAL: Fomantic UI's cross-origin stylesheet
   * contains ~4000 `url(https://cdn.jsdelivr.net/gh/jdecked/twemoji/…)` flag
   * references. When html-to-image cannot read a cross-origin sheet's
   * `cssRules` it falls back to fetching the raw CSS text and downloading
   * every `url()` it finds — so without this flag a single export triggers
   * thousands of parallel SVG requests that either hang the tab or abort with
   * ERR_INSUFFICIENT_RESOURCES, which is why Download PNG / PDF appeared to
   * "do nothing". Our cards use only system fonts (Lato / Helvetica Neue /
   * Arial), so skipping webfont embedding is visually a no-op.
   *
   * Do NOT set `imagePlaceholder` here: a 1×1 transparent PNG makes failed
   * images invisible, but combined with low-opacity capture tricks it also
   * produced all-white PNG exports in some browsers.
   */
  function h2iOptions(extra) {
    var base = {
      backgroundColor: '#ffffff',
      cacheBust: true,
      skipFonts: true,
      filter: function (node) {
        if (!node || node.nodeType !== 1) return true;
        if (node.tagName === 'IFRAME') return false;
        if (node.tagName === 'SCRIPT') return false;
        return true;
      },
    };
    if (extra) for (var k in extra) base[k] = extra[k];
    return base;
  }

  /** Wait until every <img> under `root` has loaded (or failed). */
  async function waitImages(root) {
    var imgs = root.querySelectorAll('img');
    await Promise.all(
      Array.from(imgs).map(function (img) {
        if (img.complete && (img.naturalWidth || img.src.indexOf('data:') === 0)) {
          return Promise.resolve();
        }
        return new Promise(function (resolve) {
          var done = function () {
            img.removeEventListener('load', done);
            img.removeEventListener('error', done);
            resolve();
          };
          img.addEventListener('load', done);
          img.addEventListener('error', done);
        });
      })
    );
  }

  /**
   * Temporarily move a node into the viewport so html-to-image captures it
   * with fully-resolved styles. Uses full opacity and a top stacking z-index —
   * `opacity:0.01` / `z-index:-1` caused blank white PNGs in Chromium because
   * the SVG foreignObject snapshot rasterized as empty.
   */
  async function snapshotNode(node, options) {
    var savedCss = node.style.cssText;
    node.style.cssText = savedCss +
      ';left:0 !important;top:0 !important;right:auto !important;bottom:auto !important;' +
      'position:fixed !important;z-index:2147483646 !important;opacity:1 !important;' +
      'pointer-events:none !important;visibility:visible !important;' +
      'transform:none !important;';
    void node.offsetHeight;
    await waitImages(node);
    await new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });
    try {
      return await htmlToImage.toPng(node, h2iOptions(options));
    } finally {
      node.style.cssText = savedCss;
    }
  }

  async function withExportMode(fn) {
    stopObserver();
    feedback('Rendering\u2026');
    try {
      window.__mePaintReport();
      await new Promise(function (r) { requestAnimationFrame(r); });
      await fn();
    } catch (err) {
      console.error('[materialized] export failed', err);
      feedback('Export failed: ' + (err && err.message ? err.message : 'see console'), '#b91c1c');
    } finally {
      startObserver();
    }
  }

  /* --------------------------------------------- button action handlers */

  window.__meDownloadPng = function () {
    console.info('[materialized] __meDownloadPng clicked');
    if (typeof htmlToImage === 'undefined') { missingLib('html-to-image'); return; }
    var node = document.getElementById('me-report-png-card');
    if (!node) { console.warn('[materialized] png card not mounted'); feedback('PNG card not mounted.', '#b91c1c'); return; }
    withExportMode(async function () {
      var dataUrl = await snapshotNode(node, {
        width: 1080,
        height: 1080,
        canvasWidth: 1080,
        canvasHeight: 1080,
        pixelRatio: 1,
      });
      if (!dataUrl || dataUrl.length < 200) throw new Error('empty PNG');
      downloadDataUrl(dataUrl, 'materialized_' + safeName() + '_s' + safeSeed() + '.png');
      feedback('PNG saved (1080\u00d71080)!');
    });
  };

  async function buildReportPngDataUrl() {
    if (typeof htmlToImage === 'undefined') throw new Error('html-to-image library not loaded.');
    var node = document.getElementById('me-report-png-card');
    if (!node) throw new Error('PNG card not mounted.');
    var dataUrl = await snapshotNode(node, {
      width: 1080,
      height: 1080,
      canvasWidth: 1080,
      canvasHeight: 1080,
      pixelRatio: 1,
    });
    if (!dataUrl || dataUrl.length < 200) throw new Error('empty PNG');
    return dataUrl;
  }

  /** Extract gene rows from the hidden `#me-report-pdf-long` DOM subtree.
   * Each row in that element is laid out as
   *   <div>               ← wrapper
   *     <div>             ← header: <span>GENE</span> — <span>trait</span>  (<span>organism</span>)
   *     optional <p class="me-report-evidence-tier">…
   *     optional <p class="me-report-confidence">…
   *     optional <p class="me-report-tested">…
   *     <p class="me-report-desc">description (narrative)</p>
   * We read text content instead of relying on Reflex state so this helper
   * stays self-contained in the browser. */
  function readGeneRows() {
    var root = document.getElementById('me-report-pdf-long');
    if (!root) return [];
    var rows = [];
    var entries = root.querySelectorAll(':scope > div');
    for (var i = 0; i < entries.length; i++) {
      var entry = entries[i];
      var header = entry.querySelector('div');
      if (!header) continue;
      var spans = header.querySelectorAll('span');
      var gene = spans[0] ? (spans[0].textContent || '').trim() : '';
      var trait = spans[2] ? (spans[2].textContent || '').trim() : '';
      var organism = spans[4] ? (spans[4].textContent || '').trim() : '';
      var descEl = entry.querySelector('.me-report-desc');
      var tierEl = entry.querySelector('.me-report-evidence-tier');
      var confEl = entry.querySelector('.me-report-confidence');
      var testedEl = entry.querySelector('.me-report-tested');
      rows.push({
        gene: gene,
        trait: trait,
        organism: organism,
        evidenceTier: tierEl ? (tierEl.textContent || '').replace(/^\s*Evidence tier:\s*/i, '').trim() : '',
        confidence: confEl ? (confEl.textContent || '').replace(/^\s*Confidence:\s*/i, '').trim() : '',
        testedOn: testedEl ? (testedEl.textContent || '').replace(/^\s*Tested on:\s*/i, '').trim() : '',
        description: descEl ? (descEl.textContent || '').trim() : '',
      });
    }
    return rows;
  }

  /** Render the gene library pages directly as jsPDF native text (no
   * rasterization). Keeps the output tiny (tens of KB instead of 20+ MB)
   * and perfectly sharp at any zoom. Handles multi-page flow via
   * explicit y-cursor tracking. */
  function renderGenePages(pdf, rows, layout) {
    var pageW = layout.pageW, pageH = layout.pageH, margin = layout.margin;
    var maxY = pageH - margin;
    var contentW = pageW - margin * 2;
    var y = margin;

    function ensureSpace(h) {
      if (y + h > maxY) {
        pdf.addPage();
        y = margin;
      }
    }

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(16);
    pdf.setTextColor('#1a1a2e');
    ensureSpace(10);
    pdf.text(pdfSafeWinAnsi('Gene library \u2014 full descriptions'), margin, y + 6);
    y += 10;

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(10);
    pdf.setTextColor('#374151');
    var introLines = pdf.splitTextToSize(
      pdfSafeWinAnsi(
        'The sculpture you just generated was shaped by the following genes. ' +
        'Each entry is a short narrative about the gene in its source organism ' +
        '(mechanistic detail is available in the Gene Library tab).'
      ),
      contentW
    );
    ensureSpace(introLines.length * 4.5 + 4);
    pdf.text(introLines, margin, y + 4);
    y += introLines.length * 4.5 + 6;

    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];

      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(10);
      pdf.setTextColor('#1a1a2e');
      var titleLine = pdfSafeWinAnsi(
        r.gene + ' \u2014 ' + r.trait + ' (' + r.organism + ')'
      );
      var titleLines = pdf.splitTextToSize(titleLine, contentW);
      ensureSpace(titleLines.length * 4.5 + 2);
      pdf.text(titleLines, margin, y + 4);
      y += titleLines.length * 4.5 + 2;

      function metaBlock(label, text) {
        if (!text) return;
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(8);
        pdf.setTextColor('#6b7280');
        var line = pdfSafeWinAnsi(label + ': ' + text);
        var lines = pdf.splitTextToSize(line, contentW);
        ensureSpace(lines.length * 3.8 + 1);
        pdf.text(lines, margin, y + 3);
        y += lines.length * 3.8 + 1;
      }
      metaBlock('Evidence tier', r.evidenceTier || '');
      metaBlock('Confidence', r.confidence || '');
      metaBlock('Tested on', r.testedOn || '');

      if (r.description) {
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(9);
        pdf.setTextColor('#374151');
        var descLines = pdf.splitTextToSize(pdfSafeWinAnsi(r.description), contentW);
        ensureSpace(descLines.length * 4);
        pdf.text(descLines, margin, y + 3);
        y += descLines.length * 4 + 1;
      }

      y += 3;
      pdf.setDrawColor('#e5e7eb');
      pdf.setLineWidth(0.2);
      ensureSpace(2);
      pdf.line(margin, y, pageW - margin, y);
      y += 3;
    }
  }

  /**
   * Load a puzzle SVG (served as image), rasterize to PNG data URL for jsPDF.
   * Thumbnail fits a box derived from the sculpture view size (~25–50% of view square).
   */
  function loadPuzzleRasterForPdf(puzzleSrc) {
    if (!puzzleSrc) return Promise.resolve(null);
    var url =
      puzzleSrc.indexOf('http') === 0 ? puzzleSrc : canonicalOrigin() + puzzleSrc;
    return new Promise(function (resolve) {
      var img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = function () {
        var maxPx = 260;
        var w = img.naturalWidth || img.width || 1;
        var h = img.naturalHeight || img.height || 1;
        var scale = Math.min(maxPx / w, maxPx / h, 1);
        var cw = Math.max(1, Math.round(w * scale));
        var ch = Math.max(1, Math.round(h * scale));
        var c = document.createElement('canvas');
        c.width = cw;
        c.height = ch;
        var ctx = c.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, cw, ch);
        ctx.drawImage(img, 0, 0, cw, ch);
        resolve({
          dataUrl: c.toDataURL('image/png'),
          aspect: cw / ch,
        });
      };
      img.onerror = function () {
        resolve(null);
      };
      img.src = url;
    });
  }

  function loadUserpicRasterForPdf() {
    var src = userpicDataUrl();
    if (!src) return Promise.resolve(null);
    return new Promise(function (resolve) {
      var img = new Image();
      img.onload = function () {
        try {
          var size = 256;
          var w = img.naturalWidth || img.width || 1;
          var h = img.naturalHeight || img.height || 1;
          var side = Math.min(w, h);
          var sx = Math.max(0, (w - side) / 2);
          var sy = Math.max(0, (h - side) / 2);
          var c = document.createElement('canvas');
          c.width = size;
          c.height = size;
          var ctx = c.getContext('2d');
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, size, size);
          ctx.drawImage(img, sx, sy, side, side, 0, 0, size, size);
          resolve(c.toDataURL('image/png'));
        } catch (_e) {
          resolve(null);
        }
      };
      img.onerror = function () { resolve(null); };
      img.src = src;
    });
  }

  /** Build a PNG data URL for the share QR (same generator as on-screen QR). */
  function qrDataUrlForShare() {
    return new Promise(function (resolve) {
      if (typeof qrcode === 'undefined') {
        resolve('');
        return;
      }
      try {
        var qr = qrcode(0, 'M');
        qr.addData(reportTargetUrl());
        qr.make();
        var tag = qr.createImgTag(4, 0);
        var div = document.createElement('div');
        div.innerHTML = tag;
        var img = div.querySelector('img');
        if (!img) {
          resolve('');
          return;
        }
        function finish() {
          try {
            var c = document.createElement('canvas');
            c.width = img.naturalWidth || img.width;
            c.height = img.naturalHeight || img.height;
            c.getContext('2d').drawImage(img, 0, 0);
            resolve(c.toDataURL('image/png'));
          } catch (_e) {
            resolve('');
          }
        }
        if (img.complete && img.naturalWidth) {
          finish();
          return;
        }
        img.onload = finish;
        img.onerror = function () { resolve(''); };
      } catch (_e) {
        resolve('');
      }
    });
  }

  /**
   * Page 1 — native A4 layout: header, metadata, three views, categories,
   * source organisms (three columns, one primary trait each), genes-in-composition
   * summary lines, then QR + URL. Full gene narratives are appended on later pages.
   */
  async function renderCoverPageA4(pdf, layout) {
    var m = layout.margin;
    var pageW = layout.pageW;
    var pageH = layout.pageH;
    var w = pageW - m * 2;
    var y = m;
    var coverMaxY = pageH - m - 36;

    function ensureCoverSpace(h) {
      if (y + h > coverMaxY) {
        pdf.addPage();
        y = m;
      }
    }

    var name = pdfSafeWinAnsi((document.getElementById('report-share-name') || {}).value || '');
    var seed = pdfSafeWinAnsi(String((document.getElementById('report-share-seed') || {}).value || ''));
    var points = pdfSafeWinAnsi(String((document.getElementById('report-share-points') || {}).value || ''));
    var note = pdfSafeWinAnsi(characterNote());
    var cats = pdfSafeWinAnsi((document.getElementById('report-export-categories') || {}).value || '');
    var urlText = pdfSafeWinAnsi(
      ((document.getElementById('report-share-url') || {}).textContent || '').trim() ||
      reportTargetUrl()
    );

    var views = window.__reportViews || {};
    var userpic = await loadUserpicRasterForPdf();
    var imgSize = Math.min(52, (w - 6) / 3);

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8);
    pdf.setTextColor(124, 58, 237);
    pdf.text(pdfSafeWinAnsi('MATERIALIZED ENHANCEMENTS'), m, y + 4);
    pdf.setFontSize(18);
    pdf.setTextColor(26, 26, 46);
    pdf.text(pdfSafeWinAnsi('Character enhancement report'), m, y + 12);
    if (userpic) {
      try {
        var portraitSize = 20;
        var portraitX = pageW - m - portraitSize;
        var portraitY = y + 1;
        pdf.setDrawColor(167, 139, 250);
        pdf.setLineWidth(0.35);
        pdf.rect(portraitX - 1, portraitY - 1, portraitSize + 2, portraitSize + 2);
        pdf.addImage(userpic, 'PNG', portraitX, portraitY, portraitSize, portraitSize);
      } catch (_e) {}
    }
    y += userpic ? 26 : 16;

    pdf.setDrawColor(167, 139, 250);
    pdf.setLineWidth(0.35);
    pdf.line(m, y, pageW - m, y);
    y += 5;

    pdf.setFont('courier', 'bold');
    pdf.setFontSize(10);
    pdf.setTextColor(124, 58, 237);
    var stamp = pdfSafeWinAnsi('LOADOUT #' + seed);
    pdf.text(stamp, pageW - m - pdf.getTextWidth(stamp), y);
    y += 6;

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(7);
    pdf.setTextColor(156, 163, 175);
    pdf.text(pdfSafeWinAnsi('CHARACTER'), m, y);
    pdf.text(pdfSafeWinAnsi('SEED'), m + 58, y);
    pdf.text(pdfSafeWinAnsi('POINTS'), m + 108, y);
    y += 4;
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(10);
    pdf.setTextColor(26, 26, 46);
    pdf.text(name, m, y);
    pdf.setFont('courier', 'bold');
    pdf.setTextColor(124, 58, 237);
    pdf.text(seed, m + 58, y);
    pdf.setTextColor(26, 26, 46);
    pdf.text(points, m + 108, y);
    y += 8;

    if (note) {
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(7);
      pdf.setTextColor(107, 114, 128);
      pdf.text(pdfSafeWinAnsi('CHARACTER NOTE'), m, y);
      y += 4;
      pdf.setFont('helvetica', 'italic');
      pdf.setFontSize(8.2);
      pdf.setTextColor(55, 65, 81);
      var noteLines = pdf.splitTextToSize(note, w);
      pdf.text(noteLines, m, y + 3);
      y += noteLines.length * 3.7 + 5;
    }

    var vx = m;
    var labels = ['FRONT', 'SIDE', 'BACK'];
    var keys = ['front', 'side', 'back'];
    for (var vi = 0; vi < 3; vi++) {
      var src = views[keys[vi]];
      var bx = vx + vi * (imgSize + 3);
      pdf.setDrawColor(124, 58, 237);
      pdf.setLineWidth(0.15);
      pdf.rect(bx, y, imgSize, imgSize);
      if (src && src.length > 100) {
        try {
          pdf.addImage(src, 'PNG', bx, y, imgSize, imgSize, undefined, 'FAST');
        } catch (_e) {
          pdf.setFont('helvetica', 'italic');
          pdf.setFontSize(7);
          pdf.setTextColor(156, 163, 175);
          pdf.text('(view)', bx + 2, y + imgSize / 2);
        }
      } else {
        pdf.setFont('helvetica', 'italic');
        pdf.setFontSize(7);
        pdf.setTextColor(156, 163, 175);
        pdf.text('(view)', bx + 2, y + imgSize / 2);
      }
      pdf.setFont('courier', 'bold');
      pdf.setFontSize(6);
      pdf.setTextColor(196, 181, 253);
      pdf.text(labels[vi], bx + 2, y + imgSize - 1);
    }
    y += imgSize + 6;

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8);
    pdf.setTextColor(107, 114, 128);
    pdf.text(pdfSafeWinAnsi('ENHANCEMENT CATEGORIES'), m, y);
    y += 4;
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8);
    pdf.setTextColor(124, 58, 237);
    var catLines = pdf.splitTextToSize(pdfSafeWinAnsi(cats || '\u2014'), w);
    pdf.text(catLines, m, y + 3);
    y += catLines.length * 3.6 + 4;

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8);
    pdf.setTextColor(107, 114, 128);
    pdf.text(pdfSafeWinAnsi('SOURCE ORGANISMS'), m, y);
    y += 4;

    var animalsList = [];
    try {
      var jsonRaw = (document.getElementById('report-export-animals-json') || {}).value || '[]';
      animalsList = JSON.parse(jsonRaw);
    } catch (_e) {
      animalsList = [];
    }

    /* Three columns; compact primary trait only (full list is in gene appendix). */
    var colCount = 3;
    var colGap = 2.8;
    var colW = (w - colGap * (colCount - 1)) / colCount;
    var boxMm = Math.min(14, Math.max(8, imgSize * 0.16));

    function cellMetrics(an, thumb) {
      var orgName = pdfSafeWinAnsi(String(an.organism || ''));
      var traitsArr = an.traits || [];
      var oneTrait =
        an.primary_trait ||
        (traitsArr.length ? traitsArr[0] : '') ||
        '\u2014';
      var traitsStr = pdfSafeWinAnsi(oneTrait);
      var textX = boxMm + 2.5;
      var textW = colW - textX - 1;
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(7.5);
      pdf.setTextColor(26, 26, 46);
      var titleLines = pdf.splitTextToSize(orgName, textW);
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(6.5);
      pdf.setTextColor(55, 65, 81);
      var traitLines = pdf.splitTextToSize(pdfSafeWinAnsi('Trait: ') + traitsStr, textW);
      var textBlockH = titleLines.length * 3.6 + traitLines.length * 3;
      var drawW = boxMm;
      var drawH = boxMm;
      if (thumb && thumb.aspect) {
        var ar = thumb.aspect;
        if (ar >= 1) drawH = boxMm / ar;
        else drawW = boxMm * ar;
      }
      var h = Math.max(textBlockH, thumb ? drawH : 0, 9);
      return {
        titleLines: titleLines,
        traitLines: traitLines,
        textX: textX,
        drawW: drawW,
        drawH: drawH,
        h: h,
      };
    }

    function drawCell(x0, y0, thumb, met) {
      if (thumb && thumb.dataUrl) {
        try {
          pdf.addImage(thumb.dataUrl, 'PNG', x0, y0, met.drawW, met.drawH);
        } catch (_e) {}
      }
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(7.5);
      pdf.setTextColor(26, 26, 46);
      pdf.text(met.titleLines, x0 + met.textX, y0 + 3.5);
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(6.5);
      pdf.setTextColor(55, 65, 81);
      pdf.text(met.traitLines, x0 + met.textX, y0 + 3.5 + met.titleLines.length * 3.6);
    }

    for (var ai = 0; ai < animalsList.length; ai += colCount) {
      var thumbs = [];
      var mets = [];
      var rowH = 0;
      for (var c = 0; c < colCount; c++) {
        var idx = ai + c;
        if (idx >= animalsList.length) break;
        var an = animalsList[idx];
        var th = await loadPuzzleRasterForPdf(an.puzzle_src || '');
        var met = cellMetrics(an, th);
        thumbs.push(th);
        mets.push(met);
        rowH = Math.max(rowH, met.h);
      }

      if (y + rowH > pageH - m - 36) {
        pdf.addPage();
        y = m;
      }

      var yRow = y;
      for (var c2 = 0; c2 < mets.length; c2++) {
        var x0 = m + c2 * (colW + colGap);
        drawCell(x0, yRow, thumbs[c2], mets[c2]);
      }
      y = yRow + rowH + 2.5;
    }

    if (!animalsList.length) {
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(7.5);
      pdf.setTextColor(55, 65, 81);
      var animFallback = pdf.splitTextToSize(
        pdfSafeWinAnsi((document.getElementById('report-export-animals') || {}).value || '\u2014'),
        w
      );
      pdf.text(animFallback, m, y + 3);
      y += animFallback.length * 3.2 + 4;
    }

    var compositionGenes = [];
    try {
      var cgRaw = (document.getElementById('report-export-composition-genes-json') || {}).value || '[]';
      compositionGenes = JSON.parse(cgRaw);
    } catch (_e) {
      compositionGenes = [];
    }

    if (compositionGenes.length) {
      ensureCoverSpace(10);
      y += 4;
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(8);
      pdf.setTextColor(107, 114, 128);
      pdf.text(pdfSafeWinAnsi('GENES IN COMPOSITION'), m, y);
      y += 4;
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(7.2);
      pdf.setTextColor(55, 65, 81);
      for (var gi = 0; gi < compositionGenes.length; gi++) {
        var cg = compositionGenes[gi];
        var gLine =
          String(cg.gene || '') +
          ' \u2014 ' +
          String(cg.category_detail || '') +
          (cg.source_organism ? ' (' + String(cg.source_organism) + ')' : '');
        var gLines = pdf.splitTextToSize(pdfSafeWinAnsi(gLine), w);
        ensureCoverSpace(gLines.length * 3.1 + 1);
        pdf.text(gLines, m, y + 3);
        y += gLines.length * 3.1 + 0.4;
      }
      y += 2;
    }

    /* Footer after organisms + composition summary (full narratives: appendix pages). */
    y += 6;
    var urlLines = pdf.splitTextToSize(urlText, w - 26);
    var footerH = 22 + Math.max(18, urlLines.length * 3.2);
    if (y + footerH > pageH - m) {
      pdf.addPage();
      y = m;
    }

    var qrUrl = await qrDataUrlForShare();
    var fy = y;
    if (qrUrl) {
      try {
        pdf.addImage(qrUrl, 'PNG', m, fy, 22, 22);
      } catch (_e) {}
    }
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(9);
    pdf.setTextColor(124, 58, 237);
    pdf.text(pdfSafeWinAnsi('materialized-enhancements'), m + 26, fy + 7);
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(7.5);
    pdf.setTextColor(107, 114, 128);
    pdf.text(pdfSafeWinAnsi('GlucoseDAO \u00b7 Longevity Genie'), m + 26, fy + 13);
    pdf.setFont('courier', 'normal');
    pdf.setFontSize(6.5);
    pdf.setTextColor(107, 114, 128);
    pdf.text(urlLines, m + 26, fy + 19);
  }

  async function buildReportPdf() {
    var pdf = new jspdf.jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4', compress: true });
    var layout = { pageW: 210, pageH: 297, margin: 15 };
    await renderCoverPageA4(pdf, layout);
    var rows = readGeneRows();
    if (rows.length) {
      pdf.addPage();
      renderGenePages(pdf, rows, layout);
    }
    return pdf;
  }

  window.__meDownloadPdf = function () {
    console.info('[materialized] __meDownloadPdf clicked');
    if (typeof jspdf === 'undefined') { missingLib('jsPDF'); return; }
    withExportMode(async function () {
      var pdf = await buildReportPdf();
      pdf.save('materialized_' + safeName() + '_s' + safeSeed() + '.pdf');
      feedback('PDF saved!');
    });
  };

  async function waitReportMounted(timeoutMs) {
    var deadline = Date.now() + (timeoutMs || 6000);
    while (!document.getElementById('me-report-card') && Date.now() < deadline) {
      await new Promise(function (r) { setTimeout(r, 100); });
    }
    if (!document.getElementById('me-report-card')) {
      throw new Error('Report card not mounted.');
    }
  }

  /**
   * Build the same A4 PDF as __meDownloadPdf but resolve with
   * {filename, base64} instead of triggering a download. Used by the
   * "Send STL + report" button to attach the PDF to the outgoing email.
   *
   * Waits up to `timeoutMs` for the report DOM to mount, since the user may
   * not have expanded the Share & Report section before clicking Send.
   * Always resolves (never rejects); on error returns {error: "..."}.
   */
  window.__meBuildReportPdfBase64 = async function (timeoutMs) {
    timeoutMs = timeoutMs || 6000;
    if (typeof jspdf === 'undefined') {
      return JSON.stringify({ error: 'jsPDF library not loaded.' });
    }
    stopObserver();
    try {
      await waitReportMounted(timeoutMs);
      window.__mePaintReport();
      await new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });
      var pdf = await buildReportPdf();
      // jsPDF's `datauristring` returns "data:application/pdf;filename=...;base64,<b64>"
      var dataUri = pdf.output('datauristring');
      var b64 = dataUrlBase64(dataUri, 'PDF');
      var filename = 'materialized_' + safeName() + '_s' + safeSeed() + '.pdf';
      return JSON.stringify({ filename: filename, base64: b64 });
    } catch (err) {
      console.error('[materialized] __meBuildReportPdfBase64 failed', err);
      return JSON.stringify({ error: (err && err.message) ? err.message : String(err) });
    } finally {
      startObserver();
    }
  };

  window.__meBuildReportBundleBase64 = async function (timeoutMs, publishedUrlOverride) {
    timeoutMs = timeoutMs || 8000;
    if (typeof jspdf === 'undefined') {
      return JSON.stringify({ error: 'jsPDF library not loaded.' });
    }
    if (typeof htmlToImage === 'undefined') {
      return JSON.stringify({ error: 'html-to-image library not loaded.' });
    }
    window.__mePendingPublishedReportUrl = browserAbsoluteUrl(publishedUrlOverride);
    stopObserver();
    try {
      await waitReportMounted(timeoutMs);
      window.__mePaintReport();
      await new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });
      var pngDataUrl = await buildReportPngDataUrl();
      var pdf = await buildReportPdf();
      var pdfDataUri = pdf.output('datauristring');
      return JSON.stringify({
        png_filename: 'materialized_' + safeName() + '_s' + safeSeed() + '.png',
        png_base64: dataUrlBase64(pngDataUrl, 'PNG'),
        pdf_filename: 'materialized_' + safeName() + '_s' + safeSeed() + '.pdf',
        pdf_base64: dataUrlBase64(pdfDataUri, 'PDF'),
        share_url: reportTargetUrl(),
      });
    } catch (err) {
      console.error('[materialized] __meBuildReportBundleBase64 failed', err);
      return JSON.stringify({ error: (err && err.message) ? err.message : String(err) });
    } finally {
      if (!publishedReportUrl()) window.__mePendingPublishedReportUrl = '';
      startObserver();
    }
  };

  window.__meCopyShareLink = async function () {
    var url = reportTargetUrl();
    if (!url) {
      feedback('Generate a sharable folder first.', '#b45309');
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
    } catch (_e) {
      var ta = document.createElement('textarea');
      ta.value = url;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); } catch (__) {}
      document.body.removeChild(ta);
    }
    feedback('Copied!');
  };

  window.__meShareIntent = function (network) {
    var rawUrl = reportTargetUrl();
    if (!rawUrl) {
      feedback('Generate a sharable folder first.', '#b45309');
      return;
    }
    var url = encodeURIComponent(rawUrl);
    var text = encodeURIComponent('My Materialized Enhancements personal enhancement report');
    var target = '';
    if (network === 'twitter')       target = 'https://twitter.com/intent/tweet?text=' + text + '&url=' + url;
    else if (network === 'facebook') target = 'https://www.facebook.com/sharer/sharer.php?u=' + url;
    else if (network === 'linkedin') target = 'https://www.linkedin.com/sharing/share-offsite/?url=' + url;
    if (target) window.open(target, '_blank', 'noopener,noreferrer,width=640,height=520');
  };

  console.info('[materialized] Share & Report helpers booted');
})();
