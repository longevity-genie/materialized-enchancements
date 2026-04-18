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
  function absoluteShareUrl() {
    var p = sharePath();
    if (!p) return window.location.origin + '/';
    return window.location.origin + '/' + (p.charAt(0) === '?' ? '' : '') + p;
  }
  function safeName() {
    var raw = (document.getElementById('report-share-name') || {}).value || 'anon';
    return raw.replace(/[^a-zA-Z0-9_-]+/g, '_').slice(0, 40) || 'anon';
  }
  function safeSeed() {
    return (document.getElementById('report-share-seed') || {}).value || '0';
  }

  /* ---------------------------------------------------------- painters */

  function paintShareUrl() {
    var urlEl = document.getElementById('report-share-url');
    if (urlEl) urlEl.textContent = absoluteShareUrl();
  }

  function renderQrInto(el) {
    if (!el || typeof qrcode === 'undefined') return false;
    try {
      var qr = qrcode(0, 'M');
      qr.addData(absoluteShareUrl());
      qr.make();
      el.innerHTML = qr.createImgTag(4, 0);
      var img = el.querySelector('img');
      if (img) {
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.display = 'block';
      }
      return true;
    } catch (_e) { return false; }
  }
  function paintQr() {
    var ok1 = renderQrInto(document.getElementById('report-qr'));
    var ok2 = renderQrInto(document.getElementById('report-qr-png'));
    return ok1 || ok2;
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
    var url = absoluteShareUrl();
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
          // Ignore our own DOM writes so we don't feedback-loop.
          if (n.id === 'report-qr' || n.id === 'report-qr-png' ||
              n.id === 'me-report-pdf-long' || n.id === 'me-report-png-card') return;
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
    if (text) setTimeout(function () { fb.textContent = ''; }, 2500);
  }

  function missingLib(name) {
    console.warn('[materialized] skipping action: ' + name + ' is not loaded yet');
    feedback(name + ' not loaded — reload the page.', '#b91c1c');
  }

  async function captureSquareAt(node, targetPx) {
    // html-to-image measures the node's box; we force exact pixel size so the
    // output is a true 1080x1080 image without extra padding.
    var width = node.offsetWidth || targetPx;
    var height = node.offsetHeight || targetPx;
    var ratio = targetPx / Math.max(width, height);
    return htmlToImage.toPng(node, {
      pixelRatio: ratio,
      backgroundColor: '#ffffff',
      width: width,
      height: height,
      canvasWidth: targetPx,
      canvasHeight: targetPx,
      cacheBust: true,
      skipFonts: false,
    });
  }

  async function withExportMode(fn) {
    // Pause the mutation observer during rasterization so html-to-image's
    // internal DOM churn doesn't fire observer → repaint → DOM churn cycles
    // that slow down export.
    stopObserver();
    feedback('Rendering\u2026');
    try {
      window.__mePaintReport();
      // Wait one frame so the browser paints QR/views before html-to-image reads the DOM.
      await new Promise(function (r) { requestAnimationFrame(r); });
      await fn();
    } catch (err) {
      console.error('[materialized] export failed', err);
      feedback('Export failed — see console.', '#b91c1c');
    } finally {
      startObserver();
      feedback('');
    }
  }

  /* --------------------------------------------- button action handlers */

  window.__meDownloadPng = function () {
    if (typeof htmlToImage === 'undefined') { missingLib('html-to-image'); return; }
    var node = document.getElementById('me-report-png-card');
    if (!node) { console.warn('[materialized] png card not mounted'); return; }
    withExportMode(async function () {
      var dataUrl = await captureSquareAt(node, 1080);
      downloadDataUrl(dataUrl, 'materialized_' + safeName() + '_s' + safeSeed() + '.png');
      feedback('PNG saved!');
    });
  };

  window.__meDownloadPdf = function () {
    if (typeof htmlToImage === 'undefined') { missingLib('html-to-image'); return; }
    if (typeof jspdf === 'undefined')       { missingLib('jsPDF');         return; }
    var mainNode = document.getElementById('me-report-card');
    if (!mainNode) return;
    withExportMode(async function () {
      // Page 1: full identity card (tall, not square) at its natural size
      var mainUrl = await htmlToImage.toPng(mainNode, {
        pixelRatio: 2,
        backgroundColor: '#ffffff',
        cacheBust: true,
      });
      var pdf = new jspdf.jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      var pageW = 210, pageH = 297, margin = 15;

      var im1 = new Image();
      im1.src = mainUrl;
      await new Promise(function (r) { im1.onload = r; });
      var ratio1 = im1.height / im1.width;
      var w1 = pageW - margin * 2;
      var h1 = w1 * ratio1;
      if (h1 > pageH - margin * 2) { h1 = pageH - margin * 2; w1 = h1 / ratio1; }
      pdf.addImage(mainUrl, 'PNG', (pageW - w1) / 2, margin, w1, h1);

      var outName = 'materialized_' + safeName() + '_s' + safeSeed() + '.pdf';

      // Subsequent pages: long gene descriptions
      var longDoc = document.getElementById('me-report-pdf-long');
      if (longDoc) {
        var saved = longDoc.style.cssText;
        longDoc.style.cssText = saved + ';left:0;top:0;position:fixed;z-index:-1;opacity:0.01;';
        var longUrl = await htmlToImage.toPng(longDoc, {
          pixelRatio: 2,
          backgroundColor: '#ffffff',
          cacheBust: true,
        });
        longDoc.style.cssText = saved;
        var im2 = new Image();
        im2.src = longUrl;
        await new Promise(function (r) { im2.onload = r; });
        var ratio2 = im2.height / im2.width;
        var w2 = pageW - margin * 2;
        var h2 = w2 * ratio2;
        var bodyH = pageH - margin * 2;
        var drawn = 0;
        while (drawn < h2) {
          pdf.addPage();
          pdf.addImage(longUrl, 'PNG', margin, margin - drawn, w2, h2);
          drawn += bodyH;
        }
      }
      pdf.save(outName);
      feedback('PDF saved!');
    });
  };

  window.__meCopyShareLink = async function () {
    var url = absoluteShareUrl();
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
    var url = encodeURIComponent(absoluteShareUrl());
    var text = encodeURIComponent('My Materialized Enhancements identity report');
    var target = '';
    if (network === 'twitter')       target = 'https://twitter.com/intent/tweet?text=' + text + '&url=' + url;
    else if (network === 'facebook') target = 'https://www.facebook.com/sharer/sharer.php?u=' + url;
    else if (network === 'linkedin') target = 'https://www.linkedin.com/sharing/share-offsite/?url=' + url;
    if (target) window.open(target, '_blank', 'noopener,noreferrer,width=640,height=520');
  };

  console.info('[materialized] Share & Report helpers booted');
})();
