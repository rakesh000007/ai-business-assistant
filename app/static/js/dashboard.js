/* ==========================================================
   AI Business Assistant — Dashboard v2 interactions
   ========================================================== */
document.addEventListener("DOMContentLoaded", () => {

  /* ---------- Sidebar toggle (mobile) ---------- */
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  const menuToggle = document.getElementById("menuToggle");

  function openSidebar() {
    sidebar.classList.add("open");
    backdrop.classList.add("open");
  }
  function closeSidebar() {
    sidebar.classList.remove("open");
    backdrop.classList.remove("open");
  }

  menuToggle?.addEventListener("click", () => {
    sidebar.classList.contains("open") ? closeSidebar() : openSidebar();
  });
  backdrop?.addEventListener("click", closeSidebar);

  /* ---------- Close mobile sidebar on navigation ---------- */
  /* Active state itself is server-rendered in base.html via request.endpoint */
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", () => closeSidebar());
  });

  /* ---------- Dropdowns: notifications + profile ---------- */
  const bellBtn = document.getElementById("bellBtn");
  const bellPanel = document.getElementById("bellPanel");
  const profileBtn = document.getElementById("profileBtn");
  const profilePanel = document.getElementById("profilePanel");

  function toggleDropdown(panel, others) {
    const isOpen = panel.classList.contains("open");
    others.forEach((p) => p.classList.remove("open"));
    panel.classList.toggle("open", !isOpen);
  }

  bellBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleDropdown(bellPanel, [profilePanel]);
  });
  profileBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleDropdown(profilePanel, [bellPanel]);
  });
  document.addEventListener("click", () => {
    bellPanel?.classList.remove("open");
    profilePanel?.classList.remove("open");
  });

  /* ---------- Chart range toggle (visual placeholder) ---------- */
  document.querySelectorAll(".range-toggle button").forEach((btn) => {
    btn.addEventListener("click", () => {
      btn.parentElement.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });

  /* ---------- Stat number count-up animation ---------- */
  const counters = document.querySelectorAll(".stat-number[data-count]");
  const animateCount = (el) => {
    const target = parseInt(el.dataset.count, 10) || 0;
    const duration = 900;
    const start = performance.now();

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  };

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.4 }
  );
  counters.forEach((el) => observer.observe(el));
});
