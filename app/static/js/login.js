/* =========================================================
   AI Business Assistant — Login page interactions
   ========================================================= */
(function () {
  "use strict";

  /* ---------------------------------------------------------
     1. Password show / hide toggle
  --------------------------------------------------------- */
  const toggleBtn = document.getElementById("togglePassword");
  const passwordInput = document.getElementById("password");
  const toggleIcon = document.getElementById("toggleIcon");

  if (toggleBtn && passwordInput && toggleIcon) {
    toggleBtn.addEventListener("click", function () {
      const isHidden = passwordInput.type === "password";
      passwordInput.type = isHidden ? "text" : "password";

      toggleIcon.classList.toggle("bi-eye-fill", isHidden);
      toggleIcon.classList.toggle("bi-eye-slash-fill", !isHidden);

      toggleBtn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
      toggleBtn.setAttribute("aria-pressed", String(isHidden));
    });
  }

  /* ---------------------------------------------------------
     2. Lightweight client-side validation feedback
     (Server-side / Flask validation still authoritative)
  --------------------------------------------------------- */
  const form = document.querySelector(".auth-form");
  const signInBtn = document.querySelector(".btn-signin");

  if (form && signInBtn) {
    form.addEventListener("submit", function (e) {
      const emailField = form.querySelector("#email");
      const pwField = form.querySelector("#password");
      let valid = true;

      [emailField, pwField].forEach((field) => {
        if (field && !field.value.trim()) {
          valid = false;
          field.classList.add("is-invalid");
        } else if (field) {
          field.classList.remove("is-invalid");
        }
      });

      if (!valid) {
        e.preventDefault();
        return;
      }

      // Small loading state so the button feels responsive while Flask processes the POST
      signInBtn.disabled = true;
      signInBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span><span>Signing in&hellip;</span>';
    });

    // Clear invalid state as the user types
    form.querySelectorAll(".form-control").forEach((field) => {
      field.addEventListener("input", () => field.classList.remove("is-invalid"));
    });
  }

  /* ---------------------------------------------------------
     3. OAuth button placeholders
     Swap this handler out once real provider routes exist.
  --------------------------------------------------------- 
  document.querySelectorAll(".oauth-btn").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      if (btn.getAttribute("href") === "#") {
        e.preventDefault();
        const provider = btn.dataset.provider || "provider";
        console.info(`[AI Business Assistant] OAuth with ${provider} not yet wired up.`);
      }
    });
  });
   */
  /* ---------------------------------------------------------
     4. Ambient neural-network canvas
     Nodes drift slowly and draw connecting lines when close —
     a quiet nod to the product's AI core rather than generic confetti.
  --------------------------------------------------------- */
  const canvas = document.getElementById("network-canvas");
  if (!canvas || !canvas.getContext) return;

  const ctx = canvas.getContext("2d");
  let nodes = [];
  let width, height;
  let animationId;
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const NODE_COLORS = ["rgba(6,182,212,0.9)", "rgba(37,99,235,0.9)", "rgba(124,58,237,0.9)"];
  const LINK_DISTANCE =
  window.innerWidth < 768 ? 90 : 130;

  function resize() {
    width = canvas.width = canvas.offsetWidth;
    height = canvas.height = canvas.offsetHeight;
  }

  function nodeCount() {
    const area = width * height;
    return Math.max(24, Math.min(70, Math.round(area / 22000)));
  }

  function initNodes() {
    const count = nodeCount();
    nodes = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      r: Math.random() * 1.6 + 1,
      color: NODE_COLORS[Math.floor(Math.random() * NODE_COLORS.length)],
    }));
  }

  function step() {
    ctx.clearRect(0, 0, width, height);

    // Update + draw nodes
    for (const n of nodes) {
      n.x += n.vx;
      n.y += n.vy;

      if (n.x < 0 || n.x > width) n.vx *= -1;
      if (n.y < 0 || n.y > height) n.vy *= -1;

      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = n.color;
      ctx.fill();
    }

    // Draw connecting lines between nearby nodes
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < LINK_DISTANCE) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `rgba(148, 163, 184, ${0.18 * (1 - dist / LINK_DISTANCE)})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }

    animationId = requestAnimationFrame(step);
  }

  function start() {
    resize();
    initNodes();
    if (!prefersReducedMotion) {
      cancelAnimationFrame(animationId);
      step();
    } else {
      // Draw a single static frame for reduced-motion users
      step();
      cancelAnimationFrame(animationId);
    }
  }

  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(start, 200);
  });

  start();
})();
