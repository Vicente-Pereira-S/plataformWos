// Script para cambiar el idioma y mantener la preferencia
document.addEventListener("DOMContentLoaded", function () {
    const langLinks = document.querySelectorAll(".lang-select");

    langLinks.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const selectedLang = this.dataset.lang;

            fetch(`/set-language/${selectedLang}`)
                .then(() => location.reload());
        });
    });
});
