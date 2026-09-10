(function () {
  'use strict';

  window.APP = window.APP || {};

  var CHANNEL = 'app.frame';
  var handlers = {};
  var listening = false;

  function origin() {
    return window.location.origin;
  }

  function isEnvelope(data) {
    return Boolean(data) && typeof data === 'object' && data.channel === CHANNEL && typeof data.type === 'string';
  }

  function deliver(type, payload, event) {
    var list = handlers[type];
    if (!list || !list.length) return;
    list.slice().forEach(function (handler) {
      try {
        handler(payload, event);
      } catch (error) {
        return;
      }
    });
  }

  function onMessage(event) {
    if (event.origin !== origin()) return;
    if (!isEnvelope(event.data)) return;
    deliver(event.data.type, event.data.payload, event);
    deliver('*', { type: event.data.type, payload: event.data.payload }, event);
  }

  function listen() {
    if (listening) return;
    listening = true;
    window.addEventListener('message', onMessage);
  }

  function envelope(type, payload) {
    return { channel: CHANNEL, type: type, payload: payload === undefined ? null : payload };
  }

  function postTo(target, type, payload) {
    if (!target || target === window) return false;
    try {
      target.postMessage(envelope(type, payload), origin());
      return true;
    } catch (error) {
      return false;
    }
  }

  function post(type, payload) {
    if (!type) return false;
    return postTo(window.parent, type, payload);
  }

  function postToFrame(frame, type, payload) {
    if (!frame) return false;
    var target = frame.contentWindow || frame;
    return postTo(target, type, payload);
  }

  function broadcast(type, payload) {
    var sent = false;
    document.querySelectorAll('iframe').forEach(function (frame) {
      if (postToFrame(frame, type, payload)) sent = true;
    });
    return sent;
  }

  function on(type, handler) {
    if (!type || typeof handler !== 'function') return function () {};
    listen();
    handlers[type] = handlers[type] || [];
    handlers[type].push(handler);
    return function off() {
      var list = handlers[type];
      if (!list) return;
      var index = list.indexOf(handler);
      if (index >= 0) list.splice(index, 1);
    };
  }

  function isChild() {
    return Boolean(window.parent) && window.parent !== window;
  }

  window.APP.FrameBridge = {
    channel: CHANNEL,
    post: post,
    postToFrame: postToFrame,
    broadcast: broadcast,
    on: on,
    isChild: isChild
  };
})();
