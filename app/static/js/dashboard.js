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




  /* ---------- Customer Growth chart ---------- */
  const growthChart = document.querySelector(".growth-chart");
  const chartAxis = document.querySelector(".chart-axis");

  if (growthChart && chartAxis) {
    let monthlyGrowth = [];
    let dailyGrowth = [];

    try {
      monthlyGrowth = JSON.parse(growthChart.dataset.growth || "[]");
      dailyGrowth = JSON.parse(
        growthChart.dataset.dailyGrowth || "[]"
      );
    } catch (error) {
      console.error("Could not read customer growth data:", error);
    }

    const areaLine = growthChart.querySelector(".area");
    const line = growthChart.querySelector(".line");
    const endDot = growthChart.querySelector(".end-dot");
    const growthPoints = growthChart.querySelector(".growth-points");
    function renderGrowthChart(range) {
      const data = range === "1M"
        ? dailyGrowth
        : monthlyGrowth.slice(range === "3M" ? -3 : -12);

      if (!data.length || !areaLine || !line || !endDot) {
        console.warn("No customer growth data available for:", range);
        return;
      }

      const width = 560;
      const bottom = 190;
      const top = 30;
      const maxCount = Math.max(
       1,
       ...data.map(item => Number(item.count) || 0)
      );


      const points = data.map((item, index) => {
        const x = data.length === 1
          ? width / 2
          : (index / (data.length - 1)) * width;

        const count = Number(item.count) || 0;
        const y = bottom - (count / maxCount) * (bottom - top);

        return { x, y, label: item.label, count };
      });


      const linePoints = points
        .map(point => `${point.x},${point.y}`)
        .join(" ");

      line.setAttribute("points", linePoints);

      const areaPoints = `${linePoints} ${points[points.length - 1].x},220 ${points[0].x},220`;
      areaLine.setAttribute("points", areaPoints);


      const lastPoint = points[points.length - 1];
      endDot.setAttribute("cx", lastPoint.x);
      endDot.setAttribute("cy", lastPoint.y);

      const endTooltip = endDot.querySelector("title");
      if (endTooltip) {
        endTooltip.textContent =
          `${lastPoint.label}: ${lastPoint.count} customer${lastPoint.count === 1 ? "" : "s"}`;
      }

      // Create a hoverable circle for every data point.
      if (growthPoints) {
        growthPoints.replaceChildren();

        points.forEach(point => {
          const circle = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "circle"
          );

          circle.setAttribute("cx", point.x);
          circle.setAttribute("cy", point.y);
          circle.setAttribute("r", "4");
          circle.style.opacity = "0";
          circle.style.transition = "opacity 0.15s ease";
          circle.setAttribute("fill", "#7c5cfc");
          circle.setAttribute("stroke", "#ffffff");
          circle.setAttribute("stroke-width", "1.5");
          circle.style.cursor = "pointer";
          circle.addEventListener("mouseenter", () => {
            circle.style.opacity = "1";
          });

          circle.addEventListener("mouseleave", () => {
            circle.style.opacity = "0";
          });

          const tooltip = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "title"
          );

          tooltip.textContent =
            `${point.label}: ${point.count} customer${point.count === 1 ? "" : "s"}`;

          circle.appendChild(tooltip);
          growthPoints.appendChild(circle);
        });
      }
  

      chartAxis.replaceChildren();

      data.forEach((item, index) => {
        const shouldShowLabel = range === "1M"
          ? index === 0 ||
            index === data.length - 1 ||
            index % 7 === 0
          : data.length <= 5 ||
            index === 0 ||
            index === data.length - 1 ||
            index === Math.floor((data.length - 1) / 2);

        if (shouldShowLabel) {
          const label = document.createElement("span");
          label.textContent = item.label;
          chartAxis.appendChild(label);
        }
      });
    }

    document.querySelectorAll(".range-toggle button").forEach(btn => {
      btn.addEventListener("click", () => {
        btn.parentElement.querySelectorAll("button").forEach(button => {
          button.classList.remove("active");
        });

        btn.classList.add("active");
        renderGrowthChart(btn.textContent.trim());
      });
    });

    const activeButton = document.querySelector(
      ".range-toggle button.active"
    );

    renderGrowthChart(activeButton?.textContent.trim() || "1Y");
  }

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


  /* ---------- Data-driven stat sparklines ---------- */
  document.querySelectorAll(".spark[data-spark]").forEach((svg) => {
    const polyline = svg.querySelector("polyline");
    if (!polyline) return;

    try {
      const data = JSON.parse(svg.dataset.spark || "[]");
      if (!data.length) return;

      const values = data.map((item) => Number(item.count) || 0);
      const max = Math.max(...values, 1);
      const min = Math.min(...values);
      const range = max - min || 1;

      const points = values
        .map((value, index) => {
          const x = values.length === 1
            ? 50
            : (index * 100) / (values.length - 1);

          const y = 26 - ((value - min) / range) * 20;
          return `${x},${y}`;
        })
        .join(" ");

      polyline.setAttribute("points", points);
      polyline.setAttribute("fill", "none");
    } catch (error) {
      console.error("Could not render customer sparkline:", error);
    }
  });
