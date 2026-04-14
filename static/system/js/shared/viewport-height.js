(function () {
  var root = document.documentElement;

  function setViewportHeight() {
    var viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    if (!viewportHeight || viewportHeight < 100) {
      viewportHeight = window.innerHeight;
    }
    root.style.setProperty("--app-height", viewportHeight + "px");
  }

  setViewportHeight();

  window.addEventListener("resize", setViewportHeight, { passive: true });
  window.addEventListener("orientationchange", setViewportHeight, { passive: true });
  window.addEventListener("pageshow", setViewportHeight);

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", setViewportHeight, { passive: true });
    window.visualViewport.addEventListener("scroll", setViewportHeight, { passive: true });
  }
})();
