/* Material keeps both palette labels hidden until its bundle runs.
   Under file:// that bundle often never finishes, so the toggle stays
   invisible and clicks do nothing. This script owns the switch. */
(function () {
  var KEY = "cesdm-docs-palette-index";

  function inputsIn(form) {
    return Array.prototype.slice.call(
      form.querySelectorAll('input[name="__palette"]')
    );
  }

  function apply(inputs, index, persist) {
    var input = inputs[index];
    if (!input) return;
    input.checked = true;
    document.body.setAttribute(
      "data-md-color-scheme",
      input.getAttribute("data-md-color-scheme") || "default"
    );
    inputs.forEach(function (el, i) {
      var label = el.nextElementSibling;
      if (label && label.tagName === "LABEL") {
        if (i === index) label.removeAttribute("hidden");
        else label.setAttribute("hidden", "");
      }
    });
    if (persist) {
      try {
        localStorage.setItem(KEY, String(index));
      } catch (err) {}
    }
  }

  function readIndex(inputs) {
    try {
      var saved = localStorage.getItem(KEY);
      if (saved !== null) {
        var parsed = parseInt(saved, 10);
        if (parsed >= 0 && parsed < inputs.length) return parsed;
      }
    } catch (err) {}
    return document.body.getAttribute("data-md-color-scheme") === "slate" ? 1 : 0;
  }

  function init() {
    var form = document.querySelector("[data-cesdm-palette]");
    if (!form) return;
    var inputs = inputsIn(form);
    if (!inputs.length) return;

    inputs.forEach(function (input, index) {
      input.addEventListener("change", function () {
        if (input.checked) apply(inputs, index, true);
      });
    });
    apply(inputs, readIndex(inputs), false);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
