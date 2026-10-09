/* =========================================================
   AI Business Assistant — Register page interactions
   ========================================================= */
(function () {
  "use strict";

  /* ---------------------------------------------------------
     1. Password show / hide toggle
     Shared helper wired up to both the Password and
     Confirm Password fields.
  --------------------------------------------------------- */
  function wireToggle(buttonId, inputId) {
    const btn = document.getElementById(buttonId);
    const input = document.getElementById(inputId);
    if (!btn || !input) return;

    const icon = btn.querySelector("i");

    btn.addEventListener("click", function () {
      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";

      if (icon) {
        icon.classList.toggle("bi-eye-fill", isHidden);
        icon.classList.toggle("bi-eye-slash-fill", !isHidden);
      }

      btn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
      btn.setAttribute("aria-pressed", String(isHidden));
    });
  }

  wireToggle("togglePassword", "password");
  wireToggle("toggleConfirmPassword", "confirmPassword");

  /* ---------------------------------------------------------
     2. Password strength meter
     Scored on: length >= 8, uppercase, lowercase, number,
     special character. 0-2 checks = Weak, 3 = Medium, 4-5 = Strong.
  --------------------------------------------------------- */
  const passwordField = document.getElementById("password");
  const strengthBars = document.getElementById("strengthBars");
  const strengthLabel = document.getElementById("strengthLabel");
  const strengthText = document.getElementById("passwordStrengthText");

  function scorePassword(value) {
    let score = 0;
    if (value.length >= 8) score++;
    if (/[A-Z]/.test(value)) score++;
    if (/[a-z]/.test(value)) score++;
    if (/[0-9]/.test(value)) score++;
    if (/[^A-Za-z0-9]/.test(value)) score++;
    return score;
  }

  function updateStrengthMeter() {
    if (!passwordField || !strengthBars || !strengthLabel) return;
    const value = passwordField.value;

    strengthBars.classList.remove("weak", "medium", "strong");
    strengthText.classList.remove("weak", "medium", "strong");

    if (!value) {
      strengthLabel.textContent = "—";
      return;
    }

    const score = scorePassword(value);
    let level;
    if (score <= 2) level = "weak";
    else if (score === 3) level = "medium";
    else level = "strong";

    strengthBars.classList.add(level);
    strengthText.classList.add(level);
    strengthLabel.textContent = level.charAt(0).toUpperCase() + level.slice(1);
  }

  if (passwordField) {
    passwordField.addEventListener("input", updateStrengthMeter);
  }

  /* ---------------------------------------------------------
     3. Client-side validation + loading state
     (Server-side / Flask validation is still authoritative)
  --------------------------------------------------------- */
  const form = document.getElementById("registerForm");
  const registerBtn = document.getElementById("registerBtn");

  function setError(fieldId, errorId, message) {
    const field = document.getElementById(fieldId);
    const errorEl = document.getElementById(errorId);
    if (field) field.classList.add("is-invalid");
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.classList.add("show");
    }
  }

  function clearError(fieldId, errorId) {
    const field = document.getElementById(fieldId);
    const errorEl = document.getElementById(errorId);
    if (field) field.classList.remove("is-invalid");
    if (errorEl) {
      errorEl.textContent = "";
      errorEl.classList.remove("show");
    }
  }

  function isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  if (form && registerBtn) {
    form.addEventListener("submit", function (e) {
      let valid = true;

      const fullName = document.getElementById("fullName");
      const email = document.getElementById("email");
      const password = document.getElementById("password");
      const confirmPassword = document.getElementById("confirmPassword");
      const terms = document.getElementById("terms");

      // Full name required
      if (!fullName.value.trim()) {
        setError("fullName", "fullNameError", "Full name is required.");
        valid = false;
      } else {
        clearError("fullName", "fullNameError");
      }

      // Email required + valid format
      if (!email.value.trim()) {
        setError("email", "emailError", "Email address is required.");
        valid = false;
      } else if (!isValidEmail(email.value.trim())) {
        setError("email", "emailError", "Enter a valid email address.");
        valid = false;
      } else {
        clearError("email", "emailError");
      }

      // Password required
      if (!password.value) {
        setError("password", "passwordError", "Password is required.");
        valid = false;
      } else {
        clearError("password", "passwordError");
      }

      // Confirm password required + must match
      if (!confirmPassword.value) {
        setError("confirmPassword", "confirmPasswordError", "Please confirm your password.");
        valid = false;
      } else if (confirmPassword.value !== password.value) {
        setError("confirmPassword", "confirmPasswordError", "Passwords do not match.");
        valid = false;
      } else {
        clearError("confirmPassword", "confirmPasswordError");
      }

      // Terms checkbox required
      if (!terms.checked) {
        setError("terms", "termsError", "You must agree to the Terms & Conditions to continue.");
        valid = false;
      } else {
        clearError("terms", "termsError");
      }

      if (!valid) {
        e.preventDefault();
        return;
      }

      // Loading state while Flask processes the POST
      registerBtn.disabled = true;
      registerBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span><span>Creating account&hellip;</span>';
    });

    // Clear each field's invalid state as the user corrects it
    form.querySelectorAll(".form-control").forEach((field) => {
      field.addEventListener("input", () => field.classList.remove("is-invalid"));
    });
    const termsField = document.getElementById("terms");
    if (termsField) {
      termsField.addEventListener("change", () => clearError("terms", "termsError"));
    }
  }

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
  const LINK_DISTANCE = 150;

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
