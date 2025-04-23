document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("searchForm");
    const input = document.getElementById("codigoInput");
    const msg = document.getElementById("codigo-msg");
    const btn = document.getElementById("buscarBtn");
    const resultado = document.getElementById("resultadoBusqueda");

    const msgOk = resultado.dataset.msgOk;
    const msgNotFound = resultado.dataset.msgNotFound;
    const msgError = resultado.dataset.msgError;

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        const codigo = input.value.trim();
        if (!codigo || btn.disabled) return;

        fetch(`/public/search-state-ajax?code=${encodeURIComponent(codigo)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resultado.innerHTML = `<div class="alert alert-success">${msgOk}: <strong>${codigo}</strong> (Estado: ${data.state_number})</div>`;
                } else {
                    resultado.innerHTML = `<div class="alert alert-danger">${msgNotFound}</div>`;
                }
            })
            .catch(() => {
                resultado.innerHTML = `<div class="alert alert-danger">${msgError}</div>`;
            });
    });

    window.validateGroupCode = function () {
        if (!input || !msg || !btn) return;

        input.value = input.value.toUpperCase();
        const regex = /^[A-Z0-9-]*$/;

        if (input.value === "") {
            msg.textContent = "";
            msg.style.color = "";
            btn.disabled = false;
            return;
        }

        if (!regex.test(input.value)) {
            msg.textContent = msg.dataset.invalid;
            msg.style.color = "red";
            btn.disabled = true;
        } else {
            msg.textContent = msg.dataset.valid;
            msg.style.color = "green";
            btn.disabled = false;
        }
    };
});
