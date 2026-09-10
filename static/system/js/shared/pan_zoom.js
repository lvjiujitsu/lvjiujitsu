(function () {
  "use strict";

  window.APP = window.APP || {};

  const DRAG_THRESHOLD = 11;

  function init(options) {
    const opts = options || {};
    const viewport = opts.viewport;
    const stage = opts.stage;
    if (!viewport || !stage) return null;

    const minScale = typeof opts.minScale === "number" ? opts.minScale : 0.25;
    const maxScale = typeof opts.maxScale === "number" ? opts.maxScale : 2.4;
    const zoomInBtn = opts.zoomInBtn || null;
    const zoomOutBtn = opts.zoomOutBtn || null;
    const fitBtn = opts.fitBtn || null;
    const scaleProperty = opts.scaleProperty || "--pan-zoom-scale-inverse";
    const compactWidth = typeof opts.compactWidth === "number" ? opts.compactWidth : 700;

    const state = { x: 0, y: 0, scale: 1, fitScale: 1 };
    let viewMode = "explore";
    let pointerState = null;
    let suppressClickUntil = 0;

    function clampAxis(position, viewportSize, scaledContentSize) {
      const viewportCenter = viewportSize / 2;
      return Math.min(
        viewportCenter,
        Math.max(viewportCenter - scaledContentSize, position)
      );
    }

    function clampPosition() {
      const viewWidth = viewport.clientWidth;
      const viewHeight = viewport.clientHeight;
      const scaledWidth = stage.offsetWidth * state.scale;
      const scaledHeight = stage.offsetHeight * state.scale;
      state.x = clampAxis(state.x, viewWidth, scaledWidth);
      state.y = clampAxis(state.y, viewHeight, scaledHeight);
    }

    function renderTransform() {
      clampPosition();
      stage.style.setProperty(scaleProperty, String(1 / state.scale));
      stage.style.transform = `translate3d(${state.x}px, ${state.y}px, 0) scale(${state.scale})`;
    }

    function calculateFitScale() {
      const padding = viewport.clientWidth < compactWidth ? 16 : 34;
      state.fitScale = Math.min(
        (viewport.clientWidth - padding * 2) / stage.offsetWidth,
        (viewport.clientHeight - padding * 2) / stage.offsetHeight,
        maxScale
      );
      return state.fitScale;
    }

    function calculateExploreScale() {
      const compact = viewport.clientWidth < compactWidth;
      const fitScale = calculateFitScale();
      const widthFill = (viewport.clientWidth * (compact ? 0.86 : 0.64)) / stage.offsetWidth;
      const boostedFit = fitScale * (compact ? 1.75 : 1.35);
      return Math.max(compact ? 0.82 : 1.08, widthFill, boostedFit);
    }

    function setViewMode(mode) {
      viewMode = mode;
      viewport.dataset.viewMode = mode;
      if (fitBtn) fitBtn.setAttribute("aria-pressed", String(mode === "fit"));
    }

    function centerStage(scale) {
      state.scale = Math.max(minScale, Math.min(maxScale, scale));
      state.x = (viewport.clientWidth - stage.offsetWidth * state.scale) / 2;
      state.y = (viewport.clientHeight - stage.offsetHeight * state.scale) / 2;
      renderTransform();
    }

    function explore() {
      setViewMode("explore");
      centerStage(calculateExploreScale());
    }

    function fit() {
      setViewMode("fit");
      centerStage(calculateFitScale());
    }

    function zoomTo(nextScale, originX, originY) {
      if (originX === undefined) originX = viewport.clientWidth / 2;
      if (originY === undefined) originY = viewport.clientHeight / 2;
      setViewMode("manual");
      const previousScale = state.scale;
      const bounded = Math.max(minScale, Math.min(maxScale, nextScale));
      const localX = (originX - state.x) / previousScale;
      const localY = (originY - state.y) / previousScale;
      state.scale = bounded;
      state.x = originX - localX * bounded;
      state.y = originY - localY * bounded;
      renderTransform();
    }

    function focusPoint(localX, localY, nextScale) {
      setViewMode("manual");
      if (typeof nextScale === "number") {
        state.scale = Math.max(minScale, Math.min(maxScale, nextScale));
      }
      state.x = viewport.clientWidth / 2 - localX * state.scale;
      state.y = viewport.clientHeight / 2 - localY * state.scale;
      renderTransform();
    }

    viewport.addEventListener("pointerdown", (event) => {
      if (event.button !== 0) return;
      pointerState = {
        id: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        originX: state.x,
        originY: state.y,
        moved: false,
      };
    });

    viewport.addEventListener("pointermove", (event) => {
      if (!pointerState || pointerState.id !== event.pointerId) return;
      const deltaX = event.clientX - pointerState.startX;
      const deltaY = event.clientY - pointerState.startY;
      if (Math.hypot(deltaX, deltaY) > DRAG_THRESHOLD) {
        pointerState.moved = true;
        setViewMode("manual");
        if (!viewport.hasPointerCapture(event.pointerId)) {
          viewport.setPointerCapture(event.pointerId);
        }
        viewport.classList.add("is-dragging");
      }
      if (!pointerState.moved) return;
      state.x = pointerState.originX + deltaX;
      state.y = pointerState.originY + deltaY;
      renderTransform();
    });

    function finishPointer(event) {
      if (!pointerState || pointerState.id !== event.pointerId) return;
      if (pointerState.moved) suppressClickUntil = Date.now() + 240;
      viewport.classList.remove("is-dragging");
      pointerState = null;
    }

    viewport.addEventListener("pointerup", finishPointer);
    viewport.addEventListener("pointercancel", finishPointer);
    viewport.addEventListener(
      "wheel",
      (event) => {
        event.preventDefault();
        const rect = viewport.getBoundingClientRect();
        zoomTo(
          state.scale * (event.deltaY < 0 ? 1.12 : 0.89),
          event.clientX - rect.left,
          event.clientY - rect.top
        );
      },
      { passive: false }
    );

    if (zoomInBtn) zoomInBtn.addEventListener("click", () => zoomTo(state.scale * 1.2));
    if (zoomOutBtn) zoomOutBtn.addEventListener("click", () => zoomTo(state.scale / 1.2));
    if (fitBtn) fitBtn.addEventListener("click", fit);

    function onResize() {
      if (!viewport.isConnected) {
        window.removeEventListener("resize", onResize);
        return;
      }
      if (viewMode === "fit") fit();
      else if (viewMode === "explore") explore();
      else renderTransform();
    }
    window.addEventListener("resize", onResize);

    explore();

    return {
      state,
      explore,
      fit,
      zoomTo,
      focusPoint,
      exploreScale: calculateExploreScale,
      wasRecentlyDragging: () => Date.now() < suppressClickUntil,
      destroy: () => window.removeEventListener("resize", onResize),
    };
  }

  window.APP.PanZoom = { init };
})();
