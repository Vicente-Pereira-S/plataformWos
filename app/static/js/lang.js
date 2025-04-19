document.addEventListener("DOMContentLoaded", function () {
    const langLinks = document.querySelectorAll(".lang-select");
    langLinks.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const lang = this.getAttribute("data-lang");
            fetch(`/set-language/${lang}`)
                .then(() => window.location.reload());
        });
    });
});
