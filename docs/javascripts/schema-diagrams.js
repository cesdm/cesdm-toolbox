/* Schema diagrams (docs/reference/schema-diagrams/).
 *
 * The generated pages contain ```cesdm-uml fences with Mermaid classDiagram code.
 * Material's built-in Mermaid support shrinks every diagram to the column width,
 * which makes a 40-class diagram unreadable. This script renders those fences
 * itself: at natural size, in a scrollable frame, with zoom buttons, in the
 * current light or dark palette. Mermaid is loaded only on pages that need it.
 */
(function () {
  "use strict";

  var MERMAID_URL = "https://unpkg.com/mermaid@11.4.1/dist/mermaid.min.js";
  var loading = null;
  var counter = 0;

  function loadMermaid() {
    if (window.mermaid) return Promise.resolve(window.mermaid);
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var script = document.createElement("script");
      script.src = MERMAID_URL;
      script.onload = function () { resolve(window.mermaid); };
      script.onerror = reject;
      document.head.appendChild(script);
    });
    return loading;
  }

  function isDark() {
    var scheme = document.body.getAttribute("data-md-color-scheme");
    return scheme === "slate";
  }

  function setScale(frame, scale) {
    var svg = frame.querySelector("svg");
    if (!svg) return;
    var natural = parseFloat(svg.dataset.naturalWidth);
    if (scale === "fit") {
      scale = Math.min(1, (frame.clientWidth - 16) / natural);
    } else if (scale === "start") {
      // Overview first, but never so small that class names become unreadable.
      scale = Math.max(0.5, Math.min(1, (frame.clientWidth - 16) / natural));
    }
    frame.dataset.scale = scale;
    svg.style.width = Math.round(natural * scale) + "px";
    svg.style.height = "auto";
    frame.querySelector(".schema-diagram__level").textContent = Math.round(scale * 100) + " %";
  }

  function toolbar(frame) {
    var bar = document.createElement("div");
    bar.className = "schema-diagram__toolbar";
    var buttons = [
      ["−", "Zoom out", function () { setScale(frame, Math.max(0.2, frame.dataset.scale / 1.25)); }],
      ["+", "Zoom in", function () { setScale(frame, Math.min(3, frame.dataset.scale * 1.25)); }],
      ["Fit", "Fit to width", function () { setScale(frame, "fit"); }],
      ["100 %", "Actual size", function () { setScale(frame, 1); }]
    ];
    buttons.forEach(function (b) {
      var button = document.createElement("button");
      button.type = "button";
      button.textContent = b[0];
      button.title = b[1];
      button.addEventListener("click", b[2]);
      bar.appendChild(button);
    });
    var level = document.createElement("span");
    level.className = "schema-diagram__level";
    bar.appendChild(level);
    return bar;
  }

  // Drag with the mouse to move around a large diagram (links still work on click).
  function enablePan(canvas) {
    var start = null;
    canvas.addEventListener("mousedown", function (event) {
      if (event.button !== 0 || event.target.closest("a")) return;
      start = { x: event.clientX, y: event.clientY, left: canvas.scrollLeft, top: canvas.scrollTop };
      canvas.classList.add("is-panning");
      event.preventDefault();
    });
    window.addEventListener("mousemove", function (event) {
      if (!start) return;
      canvas.scrollLeft = start.left - (event.clientX - start.x);
      canvas.scrollTop = start.top - (event.clientY - start.y);
    });
    window.addEventListener("mouseup", function () {
      start = null;
      canvas.classList.remove("is-panning");
    });
  }

  async function renderAll() {
    var blocks = document.querySelectorAll("pre.cesdm-uml, div.schema-diagram[data-source]");
    if (!blocks.length) return;
    var mermaid = await loadMermaid();
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      maxTextSize: 500000,
      theme: isDark() ? "dark" : "default",
      class: { useMaxWidth: false }
    });

    for (var i = 0; i < blocks.length; i++) {
      var block = blocks[i];
      var source = block.dataset.source || block.textContent;
      var wrapper = block;
      if (block.tagName === "PRE") {
        wrapper = document.createElement("div");
        wrapper.className = "schema-diagram";
        wrapper.dataset.source = source;
        block.replaceWith(wrapper);
      }
      var keep = wrapper.dataset.scale;
      wrapper.innerHTML = "";
      wrapper.appendChild(toolbar(wrapper));
      var canvas = document.createElement("div");
      canvas.className = "schema-diagram__canvas";
      wrapper.appendChild(canvas);
      try {
        var result = await mermaid.render("cesdm-uml-" + (counter++), source);
        canvas.innerHTML = result.svg;
        var svg = canvas.querySelector("svg");
        var box = svg.viewBox && svg.viewBox.baseVal;
        svg.dataset.naturalWidth = box && box.width ? box.width : svg.getBoundingClientRect().width;
        svg.style.maxWidth = "none";
        if (result.bindFunctions) result.bindFunctions(canvas);
        setScale(wrapper, keep ? parseFloat(keep) : "start");
        enablePan(canvas);
      } catch (error) {
        canvas.textContent = "Diagram could not be rendered: " + error.message;
      }
    }
  }

  // One render at a time: page load and palette switches can arrive together.
  var queue = Promise.resolve();
  function schedule() { queue = queue.then(renderAll, renderAll); }

  // Re-render when the reader switches between light and dark palette.
  new MutationObserver(schedule)
    .observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });

  if (window.document$ && window.document$.subscribe) {
    window.document$.subscribe(schedule);           // Material: runs on every page load
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", schedule);
  } else {
    schedule();
  }
})();
