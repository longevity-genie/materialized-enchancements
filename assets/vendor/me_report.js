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
  function publishedReportPdfUrl() {
    var el = document.getElementById('report-pdf-url');
    return el && el.value ? String(el.value).trim() : '';
  }
  function generatedShareUrl() {
    return window.__mePendingPublishedReportUrl || publishedReportUrl();
  }
  /** Server-provided canonical origin (DEPLOY_URL); falls back to browser. */
  function canonicalOrigin() {
    var el = document.getElementById('report-canonical-base');
    var v = el && el.value ? String(el.value).trim().replace(/\/+$/, '') : '';
    if (v) return v;
    return window.location.origin;
  }
  function absoluteShareUrl() {
    var p = sharePath();
    var origin = canonicalOrigin();
    if (!p) return '';
    if (/^https?:\/\//i.test(p)) return p;
    if (p.charAt(0) === '/') return origin + p;
    return origin + '/' + (p.charAt(0) === '?' ? '' : '') + p;
  }
  function reportTargetUrl() {
    return generatedShareUrl();
  }
  function publicReportTargetUrl() {
    return generatedShareUrl();
  }
  function reportPdfTargetUrl() {
    return reportTargetUrl() || absoluteShareUrl();
  }
  function canonicalAbsoluteUrl(pathOrUrl) {
    var v = String(pathOrUrl || '').trim();
    if (!v) return '';
    if (/^https?:\/\//i.test(v)) return v;
    if (v.charAt(0) === '/') return canonicalOrigin() + v;
    return canonicalOrigin() + '/' + v;
  }
  function localAssetUrl(pathOrUrl) {
    var v = String(pathOrUrl || '').trim();
    if (!v) return '';
    if (/^https?:\/\//i.test(v) || v.indexOf('data:') === 0) return v;
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
    var url = publicReportTargetUrl();
    urlEl.textContent = url || 'Create a public link to generate the QR and sharing buttons.';
  }

  function qrPlaceholder(el) {
    if (!el) return false;
    el.innerHTML = '';
    var span = document.createElement('span');
    span.textContent = 'Create public link';
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
    var url = publicReportTargetUrl();
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
      ['char-view-front',   v.front],
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
    var urlEl = document.getElementById('report-share-url');
    var qrEl = document.getElementById('report-qr');
    var needsInitialPaint =
      (urlEl && !urlEl.textContent) ||
      (qrEl && !qrEl.childNodes.length);
    if (url !== lastShareUrl || needsInitialPaint) {
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
    var root = document.getElementById('me-report-observer-root');
    if (!root) {
      if (window.location.pathname === '/materialization') window.setTimeout(startObserver, 250);
      return;
    }
    observer = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var n = mutations[i].target;
        while (n && n !== root) {
          if (n.id === 'report-qr' ||
              n.id === 'me-report-pdf-long' || n.id === 'me-report-png-card' || n.id === 'me-report-png-card-character' ||
              n.id === 'report-export-animals-json' ||
              n.id === 'report-export-composition-genes-json') return;
          n = n.parentNode;
        }
      }
      schedule();
    });
    observer.observe(root, { childList: true, subtree: true });
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

  function pdfFeedback(text, color) {
    var fb = document.getElementById('report-pdf-feedback');
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

  async function withTimeout(promise, timeoutMs, message) {
    var timer = null;
    try {
      return await Promise.race([
        promise,
        new Promise(function (_resolve, reject) {
          timer = setTimeout(function () {
            reject(new Error(message || 'Rendering timed out.'));
          }, timeoutMs || 8000);
        }),
      ]);
    } finally {
      if (timer) clearTimeout(timer);
    }
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
          var timer = null;
          var done = function () {
            if (timer) clearTimeout(timer);
            img.removeEventListener('load', done);
            img.removeEventListener('error', done);
            resolve();
          };
          timer = setTimeout(done, 3000);
          img.addEventListener('load', done);
          img.addEventListener('error', done);
        });
      })
    );
  }

  /**
   * Snapshot a temporary clone in an invisible capture host. The clone must stay
   * renderable for html-to-image, but the host itself must not contribute pixels
   * to the live page; otherwise mobile browsers briefly flash the report over
   * the current view while sharing/exporting.
   */
  async function snapshotNode(node, options) {
    var host = document.createElement('div');
    var clone = node.cloneNode(true);
    clone.removeAttribute('id');
    clone.setAttribute('aria-hidden', 'true');
    host.style.cssText =
      'position:fixed !important;left:0 !important;top:0 !important;' +
      'width:' + ((options && options.width) || 1080) + 'px !important;' +
      'height:' + ((options && options.height) || 1080) + 'px !important;' +
      'overflow:visible !important;opacity:0 !important;pointer-events:none !important;' +
      'visibility:visible !important;z-index:2147483646 !important;' +
      'contain:layout style !important;';
    clone.style.cssText = node.style.cssText +
      ';left:0 !important;top:0 !important;right:auto !important;bottom:auto !important;' +
      'position:relative !important;z-index:0 !important;opacity:1 !important;' +
      'pointer-events:none !important;visibility:visible !important;' +
      'transform:none !important;';
    host.appendChild(clone);
    document.body.appendChild(host);
    void clone.offsetHeight;
    await waitImages(clone);
    await new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });
    try {
      var canvas = await htmlToImage.toCanvas(clone, h2iOptions(options));
      return canvas.toDataURL('image/webp', 0.92);
    } finally {
      if (host.parentNode) host.parentNode.removeChild(host);
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

  function activeCardId() {
    var el = document.getElementById('report-card-mode');
    var mode = el && el.value ? String(el.value).trim() : 'model';
    return mode === 'character' ? 'me-report-png-card-character' : 'me-report-png-card';
  }

  window.__meDownloadPng = function () {
    console.info('[materialized] __meDownloadPng clicked');
    if (typeof htmlToImage === 'undefined') { missingLib('html-to-image'); return; }
    var node = document.getElementById(activeCardId());
    if (!node) { console.warn('[materialized] png card not mounted'); feedback('PNG card not mounted.', '#b91c1c'); return; }
    withExportMode(async function () {
      var dataUrl = await snapshotNode(node, {
        width: 1080,
        height: 1080,
        canvasWidth: 1080,
        canvasHeight: 1080,
        pixelRatio: 1,
      });
      if (!dataUrl || dataUrl.length < 200) throw new Error('empty WebP');
      downloadDataUrl(dataUrl, 'materialized_' + safeName() + '_s' + safeSeed() + '.webp');
      feedback('WebP saved (1080\u00d71080)!');
    });
  };

  async function buildReportPngDataUrl() {
    if (typeof htmlToImage === 'undefined') throw new Error('html-to-image library not loaded.');
    var node = document.getElementById(activeCardId());
    if (!node) throw new Error('PNG card not mounted.');
    var dataUrl = await snapshotNode(node, {
      width: 1080,
      height: 1080,
      canvasWidth: 1080,
      canvasHeight: 1080,
      pixelRatio: 1,
    });
    if (!dataUrl || dataUrl.length < 200) throw new Error('empty WebP');
    return dataUrl;
  }

  window.__meGenerateShareCard = async function (timeoutMs) {
    timeoutMs = timeoutMs || 6000;
    if (typeof htmlToImage === 'undefined') {
      return JSON.stringify({ error: 'html-to-image library not loaded.' });
    }
    stopObserver();
    try {
      await waitReportMounted(timeoutMs);
      window.__mePaintReport();
      await new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });
      var dataUrl = await buildReportPngDataUrl();
      return JSON.stringify({ data_url: dataUrl });
    } catch (err) {
      console.error('[materialized] __meGenerateShareCard failed', err);
      return JSON.stringify({ error: (err && err.message) ? err.message : String(err) });
    } finally {
      startObserver();
    }
  };

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
      var gene = (header.getAttribute('data-gene') || '').trim();
      var trait = (header.getAttribute('data-trait') || '').trim();
      var organism = (header.getAttribute('data-organism') || '').trim();
      var puzzleSrc = (header.getAttribute('data-puzzle-src') || '').trim();
      var descEl = entry.querySelector('.me-report-desc');
      var tierEl = entry.querySelector('.me-report-evidence-tier');
      var confEl = entry.querySelector('.me-report-confidence');
      var testedEl = entry.querySelector('.me-report-tested');
      rows.push({
        gene: gene,
        trait: trait,
        organism: organism,
        puzzleSrc: puzzleSrc,
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
  async function renderGenePages(pdf, rows, layout) {
    var silhouettes = {};
    var uniqueSrcs = [];
    for (var si = 0; si < rows.length; si++) {
      var src = rows[si].puzzleSrc;
      if (src && uniqueSrcs.indexOf(src) < 0) uniqueSrcs.push(src);
    }
    var loadPromises = uniqueSrcs.map(function (src) {
      return loadPuzzleRasterForPdf(src).then(function (result) {
        if (result) silhouettes[src] = result;
      });
    });
    await Promise.all(loadPromises);

    var pageW = layout.pageW, pageH = layout.pageH, margin = layout.margin;
    var maxY = pageH - margin;
    var contentW = pageW - margin * 2;
    var cardPad = 4;
    var silW = 16;
    var cardInner = contentW - cardPad - 2;
    var y = margin;
    var palette = {
      'Stress Resistance': [124, 58, 237],
      'Longevity & Genome': [14, 165, 233],
      'Environmental Adaptation': [16, 185, 129],
      'Regeneration': [245, 158, 11],
      'Perception': [236, 72, 153],
      'Expression': [99, 102, 241],
    };
    function catRgb(trait) {
      for (var k in palette) {
        if (trait && trait.indexOf(k) === 0) return palette[k];
      }
      return [124, 58, 237];
    }

    function ensureSpace(h) {
      if (y + h > maxY) {
        pdf.addPage();
        y = margin;
      }
    }

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(16);
    pdf.setTextColor(26, 26, 46);
    ensureSpace(10);
    pdf.text(pdfSafeWinAnsi('Gene library'), margin, y + 6);
    y += 10;

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(9);
    pdf.setTextColor(55, 65, 81);
    var introLines = pdf.splitTextToSize(
      pdfSafeWinAnsi(
        'Full narratives for each selected gene. Each entry describes the gene ' +
        'in its source organism with evidence tier and testing context.'
      ),
      contentW
    );
    ensureSpace(introLines.length * 4 + 4);
    pdf.text(introLines, margin, y + 4);
    y += introLines.length * 4 + 6;

    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      var accentRgb = catRgb(r.trait);

      var geneName = pdfSafeWinAnsi(r.gene || '');
      var traitText = pdfSafeWinAnsi(r.trait || '');
      var orgText = pdfSafeWinAnsi(r.organism || '');
      var descText = r.description ? pdfSafeWinAnsi(r.description) : '';
      var sil = r.puzzleSrc ? silhouettes[r.puzzleSrc] : null;
      var silReserve = sil ? silW + 4 : 0;
      var textW = cardInner - 4 - silReserve;
      var descLines = descText ? pdf.splitTextToSize(descText, textW) : [];
      var metaCount = 0;
      if (r.evidenceTier) metaCount++;
      if (r.confidence) metaCount++;
      if (r.testedOn) metaCount++;
      var orgLineH = orgText ? 4 : 0;
      var cardH = 14 + orgLineH + metaCount * 4 + descLines.length * 3.6 + 6;
      if (sil) cardH = Math.max(cardH, silW / sil.aspect + 10);

      ensureSpace(Math.min(cardH, 50));

      pdf.setFillColor(accentRgb[0], accentRgb[1], accentRgb[2]);
      pdf.rect(margin, y, 1.5, Math.min(cardH, maxY - y), 'F');

      pdf.setDrawColor(229, 231, 235);
      pdf.setFillColor(255, 255, 255);
      pdf.setLineWidth(0.2);
      pdf.rect(margin + 1.5, y, contentW - 1.5, Math.min(cardH, maxY - y), 'FD');

      if (sil) {
        var silH = silW / sil.aspect;
        var silX = margin + contentW - silW - 3;
        var silY = y + 3;
        try {
          pdf.addImage(sil.dataUrl, 'PNG', silX, silY, silW, silH, undefined, 'FAST');
        } catch (_es) {}
      }

      var cx = margin + cardPad + 2;
      var cy = y + 5;

      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(10);
      pdf.setTextColor(26, 26, 46);
      pdf.text(pdf.splitTextToSize(geneName, textW)[0] || '', cx, cy);
      cy += 4.5;

      if (orgText) {
        pdf.setFont('helvetica', 'italic');
        pdf.setFontSize(8);
        pdf.setTextColor(13, 148, 136);
        pdf.text(pdf.splitTextToSize(orgText, textW)[0] || '', cx, cy);
        cy += 4;
      }

      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(7.5);
      pdf.setTextColor(accentRgb[0], accentRgb[1], accentRgb[2]);
      pdf.text(pdf.splitTextToSize(traitText, textW)[0] || '', cx, cy);
      cy += 5;

      function metaLine(lbl, val) {
        if (!val) return;
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(7);
        pdf.setTextColor(156, 163, 175);
        pdf.text(pdfSafeWinAnsi(lbl + ':'), cx, cy);
        var lblW = pdf.getTextWidth(pdfSafeWinAnsi(lbl + ': '));
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(7);
        pdf.setTextColor(75, 85, 99);
        var valLines = pdf.splitTextToSize(pdfSafeWinAnsi(val), textW - lblW - 2);
        pdf.text(valLines[0] || '', cx + lblW, cy);
        cy += 4;
      }
      metaLine('Evidence', r.evidenceTier || '');
      metaLine('Confidence', r.confidence || '');
      metaLine('Tested on', r.testedOn || '');

      if (descLines.length) {
        cy += 1;
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(8);
        pdf.setTextColor(55, 65, 81);
        for (var dl = 0; dl < descLines.length; dl++) {
          if (cy + 3.6 > maxY) {
            pdf.addPage();
            y = margin;
            cy = margin + 4;
            var remainLines = descLines.length - dl;
            var contH = Math.min(remainLines * 3.6 + 8, maxY - margin);
            pdf.setFillColor(accentRgb[0], accentRgb[1], accentRgb[2]);
            pdf.rect(margin, y, 1.5, contH, 'F');
            pdf.setDrawColor(229, 231, 235);
            pdf.setFillColor(255, 255, 255);
            pdf.setLineWidth(0.2);
            pdf.rect(margin + 1.5, y, contentW - 1.5, contH, 'FD');
            pdf.setFont('helvetica', 'normal');
            pdf.setFontSize(8);
            pdf.setTextColor(55, 65, 81);
          }
          pdf.text(descLines[dl], cx, cy);
          cy += 3.6;
        }
      }

      y = cy + 5;
    }
  }

  /**
   * Load a puzzle SVG (served as image), rasterize to PNG data URL for jsPDF.
   * Thumbnail fits a box derived from the sculpture view size (~25–50% of view square).
   */
  function loadPuzzleRasterForPdf(puzzleSrc) {
    if (!puzzleSrc) return Promise.resolve(null);
    var url = localAssetUrl(puzzleSrc);
    return new Promise(function (resolve) {
      var img = new Image();
      var timer = null;
      var done = function (value) {
        if (timer) clearTimeout(timer);
        resolve(value);
      };
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
        done({
          dataUrl: c.toDataURL('image/png'),
          aspect: cw / ch,
        });
      };
      img.onerror = function () {
        done(null);
      };
      timer = setTimeout(function () { done(null); }, 3000);
      img.src = url;
    });
  }

  function loadUserpicRasterForPdf() {
    var src = userpicDataUrl();
    if (!src) return Promise.resolve(null);
    return new Promise(function (resolve) {
      var img = new Image();
      var timer = null;
      var done = function (value) {
        if (timer) clearTimeout(timer);
        resolve(value);
      };
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
          done(c.toDataURL('image/png'));
        } catch (_e) {
          done(null);
        }
      };
      img.onerror = function () { done(null); };
      timer = setTimeout(function () { done(null); }, 3000);
      img.src = src;
    });
  }

  function loadHumanRasterForPdf() {
    return new Promise(function (resolve) {
      var img = new Image();
      var timer = null;
      var done = function (value) {
        if (timer) clearTimeout(timer);
        resolve(value);
      };
      img.crossOrigin = 'anonymous';
      img.onload = function () {
        try {
          var maxH = 620;
          var w = img.naturalWidth || img.width || 1;
          var h = img.naturalHeight || img.height || 1;
          var scale = Math.min(maxH / h, 1);
          var cw = Math.max(1, Math.round(w * scale));
          var ch = Math.max(1, Math.round(h * scale));
          var c = document.createElement('canvas');
          c.width = cw;
          c.height = ch;
          var ctx = c.getContext('2d');
          ctx.clearRect(0, 0, cw, ch);
          ctx.drawImage(img, 0, 0, cw, ch);
          done({
            dataUrl: c.toDataURL('image/png'),
            aspect: cw / ch,
          });
        } catch (_e) {
          done(null);
        }
      };
      img.onerror = function () { done(null); };
      timer = setTimeout(function () { done(null); }, 3000);
      img.src = localAssetUrl('/images/body_only.webp');
    });
  }

  /** Build a PNG data URL for the share QR (same generator as on-screen QR). */
  function qrDataUrlForShare(urlOverride) {
    return new Promise(function (resolve) {
      if (typeof qrcode === 'undefined') {
        resolve('');
        return;
      }
      try {
        var targetUrl = urlOverride || reportTargetUrl();
        if (!targetUrl) {
          resolve('');
          return;
        }
        var qr = qrcode(0, 'M');
        qr.addData(targetUrl);
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

    var name = pdfSafeWinAnsi((document.getElementById('report-share-name') || {}).value || '');
    var seed = pdfSafeWinAnsi(String((document.getElementById('report-share-seed') || {}).value || ''));
    var points = pdfSafeWinAnsi(String((document.getElementById('report-share-points') || {}).value || ''));
    var note = pdfSafeWinAnsi(characterNote());
    var catsRaw = String((document.getElementById('report-export-categories') || {}).value || '');
    var cats = catsRaw.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    var urlText = pdfSafeWinAnsi(reportPdfTargetUrl());

    var animalsList = [];
    var compositionGenes = [];
    try {
      animalsList = JSON.parse((document.getElementById('report-export-animals-json') || {}).value || '[]');
    } catch (_e) {
      animalsList = [];
    }
    try {
      compositionGenes = JSON.parse((document.getElementById('report-export-composition-genes-json') || {}).value || '[]');
    } catch (_e2) {
      compositionGenes = [];
    }

    var userpic = await loadUserpicRasterForPdf();
    var human = await loadHumanRasterForPdf();
    var qrUrl = await qrDataUrlForShare(urlText);
    var palette = {
      'Stress Resistance': [124, 58, 237],
      'Longevity & Genome': [14, 165, 233],
      'Environmental Adaptation': [16, 185, 129],
      'Regeneration': [245, 158, 11],
      'Perception': [236, 72, 153],
      'Expression': [99, 102, 241],
    };
    var bodyPos = {
      'Expression': [0.39, 0.24],
      'Perception': [0.61, 0.24],
      'Longevity & Genome': [0.32, 0.50],
      'Stress Resistance': [0.68, 0.50],
      'Environmental Adaptation': [0.36, 0.76],
      'Regeneration': [0.64, 0.76],
    };
    var countsByCat = {};
    for (var ci = 0; ci < cats.length; ci++) countsByCat[cats[ci]] = 0;
    for (var gi = 0; gi < compositionGenes.length; gi++) {
      var catName = String(compositionGenes[gi].category || '');
      if (catName) countsByCat[catName] = (countsByCat[catName] || 0) + 1;
    }

    function rgb(cat) {
      return palette[cat] || [124, 58, 237];
    }
    function rounded(x, yy, ww, hh, mode, radius) {
      var r = radius || 2.5;
      if (pdf.roundedRect) pdf.roundedRect(x, yy, ww, hh, r, r, mode || 'S');
      else pdf.rect(x, yy, ww, hh, mode || 'S');
    }
    function label(text, x, yy) {
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(6.8);
      pdf.setTextColor(107, 114, 128);
      pdf.text(pdfSafeWinAnsi(String(text || '').toUpperCase()), x, yy);
    }
    function card(x, yy, ww, hh, title) {
      pdf.setDrawColor(229, 231, 235);
      pdf.setFillColor(255, 255, 255);
      pdf.setLineWidth(0.25);
      rounded(x, yy, ww, hh, 'FD', 3);
      if (title) {
        label(title, x + 4, yy + 7);
        pdf.setDrawColor(229, 231, 235);
        pdf.line(x + 4, yy + 10, x + ww - 4, yy + 10);
      }
    }
    function statBox(x, yy, ww, title, value, accent) {
      var c = accent || [124, 58, 237];
      pdf.setDrawColor(229, 231, 235);
      pdf.setFillColor(249, 250, 251);
      rounded(x, yy, ww, 19, 'FD', 2.5);
      label(title, x + 3, yy + 6);
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(11);
      pdf.setTextColor(c[0], c[1], c[2]);
      pdf.text(pdfSafeWinAnsi(String(value || '\u2014')), x + 3, yy + 14);
    }
    function systemPill(cat, x, yy, ww) {
      var c = rgb(cat);
      pdf.setDrawColor(c[0], c[1], c[2]);
      pdf.setFillColor(255, 255, 255);
      rounded(x, yy, ww, 8, 'S', 4);
      pdf.setFillColor(c[0], c[1], c[2]);
      pdf.circle(x + 4, yy + 4, 1.3, 'F');
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(6.6);
      pdf.setTextColor(31, 41, 55);
      var txt = pdfSafeWinAnsi(cat + ' (' + (countsByCat[cat] || 0) + ')');
      pdf.text(pdf.splitTextToSize(txt, ww - 9), x + 7, yy + 4.9);
    }

    pdf.setFillColor(248, 249, 250);
    pdf.rect(0, 0, pageW, pageH, 'F');

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8);
    pdf.setTextColor(124, 58, 237);
    pdf.text(pdfSafeWinAnsi('MATERIALIZED ENHANCEMENTS'), m, y + 4);
    pdf.setFontSize(22);
    pdf.setTextColor(26, 26, 46);
    pdf.text(pdfSafeWinAnsi('Personal enhancement report'), m, y + 15);
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8.5);
    pdf.setTextColor(107, 114, 128);
    pdf.text(pdfSafeWinAnsi('A character-sheet summary of selected enhancement systems, source organisms, and genes.'), m, y + 22);

    pdf.setFillColor(243, 240, 255);
    pdf.setDrawColor(212, 197, 249);
    rounded(pageW - m - 42, y + 1, 42, 15, 'FD', 4);
    pdf.setFont('courier', 'bold');
    pdf.setFontSize(8.5);
    pdf.setTextColor(109, 40, 217);
    pdf.text(pdfSafeWinAnsi('LOADOUT #' + seed), pageW - m - 39, y + 10);
    if (userpic) {
      try {
        pdf.addImage(userpic, 'PNG', pageW - m - 65, y, 18, 18);
        pdf.setDrawColor(167, 139, 250);
        pdf.rect(pageW - m - 65, y, 18, 18);
      } catch (_e3) {}
    }
    y += 30;

    var statW = (w - 8) / 3;
    statBox(m, y, statW, 'Character', name || '\u2014', [26, 26, 46]);
    statBox(m + statW + 4, y, statW, 'Model points', points || '\u2014', [124, 58, 237]);
    statBox(m + (statW + 4) * 2, y, statW, 'Selected genes', String(compositionGenes.length || 0), [16, 185, 129]);
    y += 25;

    if (note) {
      card(m, y, w, 20, 'Character note');
      pdf.setFont('helvetica', 'italic');
      pdf.setFontSize(8);
      pdf.setTextColor(55, 65, 81);
      var noteLines = pdf.splitTextToSize(note, w - 10);
      pdf.text(noteLines.slice(0, 3), m + 5, y + 15);
      y += 24;
    }

    var mainY = y;
    var bodyW = 78;
    var mainH = 116;
    var sideX = m + bodyW + 7;
    var sideW = w - bodyW - 7;
    card(m, mainY, bodyW, mainH, 'Body-map selection');
    var bodyImgX = m + 17;
    var bodyImgY = mainY + 16;
    var bodyImgH = 72;
    var bodyImgW = 40;
    if (human && human.dataUrl) {
      bodyImgW = Math.min(48, bodyImgH * human.aspect);
      bodyImgX = m + (bodyW - bodyImgW) / 2;
      try {
        pdf.addImage(human.dataUrl, 'PNG', bodyImgX, bodyImgY, bodyImgW, bodyImgH, undefined, 'FAST');
      } catch (_e4) {}
    } else {
      pdf.setDrawColor(156, 163, 175);
      pdf.ellipse(m + bodyW / 2, bodyImgY + 8, 5, 6, 'S');
      pdf.line(m + bodyW / 2, bodyImgY + 14, m + bodyW / 2, bodyImgY + 48);
      pdf.line(m + bodyW / 2, bodyImgY + 23, m + bodyW / 2 - 12, bodyImgY + 34);
      pdf.line(m + bodyW / 2, bodyImgY + 23, m + bodyW / 2 + 12, bodyImgY + 34);
      pdf.line(m + bodyW / 2, bodyImgY + 48, m + bodyW / 2 - 10, bodyImgY + 70);
      pdf.line(m + bodyW / 2, bodyImgY + 48, m + bodyW / 2 + 10, bodyImgY + 70);
    }
    for (var mc = 0; mc < cats.length; mc++) {
      var mp = bodyPos[cats[mc]];
      if (!mp) continue;
      var mrgb = rgb(cats[mc]);
      var pinX = bodyImgX + bodyImgW * mp[0];
      var pinY = bodyImgY + bodyImgH * mp[1];
      pdf.setFillColor(mrgb[0], mrgb[1], mrgb[2]);
      pdf.setDrawColor(255, 255, 255);
      pdf.circle(pinX, pinY, 3, 'FD');
      var pinCount = countsByCat[cats[mc]] || 0;
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(6);
      pdf.setTextColor(255, 255, 255);
      pdf.text(String(pinCount), pinX - (pinCount >= 10 ? 1.8 : 1), pinY + 1.8);
    }

    card(sideX, mainY, sideW, mainH, 'Selected systems');
    var pillY = mainY + 15;
    for (var pc = 0; pc < cats.length; pc++) {
      systemPill(cats[pc], sideX + 4, pillY, sideW - 8);
      pillY += 9.5;
      if (pillY > mainY + 68) break;
    }
    var summaryY = mainY + 78;
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8.5);
    pdf.setTextColor(26, 26, 46);
    pdf.text(pdfSafeWinAnsi('Character build'), sideX + 4, summaryY);
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(7.2);
    pdf.setTextColor(55, 65, 81);
    var summary = [
      'Source organisms: ' + animalsList.length,
      'Enhancement systems: ' + cats.length,
      'Selected genes: ' + compositionGenes.length,
    ];
    pdf.text(pdf.splitTextToSize(pdfSafeWinAnsi(summary.join('  \u00b7  ')), sideW - 8), sideX + 4, summaryY + 6);
    y = mainY + mainH + 7;

    var orgCols = 3;
    var orgColW = (w - 4 * (orgCols + 1)) / orgCols;
    var orgRowH = 7.5;
    var maxOrg = animalsList.length;
    var orgRows = Math.ceil(maxOrg / orgCols);
    var orgCardH = 14 + orgRows * orgRowH + 4;
    card(m, y, w, orgCardH, 'Source organisms');
    var orgX = m + 4;
    var orgY = y + 15;
    for (var oi = 0; oi < maxOrg; oi++) {
      var an = animalsList[oi] || {};
      var ox = orgX + (oi % orgCols) * (orgColW + 4);
      var oy = orgY + Math.floor(oi / orgCols) * orgRowH;
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(6.8);
      pdf.setTextColor(26, 26, 46);
      var orgName = String(an.common_name || an.organism || '\u2014');
      pdf.text(pdf.splitTextToSize(pdfSafeWinAnsi(orgName), orgColW - 2)[0] || '', ox, oy);
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(6.2);
      pdf.setTextColor(75, 85, 99);
      pdf.text(pdf.splitTextToSize(pdfSafeWinAnsi(an.primary_trait || '\u2014'), orgColW - 2)[0] || '', ox, oy + 3.4);
    }
    y += orgCardH + 7;

    var geneCols = 3;
    var geneColW = (w - 4 * (geneCols + 1)) / geneCols;
    var geneRowH = 7;
    var maxGenes = compositionGenes.length;
    var geneRows = Math.ceil(maxGenes / geneCols);
    var geneCardH = 14 + geneRows * geneRowH + 4;
    card(m, y, w, geneCardH, 'Gene loadout');
    for (var cgIdx = 0; cgIdx < maxGenes; cgIdx++) {
      var cg = compositionGenes[cgIdx] || {};
      var gx = m + 4 + (cgIdx % geneCols) * (geneColW + 4);
      var gy = y + 15 + Math.floor(cgIdx / geneCols) * geneRowH;
      var gc = rgb(String(cg.category || ''));
      pdf.setFillColor(gc[0], gc[1], gc[2]);
      pdf.circle(gx + 1.5, gy - 1.2, 1.3, 'F');
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(6.2);
      pdf.setTextColor(26, 26, 46);
      var geneNameTxt = pdfSafeWinAnsi(String(cg.gene || ''));
      pdf.text(pdf.splitTextToSize(geneNameTxt, geneColW - 6)[0] || '', gx + 4, gy);
      pdf.setFont('helvetica', 'normal');
      pdf.setFontSize(5.4);
      pdf.setTextColor(75, 85, 99);
      var traitTxt = pdfSafeWinAnsi(String(cg.category_detail || ''));
      pdf.text(pdf.splitTextToSize(traitTxt, geneColW - 6)[0] || '', gx + 4, gy + 3);
    }
    y += geneCardH + 5;
  }

  async function renderShareFooterPage(pdf, layout) {
    var m = layout.margin;
    var pageW = layout.pageW;
    var pageH = layout.pageH;
    var w = pageW - m * 2;

    var urlText = pdfSafeWinAnsi(reportPdfTargetUrl());
    var qrUrl = await qrDataUrlForShare(urlText);

    pdf.setFillColor(248, 249, 250);
    pdf.rect(0, 0, pageW, pageH, 'F');

    var y = m;
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8);
    pdf.setTextColor(124, 58, 237);
    pdf.text(pdfSafeWinAnsi('MATERIALIZED ENHANCEMENTS'), m, y + 4);
    pdf.setFontSize(18);
    pdf.setTextColor(26, 26, 46);
    pdf.text(pdfSafeWinAnsi('Open this character'), m, y + 15);
    y += 24;

    pdf.setDrawColor(212, 197, 249);
    pdf.line(m, y, pageW - m, y);
    y += 8;

    var qrSize = 50;
    if (qrUrl) {
      try {
        var qrX = (pageW - qrSize) / 2;
        pdf.addImage(qrUrl, 'PNG', qrX, y, qrSize, qrSize);
        y += qrSize + 8;
      } catch (_e5) {
        y += 4;
      }
    }

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(9);
    pdf.setTextColor(55, 65, 81);
    pdf.text(pdfSafeWinAnsi('Scan the QR code or visit the link below to open this character:'), m, y);
    y += 8;

    pdf.setFont('courier', 'normal');
    pdf.setFontSize(7.5);
    pdf.setTextColor(124, 58, 237);
    var urlLines = pdf.splitTextToSize(urlText || pdfSafeWinAnsi('Create a public link from the app to publish this report.'), w);
    pdf.text(urlLines, m, y);
    y += urlLines.length * 4 + 12;

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(7);
    pdf.setTextColor(107, 114, 128);
    pdf.text(pdfSafeWinAnsi('materialized-enhancements  \u00b7  GlucoseDAO  \u00b7  Longevity Genie'), pageW - m - 70, pageH - 7);
  }

  function renderModelViewsPage(pdf, layout) {
    var m = layout.margin;
    var pageW = layout.pageW;
    var pageH = layout.pageH;
    var w = pageW - m * 2;
    var v = window.__reportViews;
    if (!v || (!v.front && !v.side && !v.back)) return false;

    pdf.setFillColor(248, 249, 250);
    pdf.rect(0, 0, pageW, pageH, 'F');

    var y = m;
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8);
    pdf.setTextColor(124, 58, 237);
    pdf.text(pdfSafeWinAnsi('MATERIALIZED ENHANCEMENTS'), m, y + 4);
    pdf.setFontSize(18);
    pdf.setTextColor(26, 26, 46);
    pdf.text(pdfSafeWinAnsi('Printable 3D model'), m, y + 15);
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8.5);
    pdf.setTextColor(107, 114, 128);
    pdf.text(pdfSafeWinAnsi('Three views of the parametric sculpture shaped by your gene selection.'), m, y + 22);
    y += 30;

    var viewW = (w - 8) / 3;
    var viewH = viewW * 1.2;
    var labels = ['Front', 'Side', 'Back'];
    var sources = [v.front, v.side, v.back];
    for (var vi = 0; vi < 3; vi++) {
      var vx = m + vi * (viewW + 4);
      pdf.setDrawColor(229, 231, 235);
      pdf.setFillColor(255, 255, 255);
      pdf.setLineWidth(0.25);
      if (pdf.roundedRect) pdf.roundedRect(vx, y, viewW, viewH + 12, 3, 3, 'FD');
      else pdf.rect(vx, y, viewW, viewH + 12, 'FD');

      if (sources[vi]) {
        try {
          pdf.addImage(sources[vi], 'PNG', vx + 2, y + 2, viewW - 4, viewH - 4, undefined, 'FAST');
        } catch (_ev) {}
      } else {
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(8);
        pdf.setTextColor(156, 163, 175);
        pdf.text('No view', vx + viewW / 2 - 6, y + viewH / 2);
      }

      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(8);
      pdf.setTextColor(26, 26, 46);
      pdf.text(labels[vi], vx + viewW / 2 - pdf.getTextWidth(labels[vi]) / 2, y + viewH + 6);
    }
    y += viewH + 20;

    var name = pdfSafeWinAnsi((document.getElementById('report-share-name') || {}).value || '');
    var points = pdfSafeWinAnsi(String((document.getElementById('report-share-points') || {}).value || ''));
    var catsRaw = String((document.getElementById('report-export-categories') || {}).value || '');
    var cats = catsRaw.split(',').map(function (s) { return s.trim(); }).filter(Boolean);

    pdf.setDrawColor(229, 231, 235);
    pdf.setFillColor(255, 255, 255);
    pdf.setLineWidth(0.25);
    var storyH = 72;
    if (pdf.roundedRect) pdf.roundedRect(m, y, w, storyH, 3, 3, 'FD');
    else pdf.rect(m, y, w, storyH, 'FD');

    var sx = m + 6;
    var sy = y + 8;

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(11);
    pdf.setTextColor(26, 26, 46);
    pdf.text(pdfSafeWinAnsi('How this 3D model was generated'), sx, sy);
    sy += 7;

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8.5);
    pdf.setTextColor(55, 65, 81);
    var storyText = pdfSafeWinAnsi(
      'The app takes the selected genes to procedurally grow a unique mathematical Voronoi shape. ' +
      'Biophysical properties dictate its cellular complexity, seeded by your choices.'
    );
    var storyLines = pdf.splitTextToSize(storyText, w - 12);
    pdf.text(storyLines, sx, sy);
    sy += storyLines.length * 4 + 5;

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(7.5);
    pdf.setTextColor(107, 114, 128);
    pdf.text(pdfSafeWinAnsi('Inputs:'), sx, sy);
    pdf.setFont('helvetica', 'normal');
    pdf.text(pdfSafeWinAnsi(' protein mass, exon count, biological system size, GRAVY score, disorder, pI, name, and categories.'), sx + pdf.getTextWidth('Inputs: '), sy);
    sy += 5;

    pdf.setFont('helvetica', 'bold');
    pdf.setTextColor(124, 58, 237);
    pdf.text(pdfSafeWinAnsi('Outputs:'), sx, sy);
    pdf.setFont('helvetica', 'normal');
    pdf.setTextColor(107, 114, 128);
    pdf.text(pdfSafeWinAnsi(' seed, radius, layer spacing, Voronoi points, surface extrusion, and print-safe scale.'), sx + pdf.getTextWidth('Outputs: '), sy);
    sy += 7;

    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(8);
    pdf.setTextColor(26, 26, 46);
    pdf.text(pdfSafeWinAnsi('Character: ' + (name || '—')), sx, sy);
    pdf.text(pdfSafeWinAnsi('Model points: ' + (points || '—')), sx + 50, sy);
    pdf.text(pdfSafeWinAnsi('Enhancement systems: ' + cats.length), sx + 100, sy);

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(7);
    pdf.setTextColor(107, 114, 128);
    pdf.text(pdfSafeWinAnsi('materialized-enhancements  ·  GlucoseDAO  ·  Longevity Genie'), pageW - m - 70, pageH - 7);
    return true;
  }

  async function buildReportPdf() {
    var pdf = new jspdf.jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4', compress: true });
    var layout = { pageW: 210, pageH: 297, margin: 15 };
    await renderCoverPageA4(pdf, layout);
    if (window.__reportViews && (window.__reportViews.front || window.__reportViews.side || window.__reportViews.back)) {
      pdf.addPage();
      renderModelViewsPage(pdf, layout);
    }
    var rows = readGeneRows();
    if (rows.length) {
      pdf.addPage();
      await renderGenePages(pdf, rows, layout);
    }
    pdf.addPage();
    await renderShareFooterPage(pdf, layout);
    return pdf;
  }

  function clearPdfPreviewObjectUrl() {
    if (window.__mePdfPreviewObjectUrl) {
      URL.revokeObjectURL(window.__mePdfPreviewObjectUrl);
      window.__mePdfPreviewObjectUrl = '';
    }
  }

  function renderPdfFrameInPage(src) {
    var root = document.getElementById('me-report-pdf-viewer');
    if (!root) return false;
    root.innerHTML = '';
    root.setAttribute('data-pdf-rendered', '0');
    var iframe = document.createElement('iframe');
    iframe.title = 'Rendered personal enhancement PDF report';
    iframe.src = src;
    iframe.style.cssText =
      'display:block;width:100%;height:min(78vh,900px);min-height:640px;' +
      'background:#ffffff;border:0;border-radius:6px;box-shadow:0 12px 30px rgba(15,23,42,0.24);';
    root.appendChild(iframe);
    root.setAttribute('data-pdf-rendered', '1');
    return true;
  }

  async function renderPdfArrayBufferInPage(arrayBuffer) {
    clearPdfPreviewObjectUrl();
    var blob = new Blob([arrayBuffer], { type: 'application/pdf' });
    window.__mePdfPreviewObjectUrl = URL.createObjectURL(blob);
    return renderPdfFrameInPage(window.__mePdfPreviewObjectUrl);
  }

  async function renderPdfUrlInPage(url) {
    clearPdfPreviewObjectUrl();
    return renderPdfFrameInPage(url);
  }

  window.__meUsePublishedPdfInPage = async function () {
    var pdfUrl = publishedReportPdfUrl();
    if (!pdfUrl) return false;
    pdfFeedback('Rendering saved PDF...');
    try {
      var rendered = await renderPdfUrlInPage(pdfUrl);
      if (!rendered) {
        pdfFeedback('PDF preview area is not mounted.', '#b91c1c');
        return false;
      }
      pdfFeedback('Showing saved PDF from the generated folder.');
      return true;
    } catch (err) {
      console.error('[materialized] published PDF render failed', err);
      pdfFeedback('Saved PDF render failed: ' + (err && err.message ? err.message : 'see console'), '#b91c1c');
      return false;
    }
  };

  async function waitPdfViewerMounted(timeoutMs) {
    var deadline = Date.now() + (timeoutMs || 6000);
    while (!document.getElementById('me-report-pdf-viewer') && Date.now() < deadline) {
      await new Promise(function (r) { setTimeout(r, 100); });
    }
    if (!document.getElementById('me-report-pdf-viewer')) {
      throw new Error('PDF preview area is not mounted.');
    }
  }

  window.__meRenderActiveReportPdfInPage = async function () {
    try {
      await waitPdfViewerMounted(6000);
      if (window.__meUsePublishedPdfInPage && await window.__meUsePublishedPdfInPage()) return;
      if (window.__meRenderPdfInPage) await window.__meRenderPdfInPage();
    } catch (err) {
      console.error('[materialized] automatic PDF render failed', err);
      pdfFeedback('PDF render failed: ' + (err && err.message ? err.message : 'see console'), '#b91c1c');
    }
  };

  window.__meRenderPdfInPage = async function () {
    if (window.__mePdfRendering) { console.info('[materialized] __meRenderPdfInPage skipped (already rendering)'); return; }
    window.__mePdfRendering = true;
    console.info('[materialized] __meRenderPdfInPage called');
    if (typeof jspdf === 'undefined') {
      window.__mePdfRendering = false;
      pdfFeedback('jsPDF library not loaded. Reload the page.', '#b91c1c');
      missingLib('jsPDF');
      return;
    }
    stopObserver();
    pdfFeedback('Rendering PDF...');
    try {
      await waitReportMounted(6000);
      window.__mePaintReport();
      await new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });
      var pdf = await buildReportPdf();
      var arrayBuffer = pdf.output('arraybuffer');
      if (await renderPdfArrayBufferInPage(arrayBuffer)) {
        pdfFeedback('PDF rendered in this page.');
      } else {
        pdfFeedback('PDF preview area is not mounted.', '#b91c1c');
      }
    } catch (err) {
      console.error('[materialized] inline PDF render failed', err);
      pdfFeedback('PDF render failed: ' + (err && err.message ? err.message : 'see console'), '#b91c1c');
    } finally {
      window.__mePdfRendering = false;
      startObserver();
    }
  };

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

  window.__meBuildReportBundleBase64 = async function (timeoutMs, publishedUrlOverride, slug) {
    timeoutMs = timeoutMs || 8000;
    if (typeof jspdf === 'undefined') {
      return JSON.stringify({ error: 'jsPDF library not loaded.' });
    }
    if (typeof htmlToImage === 'undefined') {
      return JSON.stringify({ error: 'html-to-image library not loaded.' });
    }
    var overallTimeout = timeoutMs + 60000;
    var work = new Promise(async function (resolve) {
      window.__mePendingPublishedReportUrl = canonicalAbsoluteUrl(publishedUrlOverride);
      stopObserver();
      try {
        await waitReportMounted(timeoutMs);
        window.__mePaintReport();
        await new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });
        var pngDataUrl = await buildReportPngDataUrl();
        var pdf = await buildReportPdf();
        var pdfDataUri = pdf.output('datauristring');
        var pngB64 = dataUrlBase64(pngDataUrl, 'WebP');
        var pdfB64 = dataUrlBase64(pdfDataUri, 'PDF');
        var portraitB64 = '';
        var portraitEl = document.getElementById('report-userpic-data-url');
        if (portraitEl && portraitEl.value) {
          var pv = portraitEl.value;
          portraitB64 = pv.indexOf(',') >= 0 ? pv.split(',')[1] : pv;
        }
        if (slug) {
          var uploadBody = { slug: slug, png_base64: pngB64, pdf_base64: pdfB64 };
          if (portraitB64) uploadBody.portrait_base64 = portraitB64;
          var apiUrl = (window.location.port === '3000')
            ? window.location.protocol + '//' + window.location.hostname + ':8000/_api/upload-report-assets'
            : '/_api/upload-report-assets';
          var resp = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(uploadBody),
          });
          var respData = await resp.json();
          if (!resp.ok || respData.error) {
            resolve(JSON.stringify({ error: respData.error || ('Upload failed: HTTP ' + resp.status) }));
            return;
          }
          resolve(JSON.stringify({
            status: 'uploaded',
            slug: slug,
            share_url: reportTargetUrl(),
          }));
        } else {
          resolve(JSON.stringify({
            png_base64: pngB64,
            pdf_base64: pdfB64,
            share_url: reportTargetUrl(),
          }));
        }
      } catch (err) {
        console.error('[materialized] __meBuildReportBundleBase64 failed', err);
        resolve(JSON.stringify({ error: (err && err.message) ? err.message : String(err) }));
      } finally {
        if (!publishedReportUrl()) window.__mePendingPublishedReportUrl = '';
        startObserver();
      }
    });
    var deadline = new Promise(function (resolve) {
      setTimeout(function () {
        resolve(JSON.stringify({ error: 'Report generation timed out after ' + Math.round(overallTimeout / 1000) + 's.' }));
      }, overallTimeout);
    });
    return Promise.race([work, deadline]);
  };

  window.__meCopyShareLink = async function () {
    var url = reportTargetUrl();
    if (!url) {
      feedback('No share link available yet.', '#b45309');
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
      feedback('No share link available yet.', '#b45309');
      return;
    }
    var url = encodeURIComponent(rawUrl);
    var text = encodeURIComponent('My Materialized Enhancements personal enhancement report');
    var target = '';
    if (network === 'twitter')       target = 'https://twitter.com/intent/tweet?text=' + text + '&url=' + url;
    else if (network === 'facebook') target = 'https://www.facebook.com/sharer/sharer.php?u=' + url;
    else if (network === 'linkedin') target = 'https://www.linkedin.com/sharing/share-offsite/?url=' + url;
    else if (network === 'whatsapp') target = 'https://api.whatsapp.com/send?text=' + text + '%20' + url;
    else if (network === 'telegram') target = 'https://t.me/share/url?url=' + url + '&text=' + text;
    if (target) window.open(target, '_blank', 'noopener,noreferrer,width=640,height=520');
  };

  console.info('[materialized] Share & Report helpers booted');
})();
