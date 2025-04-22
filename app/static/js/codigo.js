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



