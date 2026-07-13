(function () {
  'use strict';

  window.LV = window.LV || {};

  function warn(scope, message, err) {
    if (typeof console !== 'undefined' && console.warn) {
      console.warn('[LV wizard:' + scope + ']', message, err || '');
    }
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function readJsonScript(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent || 'null');
    } catch (e) {
      warn('json', 'Falha ao ler json_script #' + id, e);
      return null;
    }
  }

  function parseBirthdateParts(birthdateStr) {
    if (!birthdateStr) return null;
    var y;
    var m;
    var day;
    if (birthdateStr.indexOf('-') !== -1) {
      var isoParts = birthdateStr.split('-');
      if (isoParts.length !== 3) return null;
      y = parseInt(isoParts[0], 10);
      m = parseInt(isoParts[1], 10);
      day = parseInt(isoParts[2], 10);
    } else {
      var brParts = birthdateStr.split('/');
      if (brParts.length !== 3) return null;
      day = parseInt(brParts[0], 10);
      m = parseInt(brParts[1], 10);
      y = parseInt(brParts[2], 10);
    }
    if (!y || !m || !day) return null;
    return { y: y, m: m, day: day };
  }

  function calcAgeYears(birthdateStr) {
    var parts = parseBirthdateParts(birthdateStr);
    if (!parts) return null;
    var d = new Date(parts.y, parts.m - 1, parts.day);
    if (isNaN(d.getTime())) return null;
    var today = new Date();
    var age = today.getFullYear() - d.getFullYear();
    if (
      today.getMonth() < d.getMonth() ||
      (today.getMonth() === d.getMonth() && today.getDate() < d.getDate())
    ) {
      age -= 1;
    }
    return age;
  }

  function resolveAudience(birthdateStr, ibjjfCategories) {
    var categories = ibjjfCategories || [];
    var age = calcAgeYears(birthdateStr);
    if (age === null) return null;
    if (categories.length === 0) {
      return age >= 16 ? 'adult' : (age >= 10 ? 'juvenile' : 'kids');
    }
    var sorted = categories.slice().sort(function (a, b) {
      return a.minimum_age - b.minimum_age;
    });
    for (var i = 0; i < sorted.length; i += 1) {
      var cat = sorted[i];
      var maxOk = cat.maximum_age === null || cat.maximum_age === undefined || age <= cat.maximum_age;
      if (age >= cat.minimum_age && maxOk) return cat.audience;
    }
    return null;
  }

  function formatIsoDateForDisplay(isoStr) {
    if (!isoStr || isoStr.indexOf('-') === -1) return isoStr;
    var parts = isoStr.split('-');
    if (parts.length !== 3) return isoStr;
    return parts[2] + '/' + parts[1] + '/' + parts[0];
  }

  function eligibilityFetchKey(payload) {
    return JSON.stringify(payload);
  }

  function fetchEligibility(opts) {
    var url = opts.url;
    var cache = opts.cache;
    var payload = opts.payload;
    if (!url || !cache) return;
    var key = eligibilityFetchKey(payload);
    if (cache.fetchKey === key && cache.planIds) return;
    if (cache.pending) return;
    cache.pending = true;
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': opts.csrfToken || '',
      },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        cache.pending = false;
        if (data && Array.isArray(data.eligible_plan_ids)) {
          cache.fetchKey = key;
          cache.planIds = data.eligible_plan_ids;
          if (opts.onUpdated) opts.onUpdated();
        }
      })
      .catch(function (err) {
        cache.pending = false;
        warn('eligibility', 'Falha ao consultar elegibilidade de plano', err);
        if (opts.onError) opts.onError(err);
      });
  }

  function getFormEndpoints(formEl) {
    if (!formEl) {
      return { eligibilityUrl: '', validateCouponUrl: '' };
    }
    return {
      eligibilityUrl: formEl.getAttribute('data-eligibility-url') || '',
      validateCouponUrl: formEl.getAttribute('data-validate-coupon-url') || '',
    };
  }

  function setElementText(el, text, className) {
    if (!el) return;
    el.textContent = '';
    var p = document.createElement('p');
    p.className = className || 'plan-cards--empty';
    p.textContent = text;
    el.appendChild(p);
  }

  window.LV.Wizard = {
    warn: warn,
    escapeHtml: escapeHtml,
    readJsonScript: readJsonScript,
    parseBirthdateParts: parseBirthdateParts,
    calcAgeYears: calcAgeYears,
    resolveAudience: resolveAudience,
    formatIsoDateForDisplay: formatIsoDateForDisplay,
    eligibilityFetchKey: eligibilityFetchKey,
    fetchEligibility: fetchEligibility,
    getFormEndpoints: getFormEndpoints,
    setElementText: setElementText,
  };
})();
