// Script para alternar entre tema claro y oscuro
document.addEventListener("DOMContentLoaded", function () {
    const themeLinks = document.querySelectorAll(".theme-select");

    // Leer tema guardado en cookie
    const savedTheme = getCookie("theme");
    if (savedTheme) {
        document.body.setAttribute("data-theme", savedTheme);
    }

    themeLinks.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const selectedTheme = this.dataset.theme;
            document.body.setAttribute("data-theme", selectedTheme);
            document.cookie = `theme=${selectedTheme}; path=/`;
        });
    });
});

// Utilidad para leer cookies
function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? match[2] : null;
}


