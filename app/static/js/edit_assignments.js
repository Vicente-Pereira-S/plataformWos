window.addEventListener("DOMContentLoaded", () => {
    const tabla = document.querySelector("table");
    const lista = document.querySelector(".dashboard-wrapper");
    if (tabla && lista) {
        lista.style.maxHeight = tabla.offsetHeight + "px";
        lista.style.overflowY = "auto";
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("assignmentForm");
    const inputs = document.querySelectorAll(".player-input");
    const validNames = Array.from(document.querySelectorAll("#submissionsList option")).map(opt => opt.value.trim());
    const assignedMap = new Map();

    function validateInputs() {
        assignedMap.clear();
        let isValid = true;

        // Limpiar errores previos
        inputs.forEach(input => {
            const errorContainer = getOrCreateError(input);
            input.classList.remove("is-invalid");
            errorContainer.textContent = "";
            errorContainer.classList.add("d-none");
        });

        // Agrupar todos los valores válidos ingresados
        inputs.forEach(input => {
            const value = input.value.trim();
            const block = parseInt(input.getAttribute("data-block"));

            if (value === "") return;

            // Nombre inválido (no está en la lista)
            if (!validNames.includes(value)) {
                input.classList.add("is-invalid");
                const errorContainer = getOrCreateError(input);
                errorContainer.textContent = "Nombre inválido, selecciona desde la lista.";
                errorContainer.classList.remove("d-none");
                isValid = false;
                return;
            }

            if (!assignedMap.has(value)) {
                assignedMap.set(value, []);
            }

            assignedMap.get(value).push({ input, block });
        });

        // Revisar duplicados y aplicar errores
        assignedMap.forEach((entries, name) => {
            if (entries.length > 1) {
                isValid = false;
                const hours = entries.map(e => generateTime(e.block));
                const msg = `Nombre duplicado en: ${hours.join(", ")}`;
                entries.forEach(({ input }) => {
                    input.classList.add("is-invalid");
                    const errorContainer = getOrCreateError(input);
                    errorContainer.textContent = msg;
                    errorContainer.classList.remove("d-none");
                });
            }
        });

        actualizarEstilosSolicitantesAsignados();
        return isValid;
    }

    function getOrCreateError(input) {
        let error = input.nextElementSibling;
        if (!error || !error.classList.contains("input-error-msg")) {
            error = document.createElement("div");
            error.classList.add("input-error-msg");
            input.insertAdjacentElement("afterend", error);
        }
        return error;
    }

    function generateTime(blockIndex) {
        const h = Math.floor(blockIndex / 2);
        const m = blockIndex % 2 === 0 ? "00" : "30";
        return `${h.toString().padStart(2, "0")}:${m}`;
    }

    function actualizarEstilosSolicitantesAsignados() {
        const assignedNames = new Set();
        inputs.forEach(input => {
            const value = input.value.trim();
            if (value !== "") {
                assignedNames.add(value);
            }
        });

        document.querySelectorAll("#availablePlayersList li").forEach(li => {
            const nickname = li.innerText.split("]").pop().split("\n")[0].trim();
            if (assignedNames.has(nickname)) {
                li.style.backgroundColor = "green";
            } else {
                li.style.backgroundColor = "";
            }



        });
    }

    // Validación al escribir (en tiempo real)
    inputs.forEach(input => {
        input.addEventListener("input", () => {
            const value = input.value.trim();
            const matches = validNames.filter(name => name.toLowerCase() === value.toLowerCase());

            if (!matches.includes(value)) {
                input.dataset.pendingValue = value;
            } else {
                delete input.dataset.pendingValue;
            }

            validateInputs();
        });

        input.addEventListener("blur", () => {
            const pending = input.dataset.pendingValue;
            if (pending) {
                input.value = "";
                delete input.dataset.pendingValue;
                validateInputs();
            }
        });
    });

    // Validación final al guardar
   form.addEventListener("submit", (e) => {
    const valid = validateInputs();
    if (!valid) {
        e.preventDefault();
        alert("Hay errores, por favor verifica antes de guardar");
        return;
    }

    // Prevenir envío inmediato
    e.preventDefault();

    // Mostrar el modal de confirmación
    const modal = new bootstrap.Modal(document.getElementById("confirmSaveModal"));
    modal.show();

    // Al hacer clic en "Sí, guardar"
    document.getElementById("confirmSaveBtn").onclick = () => {
        // Desactivar botón para evitar doble envío
        const confirmBtn = document.getElementById("confirmSaveBtn");
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> {{ _('Guardando...') }}`;

        // Mostrar spinner general
        document.getElementById("savingOverlay")?.classList.remove("d-none");

        // Ocultar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById("confirmSaveModal"));
        modal.hide();

        // Enviar el formulario
        form.submit();
    };

});


    // Al cargar
    actualizarEstilosSolicitantesAsignados();
});
