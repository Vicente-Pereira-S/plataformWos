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
    if(pass1){
        pass1.type = type;
    }
    if(pass1){
        pass2.type = type;
    }
    
}

function checkPasswordsMatch() {
    const pass1 = document.getElementById("password");
    const pass2 = document.getElementById("confirm_password");
    const msg = document.getElementById("password-match-msg");  // Donde quiero mostrar mi mensaje error
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
        btn.disabled = true
        return;
    } else {
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

}

// Funcion pedida a la IA, no sabia como hacerlo para que fuera multiplataforma
// Soporta navegadores modernos y antiguos (tiene fallback para navegadores que no soportan el API navigator.clipboard).
function copyTextById(inputId, toastId = "copyToast", errorToastId = "copyErrorToast") {
    const input = document.getElementById(inputId);
    if (!input) return;

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(input.value)
            .then(() => showCopyToast(toastId))
            .catch(() => fallbackCopyText(input, toastId, errorToastId));
    } else {
        fallbackCopyText(input, toastId, errorToastId);
    }
}

function fallbackCopyText(input, toastId, errorToastId) {
    input.focus();
    input.setSelectionRange(0, input.value.length);
    const successful = document.execCommand('copy');

    if (successful) {
        showCopyToast(toastId);
    } else {
        const errorToast = document.getElementById(errorToastId);
        if (errorToast) {
            const toast = new bootstrap.Toast(errorToast);
            toast.show();
        }
    }
}

function showCopyToast(toastId) {
    const toast = document.getElementById(toastId);
    if (!toast) return;

    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 2000);
}




// -----------------------------------------------
// UTILIDADES COMUNES PARA CREACIÓN Y EDICIÓN DE GRUPOS
// -----------------------------------------------


//Esta función controla dinámicamente si el botón "Guardar cambios" del
// formulario de alianzas y días debe estar habilitado o deshabilitado.
function updateConfirmButton() {
    const allianceInputs = document.querySelectorAll('.alliance-field');        // Campos renderizados por funciones
    const dayInputs = document.querySelectorAll('.day-field');                  // Campos renderizados por funciones
    const confirmBtn = document.getElementById('confirmButton');                // boton en modal y settings_create

    const allianceRegex = /^[A-Za-z0-9]{3}$/;
    const allAlliancesFilled = Array.from(allianceInputs).every(input => input.value.trim() !== '' && allianceRegex.test(input.value.trim()));
    const allDaysFilled = Array.from(dayInputs).every(input => input.value.trim() !== '');

    const alliancesValid = allianceInputs.length > 0;
    const daysValid = dayInputs.length > 0;

    confirmBtn.disabled = !(alliancesValid && daysValid && allAlliancesFilled && allDaysFilled);
}


// Funcion especializada en render alianzas
function renderAllianceFields(count, existingAlliances = []) {
    const container = document.getElementById('alliancesContainer');
    container.innerHTML = '';

    const regex = /^[A-Za-z0-9]{3}$/;

    if (isNaN(count) || count < 1) {
        updateConfirmButton();
        return;
    }

    const myMsg = document.getElementById("msgContainer");

    for (let i = 1; i <= count; i++) {
        const wrapper = document.createElement('div');
        wrapper.className = 'mb-3';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control alliance-field';
        input.placeholder = `${myMsg.dataset.alianza} ${i}`;
        input.maxLength = 3;
        input.required = true;
        input.name = `alliance_${i}`;

        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = myMsg.dataset.allianceInvalid;

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

        if (existingAlliances[i - 1]) {
            input.value = existingAlliances[i - 1].name;
            const val = input.value.trim();
            if (regex.test(val)) {
                input.classList.add("is-valid");
            } else {
                input.classList.add("is-invalid");
            }
        }

        wrapper.appendChild(input);
        wrapper.appendChild(feedback);
        container.appendChild(wrapper);
    }

    updateConfirmButton();
}





// render de nombre de los dias
function renderDayFields(count, existingDays = []) {
    const container = document.getElementById('daysContainer');
    container.innerHTML = '';

    const dayRegex = /^[\p{L}0-9 ]{1,35}$/u;

    if (isNaN(count) || count < 1) {
        updateConfirmButton();
        return;
    }

    // obtengo centro de mensajes
    const myMsg = document.getElementById("msgContainer")

    const day_ex = [
        "",
        "VP Monday",
        "Friday Research",
        "MoE Thursday",
        "VP Tuesday"
    ];

    // creo un div con los campos necesarios para incrustar el modal
    for (let i = 1; i <= count; i++) {
        const wrapper = document.createElement('div');
        wrapper.className = 'mb-3';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control day-field';
        input.placeholder = `${myMsg.dataset.day} ${day_ex[i]}`;
        input.maxLength = 35;
        input.required = true;
        input.name = `day_${i}`;

        // Mensaje de error
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = myMsg.dataset.dayInvalid;

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

    // Prellenar los select, no sé donde se aplica
    selectAlliances.value = existingAlliances.length;
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



// -----------------------------------------------
// SE USA EN RENDERIZAR PREGUNTA SECRETA AL INTENTAR RECUPEAR PASSWORD
// -----------------------------------------------

function mostrarPreguntaSecreta() {
    const myContainer = document.getElementById("questionContainer");
    const questionShow = document.getElementById("questionShow");
    if (!myContainer || !questionShow) return;

    const myVar = myContainer.dataset.question;   // Numero ID de la pregunta

    const preguntas = {
        "1": myContainer.dataset.question1,
        "2": myContainer.dataset.question2,
        "3": myContainer.dataset.question3
    };

    questionShow.textContent = preguntas[myVar] || "-";
}
document.addEventListener("DOMContentLoaded", mostrarPreguntaSecreta);




// -----------------------------------------------
// SE USA PARA MOSTRAR EL RESULTADO DEL ALGORITMO DE HORARIOS
// -----------------------------------------------

function runAssign(dayId) {
    const tablaBody = document.getElementById(`tabla-asignaciones-${dayId}`);
    const tablaNoAsignados = document.getElementById(`tabla-no-asignados-${dayId}`);
    const switchLimite = document.getElementById(`switchLimite-${dayId}`);
    const containerLimites = document.getElementById(`limitesContainer-${dayId}`);
    const resumenCupos = document.getElementById(`resumen-cupos-${dayId}`);
    const listaCupos = document.getElementById(`lista-cupos-${dayId}`);

    // Mostrar mensaje temporal de carga
    tablaBody.innerHTML = `
        <tr><td colspan="6" class="text-center text-theme-muted py-3">Cargando asignaciones...</td></tr>
    `;
    tablaNoAsignados.innerHTML = "";
    listaCupos.innerHTML = "";
    resumenCupos.classList.add("d-none");

    // Construir objeto de cupos si el switch está activado
    let cupos = null;
    let cuposIniciales = {};
    const alianzasB = [];  // ← NUEVO: Alianzas sin límite definido
    const switchActivo = switchLimite && switchLimite.checked;

    if (switchActivo) {
        document.getElementById(`bloque-no-asignados-${dayId}`).classList.add("d-none");
        cupos = {};
        const selects = containerLimites.querySelectorAll("select");
        selects.forEach(select => {
            const value = select.value;
            const allianceName = select.labels[0].innerText.replace(/\[|\]/g, "").trim();
            if (value !== "") {
                const val = parseInt(value);
                cupos[allianceName] = val;
                cuposIniciales[allianceName] = val;
            } else {
                alianzasB.push(allianceName); // ← Guardamos alianzas sin límite
            }
        });
    }

    // Enviar solicitud al backend
    fetch(`/groups/asignar/${dayId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ cupos: cupos })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            tablaBody.innerHTML = `<tr><td colspan="6" class="text-danger">Error al ejecutar el algoritmo.</td></tr>`;
            return;
        }

        const asignaciones = data.data.assignments || [];
        const noAsignados = data.data.unassigned || [];
        const cuposRestantes = data.data.remaining || {};

        // Crear un mapa por bloque horario
        const mapa = new Map();
        for (const r of asignaciones) {
            mapa.set(r.hour_block, r);
        }

        // Generar las 48 filas
        let rows = "";
        for (let b = 0; b < 48; b++) {
            const hora = `${String(Math.floor(b / 2)).padStart(2, '0')}:${b % 2 === 0 ? '00' : '30'}`;
            if (mapa.has(b)) {
                const r = mapa.get(b);
                rows += `
                    <tr>
                        <td><strong>${hora}</strong></td>
                        <td>[${r.alliance}]</td>
                        <td>${r.nickname}</td>
                        <td>${r.ingame_id || '-'}</td>
                        <td>${r.speedups}</td>
                        <td>${r.availability_str}</td>
                    </tr>
                `;
            } else {
                rows += `
                    <tr class="table-secondary">
                        <td><strong>${hora}</strong></td>
                        <td colspan="5"><em>— Sin asignación —</em></td>
                    </tr>
                `;
            }
        }

        tablaBody.innerHTML = rows;

        // Si el switch estaba activo, ocultar tabla de no asignados y mostrar resumen
        if (switchActivo) {
            tablaNoAsignados.innerHTML = "";
            const resumen = [];

            for (const [alianza, total] of Object.entries(cuposIniciales)) {
                const restante = cuposRestantes[alianza] ?? 0;
                const usados = total - restante;
                resumen.push(`<li class="list-group-item">[${alianza}]: ${usados}/${total}</li>`);
            }

            // Mostrar "B" con nombres de alianzas que no tenían límite
            if ("B" in cuposRestantes) {
                const usadosB = 48 - Object.entries(cuposIniciales).reduce((a, [k, v]) => a + v, 0) - cuposRestantes.B;
                const totalB = 48 - Object.entries(cuposIniciales).reduce((a, [k, v]) => a + v, 0);
                const alianzasBstr = alianzasB.length > 0 ? ` [${alianzasB.map(a => a).join('], [')}]` : "";
                resumen.push(`<li class="list-group-item">${alianzasBstr}: ${usadosB}/${totalB}</li>`);
            }

            listaCupos.innerHTML = resumen.join("");
            resumenCupos.classList.remove("d-none");

        } else {
            // Mostrar no asignados si el switch está apagado y hay datos
            if (noAsignados.length > 0) {
                for (const u of noAsignados) {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>[${u.alliance}]</td>
                        <td>${u.nickname}</td>
                        <td>${u.ingame_id || '-'}</td>
                        <td>${u.speedups}</td>
                        <td>${u.availability_str || '<span class="text-muted">No disponible</span>'}</td>
                    `;
                    tablaNoAsignados.appendChild(row);
                }
            } else {
                tablaNoAsignados.innerHTML = `
                    <tr><td colspan="5" class="text-muted">Todos fueron asignados.</td></tr>
                `;
            }
            document.getElementById(`bloque-no-asignados-${dayId}`).classList.remove("d-none");
        }
    })
    .catch(err => {
        tablaBody.innerHTML = `<tr><td colspan="6" class="text-danger">Error inesperado.</td></tr>`;
        console.error(err);
    });
}
