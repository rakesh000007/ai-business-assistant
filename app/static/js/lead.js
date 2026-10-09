document.addEventListener("DOMContentLoaded", function () {

    const bars = document.querySelectorAll(".ai-score-bar");

    bars.forEach(function (bar) {
        const score = parseInt(bar.dataset.score) || 0;
        bar.style.width = score + "%";
    });

});