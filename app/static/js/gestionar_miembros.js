document.addEventListener("DOMContentLoaded", () => {
    const dataDiv = document.getElementById("groupData");
    if (!dataDiv) return;

    const groupCode = dataDiv.dataset.groupCode;
    const creatorId = parseInt(dataDiv.dataset.creatorId);
    const errorMessageUser = dataDiv.dataset.errorMessage;
    const catch1 = dataDiv.dataset.errorCatchMessage1;
    const catch2 = dataDiv.dataset.errorCatchMessage2;

    let miembros = [];
    let usuarioBuscado = null;

    const listaUl = document.getElementById("listaMiembrosGrupo");
    const resultadoBusqueda = document.getElementById("resultadoBusqueda");
    const alertSuccess = document.getElementById("alertSuccess")
    const nombreUsuarioEncontrado = document.getElementById("nombreUsuarioEncontrado");
    const usuarioAConfirmar = document.getElementById("usuarioAConfirmar");
    const alertError = document.getElementById("alertError")
    const usuarioNoEncontrado = document.getElementById("usuarioNoEncontrado");


    document.getElementById("btnEditarMiembros").addEventListener("click", () => {
        resultadoBusqueda.classList.add("d-none");
        alertSuccess.classList.add("d-none");
        alertError.classList.add("d-none");

        fetch(`/groups/members/${groupCode}`)
            .then(res => res.json())
            .then(data => {
                miembros = data.members;
                renderLista();
            });

    });


    // Buscar usuario
    document.getElementById("btnBuscarID").addEventListener("click", () => {
        const id = document.getElementById("inputBuscarID").value;
        if (!id) return;

        fetch(`/groups/search-user-by-id/${id}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    usuarioNoEncontrado.textContent = errorMessageUser;
                    resultadoBusqueda.classList.remove("d-none");
                    alertSuccess.classList.add("d-none")
                    alertError.classList.remove("d-none")
                    return;
                }
                usuarioBuscado = data;
                nombreUsuarioEncontrado.textContent = `${data.username} (ID: ${data.id})`;
                resultadoBusqueda.classList.remove("d-none");
                alertError.classList.add("d-none")
                alertSuccess.classList.remove("d-none");

            })
            .catch(error => {
                console.error(catch1, error);
                alert(catch2)
            });
    });

    // Abrir segundo modal
    document.getElementById("btnVerConfirmarAgregar").addEventListener("click", () => {
        usuarioAConfirmar.textContent = `${usuarioBuscado.username} (ID: ${usuarioBuscado.id})`;
    
        const modal1El = document.getElementById("modalGestionMiembros");
        const modal2El = document.getElementById("modalConfirmarAgregar");
    
        const modal1 = bootstrap.Modal.getInstance(modal1El);
        const modal2 = new bootstrap.Modal(modal2El);
    
        // Esperamos que se cierre completamente el modal 1 antes de abrir el 2
        modal1El.addEventListener("hidden.bs.modal", () => {
            modal2.show();
        }, { once: true });  // 'once' evita que se acumule el listener
    
        modal1.hide();
    });
    

    // Confirmar agregar
    document.getElementById("btnConfirmarAgregar").addEventListener("click", () => {
        if (!miembros.some(u => u.id === usuarioBuscado.id)) {
            miembros.push(usuarioBuscado);
            renderLista();
        }
        bootstrap.Modal.getInstance(document.getElementById("modalConfirmarAgregar")).hide();
        new bootstrap.Modal(document.getElementById("modalGestionMiembros")).show();
    });

    // Guardar cambios
    document.getElementById("btnGuardarMiembros").addEventListener("click", () => {
        const ids = miembros.map(u => u.id);
        fetch(`/groups/save-members/${groupCode}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_ids: ids })
        }).then(() => {
            location.reload();
        });
    });

    // Renderizar lista
    const owner = dataDiv.dataset.ownerLabel;
    function renderLista() {
        listaUl.innerHTML = "";
        miembros.forEach(u => { 
            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between align-items-center";

            const texto = document.createElement("span");
            texto.textContent = u.username;

            const btn = document.createElement("button");
            btn.className = "btn btn-sm btn-outline-danger";
            btn.textContent = "❌";
            btn.onclick = () => {
                if (u.id === creatorId) return;
                miembros = miembros.filter(m => m.id !== u.id);
                renderLista();
            };

            li.appendChild(texto);
            if (u.id !== creatorId) li.appendChild(btn);
            else li.innerHTML += `<span class="badge bg-secondary">${owner}</span>`; // Cambiar para traduccion

            listaUl.appendChild(li);
        });
    }
});
