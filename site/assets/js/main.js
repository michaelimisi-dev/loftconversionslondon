// Auto year in footer
(function () {
  var y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();
})();

// Sticky mobile CTA - shows after 300px scroll
(function () {
  var cta = document.getElementById("mobile-cta");
  if (!cta) return;
  var shown = false;
  function onScroll() {
    var should = window.scrollY > 300;
    if (should && !shown) { cta.classList.add("visible"); cta.setAttribute("aria-hidden", "false"); shown = true; }
    else if (!should && shown) { cta.classList.remove("visible"); cta.setAttribute("aria-hidden", "true"); shown = false; }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
})();

// GA4 click events for tel: and mailto:
(function () {
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a");
    if (!a) return;
    var href = a.getAttribute("href") || "";
    if (typeof gtag !== "function") return;
    if (href.indexOf("tel:") === 0) gtag("event", "click_to_call", { phone: href.slice(4) });
    else if (href.indexOf("mailto:") === 0) gtag("event", "click_email");
  });
})();

// Lead form submit -> FormSubmit.co (or any AJAX-compatible endpoint set in form.action)
//
// Skill expectation: forms post to https://formsubmit.co/ajax/{recipient_email}
// FormSubmit response shape: { success: "true", message: "..." } (success is a STRING)
// Reply-to is auto-set from the form's `email` field.
// Honeypot uses FormSubmit's `_honey` field (bots fill it, real users don't).
(function () {
  var forms = document.querySelectorAll('form#lead-form, form.lead-form, form[data-lead-form]');
  forms.forEach(function (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      var btn = form.querySelector('button[type="submit"]');
      var originalText = btn ? btn.textContent : "";
      if (btn) { btn.disabled = true; btn.textContent = "Sending..."; }

      var data = Object.fromEntries(new FormData(form).entries());
      var endpoint = form.getAttribute("action") || "";

      try {
        var res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify(data)
        });
        var result = await res.json();
        var ok = result.success === true || result.success === "true" || result.ok === true;
        if (ok) {
          if (typeof gtag === "function") gtag("event", "generate_lead", { form_id: form.id || "lead" });
          var msg = document.createElement("div");
          msg.className = "lead-form form-success";
          msg.setAttribute("role", "status");
          msg.innerHTML = '<h3 style="margin-bottom: 0.5rem;">Thanks, ' + escapeHtml(data.name || "") + '!</h3><p>We will call you back on ' + escapeHtml(data.phone || "") + ' within one working day to arrange your free survey.</p>';
          form.replaceWith(msg);
        } else {
          showError(form, btn, originalText);
        }
      } catch (err) {
        showError(form, btn, originalText);
      }
    });
  });

  function showError(form, btn, originalText) {
    var existing = form.querySelector(".form-error");
    if (existing) existing.remove();
    var err = document.createElement("p");
    err.className = "form-error";
    err.style.cssText = "color: var(--color-error); margin-bottom: 1rem; font-weight: 600;";
    err.textContent = "Something went wrong. Please email us at info@loftconversionslondon.co.uk instead.";
    form.insertBefore(err, form.firstChild);
    if (btn) { btn.disabled = false; btn.textContent = originalText; }
  }

  function escapeHtml(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
})();
