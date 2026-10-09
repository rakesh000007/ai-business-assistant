document.addEventListener("DOMContentLoaded", function () {

    const searchInput = document.getElementById("propertySearch");

    const rows = document.querySelectorAll(".property-row");

    if (!searchInput) return;

    searchInput.addEventListener("keyup", function () {

        const value = this.value
           .toLowerCase()
           .replace(/,/g, "")
           .replace(/₹/g, "");

        rows.forEach(row => {

            const text = row.innerText
               .toLowerCase()
               .replace(/,/g, "")
               .replace(/₹/g, "");

            if (text.includes(value)) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }

        });

    });

});