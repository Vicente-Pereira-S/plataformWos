function generarCodigo() {
    const input = document.getElementById("group_code");
    const random = Math.floor(1000 + Math.random() * 9000);
    const codigo = `R-${random}`;
    input.value = codigo;

    // Agrega animación temporal
    input.classList.add("flash-input");
    setTimeout(() => {
        input.classList.remove("flash-input");
    }, 400);
}

function togglePasswords() {
    const pass1 = document.getElementById("password");
    const pass2 = document.getElementById("confirm_password");

    const type = pass1.type === "password" ? "text" : "password";
    pass1.type = type;
    pass2.type = type;
}

function checkPasswordsMatch() {
    const pass1 = document.getElementById("password");
    const pass2 = document.getElementById("confirm_password");
    const msg = document.getElementById("password-match-msg");
    const registerBtn = document.getElementById("registerBtn");

    if (!pass1 || !pass2 || !msg || !registerBtn) return;

    if (pass1.value === "" || pass2.value === "") {
        msg.textContent = "";
        registerBtn.disabled = true;
        return;
    }

    if (pass1.value === pass2.value) {
        msg.textContent = msg.dataset.valid;
        msg.style.color = "green";
        registerBtn.disabled = false;
    } else {
        msg.textContent = msg.dataset.invalid;
        msg.style.color = "red";
        registerBtn.disabled = true;
    }
}


function validateGroupCode() {
    const input = document.getElementById("group_code");
    const msg = document.getElementById("group-code-msg");
    const btn = document.getElementById("createGroupBtn");

    if (!input || !msg || !btn) return;

    input.value = input.value.toUpperCase();
    
    const regex = /^[A-Z0-9-]*$/;

    if (input.value === "") {
        msg.textContent = "";
        msg.style.color = "";
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
}

function copyGroupCode() {
    const input = document.getElementById("groupCodeInput");
    if (!input) return;

    // Para asegurar compatibilidad, creamos un rango y lo seleccionamos manualmente
    if (navigator.clipboard && window.isSecureContext) {
        // Método moderno y seguro
        navigator.clipboard.writeText(input.value)
            .then(showCopyToast)
            .catch(() => fallbackCopyText(input));
    } else {
        // Fallback para navegadores más antiguos o no seguros (iOS Safari)
        fallbackCopyText(input);
    }
}

function fallbackCopyText(input) {
    input.focus();
    input.setSelectionRange(0, input.value.length); // compatible con móviles
    const successful = document.execCommand('copy'); // método clásico
    if (successful) {
        showCopyToast();
    } else {
        alert("No se pudo copiar el código. Intenta seleccionarlo manualmente.");
    }
}


function showCopyToast() {
    const toast = document.getElementById("copyToast");
    if (!toast) return;

    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 2000);
}



// -----------------------------------------------
// UTILIDADES COMUNES PARA CREACIÓN Y EDICIÓN DE GRUPOS
// -----------------------------------------------

function updateConfirmButton() {
    const allianceInputs = document.querySelectorAll('.alliance-field');
    const dayInputs = document.querySelectorAll('.day-field');
    const confirmBtn = document.getElementById('confirmButton');

    const allianceRegex = /^[A-Za-z0-9]{3}$/;
    const allAlliancesFilled = Array.from(allianceInputs).every(input => input.value.trim() !== '' && allianceRegex.test(input.value.trim()));
    const allDaysFilled = Array.from(dayInputs).every(input => input.value.trim() !== '');

    const alliancesValid = allianceInputs.length > 0;
    const daysValid = dayInputs.length > 0;

    confirmBtn.disabled = !(alliancesValid && daysValid && allAlliancesFilled && allDaysFilled);
}

function renderAllianceFields(count, existingAlliances = []) {
    const container = document.getElementById('alliancesContainer');
    container.innerHTML = '';

    const regex = /^[A-Za-z0-9]{3}$/;

    if (isNaN(count) || count < 1) {
        updateConfirmButton();
        return;
    }

    for (let i = 1; i <= count; i++) {
        const wrapper = document.createElement('div');
        wrapper.className = 'mb-3';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control alliance-field';
        input.placeholder = `Alianza ${i} (3 caracteres)`;
        input.maxLength = 3;
        input.required = true;
        input.name = `alliance_${i}`;

        // Mensaje de error
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = 'Debe tener exactamente 3 caracteres alfanuméricos.';

        // Evento de validación
        input.addEventListener("input", () => {
            const val = input.value.trim();
            if (regex.test(val)) {
                input.classList.remove("is-invalid");
                input.classList.add("is-valid");
            } else {
                input.classList.remove("is-valid");
                input.classList.add("is-invalid");
            }
            updateConfirmButton();
        });

        // Valor precargado si existe
        if (existingAlliances[i - 1] && existingAlliances[i - 1].name !== "Otra") {
            input.value = existingAlliances[i - 1].name;
            const val = input.value.trim();
            if (regex.test(val)) {
                input.classList.add("is-valid");
            } else {
                input.classList.add("is-invalid");
            }
        }

        // Armar bloque
        wrapper.appendChild(input);
        wrapper.appendChild(feedback);
        container.appendChild(wrapper);
    }

    // Campo readonly para la alianza "Otra"
    const otherInput = document.createElement('input');
    otherInput.type = 'text';
    otherInput.className = 'form-control mb-2';
    otherInput.placeholder = '[Otra] (Alianza adicional obligatoria)';
    otherInput.readOnly = true;
    otherInput.value = 'Otra';
    container.appendChild(otherInput);

    updateConfirmButton();
}



function renderDayFields(count, existingDays = []) {
    const container = document.getElementById('daysContainer');
    container.innerHTML = '';

    const dayRegex = /^[\p{L}0-9 ]{1,20}$/u;

    if (isNaN(count) || count < 1) {
        updateConfirmButton();
        return;
    }

    for (let i = 1; i <= count; i++) {
        const wrapper = document.createElement('div');
        wrapper.className = 'mb-3';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control day-field';
        input.placeholder = `Nombre de la cita ${i} (Ej: VP Monday)`;
        input.maxLength = 20;
        input.required = true;
        input.name = `day_${i}`;

        // Mensaje de error
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = 'Máximo 20 caracteres. Solo letras, números y espacios.';

        // Evento de validación
        input.addEventListener("input", () => {
            const val = input.value.trim();
            if (dayRegex.test(val)) {
                input.classList.remove("is-invalid");
                input.classList.add("is-valid");
            } else {
                input.classList.remove("is-valid");
                input.classList.add("is-invalid");
            }
            updateConfirmButton();
        });

        // Valor precargado si existe
        if (existingDays[i - 1]) {
            input.value = existingDays[i - 1].name;
            const val = input.value.trim();
            if (dayRegex.test(val)) {
                input.classList.add("is-valid");
            } else {
                input.classList.add("is-invalid");
            }
        }

        // Armar bloque
        wrapper.appendChild(input);
        wrapper.appendChild(feedback);
        container.appendChild(wrapper);
    }

    updateConfirmButton();
}



// -----------------------------------------------
// FUNCIONES DE INICIALIZACIÓN SEGÚN PLANTILLA
// -----------------------------------------------

function initGrupoSettingsCreate() {
    const selectAlliances = document.getElementById('numAlliances');
    const selectDays = document.getElementById('numDays');

    selectAlliances.addEventListener('change', () => {
        renderAllianceFields(parseInt(selectAlliances.value));
    });

    selectDays.addEventListener('change', () => {
        renderDayFields(parseInt(selectDays.value));
    });
}

function initGrupoSettingsEdit(existingAlliances = [], existingDays = []) {
    const selectAlliances = document.getElementById('numAlliances');
    const selectDays = document.getElementById('numDays');

    // Prellenar los select
    selectAlliances.value = existingAlliances.filter(a => a.name !== "Otra").length;
    selectDays.value = existingDays.length;

    // Renderizar los campos
    renderAllianceFields(parseInt(selectAlliances.value), existingAlliances);
    renderDayFields(parseInt(selectDays.value), existingDays);

    // Event listeners
    selectAlliances.addEventListener('change', () => {
        renderAllianceFields(parseInt(selectAlliances.value), []);
    });

    selectDays.addEventListener('change', () => {
        renderDayFields(parseInt(selectDays.value), []);
    });
}





function validateUsernameInput() {
    const usernameInput = document.getElementById("username");
    const registerBtn = document.getElementById("registerBtn");

    if (!usernameInput || !registerBtn) return;

    const regex = /^[\p{L}\p{N}_-]{1,15}$/u;  // permite letras (de cualquier idioma), números, _ y -, máx 15
    const value = usernameInput.value;

    if (regex.test(value)) {
        usernameInput.classList.remove("is-invalid");
        usernameInput.classList.add("is-valid");
        registerBtn.disabled = false;
    } else {
        usernameInput.classList.remove("is-valid");
        usernameInput.classList.add("is-invalid");
        registerBtn.disabled = true;
    }
}
