// GESTIONA MIEMBROS
document.addEventListener("DOMContentLoaded", () => {
    const dataDiv = document.getElementById("groupData");
    if (!dataDiv) return;
    if (!(document.getElementById("btnEditarMiembros"))) return;

    const groupCode = dataDiv.dataset.groupCode;
    const creatorId = parseInt(dataDiv.dataset.creatorId);
    const currentUserId = parseInt(dataDiv.dataset.currentUserId);
    const errorMessageUser = dataDiv.dataset.errorMessage;
    const catch1 = dataDiv.dataset.errorCatchMessage1;
    const catch2 = dataDiv.dataset.errorCatchMessage2;
    const ownerLabel = dataDiv.dataset.ownerLabel;

    let miembros = [];
    let miembrosOriginales = [];
    let usuarioBuscado = null;
    let usuarioATransferir = null;

    const listaUl = document.getElementById("listaMiembrosGrupo");
    const resultadoBusqueda = document.getElementById("resultadoBusqueda");
    const alertSuccess = document.getElementById("alertSuccess");
    const nombreUsuarioEncontrado = document.getElementById("nombreUsuarioEncontrado");
    const usuarioAConfirmar = document.getElementById("usuarioAConfirmar");
    const alertError = document.getElementById("alertError");
    const usuarioNoEncontrado = document.getElementById("usuarioNoEncontrado");
    const confirmarTransferir = document.getElementById("usuarioTransferenciaConfirmar");

    // Abrir modal de gestión
    document.getElementById("btnEditarMiembros").addEventListener("click", () => {
        resultadoBusqueda.classList.add("d-none");
        alertSuccess.classList.add("d-none");
        alertError.classList.add("d-none");

        fetch(`/groups/members/${groupCode}`)
            .then(res => res.json())
            .then(data => {
                miembros = data.members;
                miembrosOriginales = data.members.map(u => u.id);
                renderLista();
            });
    });

    // Buscar usuario por ID
    document.getElementById("btnBuscarID").addEventListener("click", () => {
        const id = document.getElementById("inputBuscarID").value;
        if (!id) return;

        fetch(`/groups/search-user-by-id/${id}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    usuarioNoEncontrado.textContent = errorMessageUser;
                    resultadoBusqueda.classList.remove("d-none");
                    alertSuccess.classList.add("d-none");
                    alertError.classList.remove("d-none");
                    return;
                }
                usuarioBuscado = data;
                nombreUsuarioEncontrado.textContent = `${data.username} (ID: ${data.id})`;
                resultadoBusqueda.classList.remove("d-none");
                alertError.classList.add("d-none");
                alertSuccess.classList.remove("d-none");
            })
            .catch(error => {
                console.error(catch1, error);
                alert(catch2);
            });
    });

    // Mostrar modal de confirmación para agregar
    document.getElementById("btnVerConfirmarAgregar").addEventListener("click", () => {
        usuarioAConfirmar.textContent = `${usuarioBuscado.username} (ID: ${usuarioBuscado.id})`;
        const modal1 = bootstrap.Modal.getInstance(document.getElementById("modalGestionMiembros"));
        const modal2 = new bootstrap.Modal(document.getElementById("modalConfirmarAgregar"));
        document.getElementById("modalGestionMiembros").addEventListener("hidden.bs.modal", () => {
            modal2.show();
        }, { once: true });
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

    // Render lista con opción de transferir
    function renderLista() {
        listaUl.innerHTML = "";
        miembros.forEach(u => {
            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between align-items-center";

            const texto = document.createElement("span");
            texto.textContent = u.username;

            const actions = document.createElement("div");
            actions.className = "d-flex gap-2";

            const esMiembroOriginal = miembrosOriginales.includes(u.id);

            if (u.id !== creatorId) {
                // Botón eliminar
                const btnEliminar = document.createElement("button");
                btnEliminar.className = "btn btn-sm btn-outline-danger";
                btnEliminar.textContent = "❌";
                btnEliminar.onclick = () => {
                    miembros = miembros.filter(m => m.id !== u.id);
                    renderLista();
                };

                

                // Botón transferir (solo si ya estaba en el grupo)
                if (esMiembroOriginal) {
                    const btnTransferir = document.createElement("button");
                    btnTransferir.className = "btn btn-sm btn-outline-warning";
                    btnTransferir.textContent = "👑";
                    btnTransferir.onclick = () => {
                        usuarioATransferir = u;
                        confirmarTransferir.textContent = `${u.username} (ID: ${u.id})`;
                        new bootstrap.Modal(document.getElementById("modalTransferencia")).show();
                    };
                    actions.appendChild(btnTransferir);
                }

                actions.appendChild(btnEliminar);
            } else {
                const badge = document.createElement("span");
                badge.className = "badge bg-secondary";
                badge.textContent = ownerLabel;
                actions.appendChild(badge);
            }

            li.appendChild(texto);
            li.appendChild(actions);
            listaUl.appendChild(li);
        });
    }

    // Confirmar transferencia
    document.getElementById("btnTransferirGrupo").addEventListener("click", () => {
        if (!usuarioATransferir) return;
        fetch(`/groups/transfer`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                group_code: groupCode,
                new_owner_id: usuarioATransferir.id
            })
        })
        .then(res => {
            if (res.ok) location.reload();
            else alert("Error al transferir el grupo");
        });
    });
});





//GESTIONA SALIR DEL GRUPO
document.addEventListener("DOMContentLoaded", () => {
    const leaveModal = document.getElementById("leaveGroupModal");

    const groupData = document.getElementById("groupData");
    const currentUserId = groupData.dataset.currentUserId;
    const isCreator = parseInt(groupData.dataset.creatorId) === parseInt(currentUserId);
    const memberCount = parseInt(groupData.dataset.memberCount);
    const groupCode = groupData.dataset.groupCode;

    const creatorCantLeave = groupData.dataset.creatorCantLeave;
    const mustTransfer = groupData.dataset.mustTransfer;
    const understood = groupData.dataset.understood;
    const onlyMember = groupData.dataset.onlyMember;
    const willDelete = groupData.dataset.willDelete;
    const cancel = groupData.dataset.cancel;
    const leaveDelete = groupData.dataset.leaveDelete;
    const confirmLeave = groupData.dataset.confirmLeave;
    const leaveGroup = groupData.dataset.leaveGroup;

    leaveModal.addEventListener("show.bs.modal", () => {
        const body = document.getElementById("leaveGroupModalBody");
        const footer = document.getElementById("leaveGroupModalFooter");

        body.innerHTML = "";
        footer.innerHTML = "";

        if (isCreator === true && memberCount > 1) {
            // Bloqueo: Creador no puede abandonar con otros miembros
            body.innerHTML = `<div class="alert alert-warning">
                ${creatorCantLeave}
                <br>${mustTransfer}
            </div>`;
            footer.innerHTML = `<button class="btn btn-secondary" data-bs-dismiss="modal">${understood}</button>`;
        } else if (isCreator === true && memberCount <= 1) {
            // Advertencia: eliminará el grupo automáticamente
            body.innerHTML = `<p>${onlyMember}</p>
                <p class="text-danger">${willDelete}</p>`;
            footer.innerHTML = `
                <button class="btn btn-secondary" data-bs-dismiss="modal">${cancel}</button>
                <form method="POST" action="/groups/leave" style="display: inline;">
                    <input type="hidden" name="group_code" value="${groupCode}">
                    <button type="submit" class="btn btn-danger">${leaveDelete}</button>
                </form>`;
        } else {
            // Miembro común: puede abandonar libremente
            body.innerHTML = `<p>${confirmLeave}</p>`;
            footer.innerHTML = `
                <button class="btn btn-secondary" data-bs-dismiss="modal">${cancel}</button>
                <form method="POST" action="/groups/leave" style="display: inline;">
                    <input type="hidden" name="group_code" value="${groupCode}">
                    <button type="submit" class="btn btn-danger">${leaveGroup}</button>
                </form>`;
        }
    });
});
