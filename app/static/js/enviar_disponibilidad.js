window.addInterval = function(dayId) {
    const container = document.getElementById(`intervals-${dayId}`);
    const countField = document.getElementById(`intervalCount-${dayId}`);
    let count = parseInt(countField.value);

    if (count >= 5) return alert("Máximo 5 intervalos");

    count++;
    countField.value = count;

    const div = document.createElement("div");
    div.className = "interval-container mt-1";
    div.innerHTML = `
        <select class="form-select form-select-sm d-inline w-auto" name="start-${dayId}-interval${count}" required></select>
        <span class="mx-1">-</span>
        <select class="form-select form-select-sm d-inline w-auto" name="end-${dayId}-interval${count}" required></select>
        <button type="button" class="btn btn-sm btn-danger ms-2 remove-btn" onclick="removeInterval(this)">Eliminar</button>
    `;
    container.appendChild(div);

    const selects = div.querySelectorAll("select");
    populateTimeSelects(selects[0], selects[1]);

    if (count === 2) {
        container.querySelector(".remove-btn").disabled = false;
    }
    if (count >= 5) {
        document.getElementById(`addInterval-${dayId}`).disabled = true;
    }
};

window.removeInterval = function(btn) {
    const wrapper = btn.closest(".interval-container");
    const container = wrapper.parentElement;
    const dayId = container.id.split("-")[1];
    const countField = document.getElementById(`intervalCount-${dayId}`);
    let count = parseInt(countField.value);

    wrapper.remove();
    countField.value = --count;

    if (count === 1) {
        container.querySelector(".remove-btn").disabled = true;
    }

    document.getElementById(`addInterval-${dayId}`).disabled = false;
};

document.addEventListener("DOMContentLoaded", () => {
    setupDayToggle();

    // Inicializar todos los selects visibles
    document.querySelectorAll(".interval-container").forEach(container => {
        const selects = container.querySelectorAll("select");
        populateTimeSelects(selects[0], selects[1]);
    });

    document.getElementById("groupForm").addEventListener("submit", handleSubmit);
});

function populateTimeSelects(startSelect, endSelect) {
    for (let hour = 0; hour < 24; hour++) {
        const hourStr = hour.toString().padStart(2, "0");
        ["00", "30"].forEach(min => {
            const value = `${hourStr}:${min}`;
            startSelect.add(new Option(value, value));
            endSelect.add(new Option(value, value));
        });
    }

    startSelect.addEventListener("change", () => updateEndOptions(startSelect, endSelect));
    updateEndOptions(startSelect, endSelect);
}

function updateEndOptions(start, end) {
    const startVal = start.value;
    const [startHour, startMinute] = startVal.split(":").map(Number);
    const currentEndValue = end.value;
    end.innerHTML = '';

    for (let hour = 0; hour < 24; hour++) {
        for (let minute of [0, 30]) {
            if (hour > startHour || (hour === startHour && minute >= startMinute)) {
                const timeStr = `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;
                end.add(new Option(timeStr, timeStr));
            }
        }
    }

    for (let i = 0; i < end.options.length; i++) {
        if (end.options[i].value === currentEndValue) {
            end.selectedIndex = i;
            return;
        }
    }

    end.selectedIndex = 0;
}

function setupDayToggle() {
    const boxes = document.querySelectorAll('input[name="selectedDays"]');
    boxes.forEach((box) => {
        box.addEventListener("change", function () {
            const dayId = this.value;
            const container = document.getElementById(`day${dayId}`);
            const inputs = container.querySelectorAll("input, select, button");

            if (this.checked) {
                container.classList.remove("hide");

                inputs.forEach(el => {
                    // Si es botón "Eliminar"
                    if (el.classList.contains("remove-btn")) {
                        const intervalContainer = el.closest(".interval-container");
                        const allContainers = intervalContainer.parentElement.querySelectorAll(".interval-container");
                        el.disabled = allContainers.length <= 1;
                    } else {
                        el.disabled = false;
                    }
                });

            } else {
                container.classList.add("hide");
                inputs.forEach(el => el.disabled = true);
            }
        });
    });
}


function handleSubmit(e) {
    e.preventDefault();

    // Deshabilitar campos ocultos para evitar errores de validación
    document.querySelectorAll(".day-container.hide input, .day-container.hide select, .day-container.hide button").forEach(el => {
        el.disabled = true;
    });

    const selected = [...document.querySelectorAll('input[name="selectedDays"]:checked')];
    if (!selected.length) return alert("Selecciona al menos un día");

    const form = new FormData(e.target);
    const data = {
        nickname: form.get("userName"),
        ingame_id: form.get("userID"),
        alliance_id: form.get("alliance"),
        submissions: [],
    };

    selected.forEach((checkbox) => {
        const dayId = checkbox.value;
        const d = {
            group_day_id: parseInt(dayId),
            speedups: parseInt(form.get(`speedups-day${dayId}`)),
            intervals: [],
        };

        const count = parseInt(document.getElementById(`intervalCount-day${dayId}`).value);
        for (let j = 1; j <= count; j++) {
            const s = form.get(`start-day${dayId}-interval${j}`);
            const e = form.get(`end-day${dayId}-interval${j}`);
            if (s && e) d.intervals.push({ start: s, end: e });
        }

        data.submissions.push(d);
    });

    fetch('/public/submit-availability', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            // Redirección futura
            window.location.href = "/public/confirm-submission";
        } else {
            alert("Error al enviar la información: " + result.message);
        }
    })
    .catch(err => {
        console.error(err);
        alert("Error al enviar la información");
    });
}
