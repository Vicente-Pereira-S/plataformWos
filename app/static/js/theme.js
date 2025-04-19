// app/static/js/theme.js
document.addEventListener("DOMContentLoaded", function () {
    const savedTheme = localStorage.getItem("theme") || "light";
    setTheme(savedTheme);

    document.querySelectorAll(".theme-select").forEach((el) => {
        el.addEventListener("click", function (e) {
            e.preventDefault();
            const selectedTheme = this.getAttribute("data-theme");
            localStorage.setItem("theme", selectedTheme);
            setTheme(selectedTheme);
        });
    });
});

function setTheme(theme) {
    const body = document.body;
    if (theme === "dark") {
        body.classList.add("dark-theme");
        body.classList.remove("light-theme");
    } else {
        body.classList.add("light-theme");
        body.classList.remove("dark-theme");
    }
}
