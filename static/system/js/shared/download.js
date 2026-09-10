(function () {
  'use strict';

  window.APP = window.APP || {};

  function supported() {
    return Boolean(window.fetch && window.URL && window.URL.createObjectURL);
  }

  function fileNameFrom(response, fallback) {
    var disposition = response.headers.get('Content-Disposition') || '';
    var match = disposition.match(/filename="?([^";]+)"?/);
    return match ? match[1] : fallback;
  }

  function save(blob, name) {
    var address = window.URL.createObjectURL(blob);
    var anchor = document.createElement('a');
    anchor.href = address;
    anchor.download = name;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(function () {
      window.URL.revokeObjectURL(address);
    }, 30000);
  }

  function fromUrl(url, options) {
    var opts = options || {};
    if (!url) return Promise.resolve(false);
    if (!supported()) return Promise.resolve(false);
    if (opts.onStart) opts.onStart();

    return window
      .fetch(url, { credentials: 'same-origin' })
      .then(function (response) {
        if (!response.ok) throw new Error(String(response.status));
        return response.blob().then(function (blob) {
          return { blob: blob, response: response };
        });
      })
      .then(function (result) {
        save(result.blob, fileNameFrom(result.response, opts.fallbackName || 'download'));
        if (opts.onSuccess) opts.onSuccess();
        return true;
      })
      .catch(function (error) {
        if (opts.onError) opts.onError(error);
        return false;
      });
  }

  window.APP.download = {
    supported: supported,
    fromUrl: fromUrl,
    save: save,
    fileNameFrom: fileNameFrom
  };
})();
