// Helper para llamadas a la API
async function api(path, options = {}) {
    const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    if (response.status === 401) {
        window.location.href = "/login";
        return;
    }
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Error en la solicitud");
    }
    return response.json();
}

// Helper para extraer datos de formularios
function getFormData(form) {
    const data = {};
    for (const [key, value] of new FormData(form).entries()) {
        if (value === "") continue;
        if (["cliente_id", "proyecto_id", "presupuesto_id", "orden_id"].includes(key)) data[key] = Number(value);
        else if (["total_materiales", "total_mano_obra", "total_transporte", "margen_porcentaje", "precio_unitario", "stock_actual", "monto"].includes(key)) data[key] = Number(value);
        else data[key] = value;
    }
    return data;
}

// Helper para notificaciones Toast
function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    const msg = document.getElementById("toast-msg");
    const icon = toast.querySelector("i");
    
    msg.textContent = message;
    if(isError) {
        icon.className = "fa-solid fa-circle-exclamation text-red-400 mr-3";
    } else {
        icon.className = "fa-solid fa-circle-check text-emerald-400 mr-3";
    }

    toast.classList.remove("translate-y-20", "opacity-0");
    setTimeout(() => {
        toast.classList.add("translate-y-20", "opacity-0");
    }, 3000);
}

// Modales
function openModal(id) {
    document.getElementById("modal-overlay").classList.remove("hidden");
    document.getElementById(id).classList.remove("hidden");
}

function closeModal(id) {
    document.getElementById("modal-overlay").classList.add("hidden");
    document.getElementById(id).classList.add("hidden");
    const form = document.getElementById(id).querySelector("form");
    if(form) form.reset();
}

// Navegación de Módulos
function showModule(moduleId, navElement) {
    // Esconder todos los módulos
    document.querySelectorAll(".module").forEach(m => m.classList.add("hidden"));
    document.querySelectorAll(".module").forEach(m => m.classList.remove("active"));
    
    // Mostrar el seleccionado
    const target = document.getElementById("module-" + moduleId);
    if(target) {
        target.classList.remove("hidden");
        target.classList.add("active");
    }

    // Actualizar estilos del menú
    if (navElement) {
        document.querySelectorAll(".nav-link").forEach(l => {
            l.classList.remove("bg-slate-800", "text-white", "border-l-4", "border-brand-500");
            l.classList.add("text-slate-300");
        });
        navElement.classList.add("bg-slate-800", "text-white", "border-l-4", "border-brand-500");
        
        // Actualizar título de cabecera
        document.getElementById("page-title").textContent = navElement.textContent.trim();
    }

    refreshData();
}

// Generador de Badges de Estado
function getStatusBadge(status) {
    const s = (status || "").toLowerCase();
    let color = "bg-gray-100 text-gray-800";
    if (["completado", "pagada", "entregado", "aceptado"].includes(s)) color = "bg-emerald-100 text-emerald-800";
    else if (["pendiente", "planificacion"].includes(s)) color = "bg-amber-100 text-amber-800";
    else if (["en_proceso", "cortando", "soldando"].includes(s)) color = "bg-blue-100 text-blue-800";
    else if (["rechazado", "vencida", "urgente"].includes(s)) color = "bg-red-100 text-red-800";
    
    return `<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${color}">${status}</span>`;
}

// Eliminar Registro
async function deleteRecord(endpoint, id) {
    if(!confirm(`¿Estás seguro de eliminar el registro #${id}? Esta acción no se puede deshacer.`)) return;
    try {
        await api(`${endpoint}/${id}`, { method: "DELETE" });
        showToast("Registro eliminado correctamente");
        refreshData();
    } catch (err) {
        showToast(err.message, true);
    }
}

// Renderizar Tablas
function renderTable(id, rows, columns) {
    const tbody = document.getElementById(id);
    if (!tbody) return;
    tbody.innerHTML = "";
    
    if(rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${columns.length + 1}" class="px-6 py-4 text-center text-sm text-gray-500">No hay registros disponibles</td></tr>`;
        return;
    }

    rows.forEach(row => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-gray-50 transition-colors";
        
        let html = "";
        columns.forEach(col => {
            let val = row[col.key];
            if(col.type === "status") val = getStatusBadge(val);
            if(col.type === "currency") val = `$${Number(val).toFixed(2)}`;
            html += `<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">${val || '-'}</td>`;
        });
        
        // Columna de acciones
        html += `<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <button onclick="deleteRecord('${columns[0].endpoint}', ${row.id})" class="text-red-500 hover:text-red-700 transition-colors" title="Eliminar"><i class="fa-solid fa-trash"></i></button>
        </td>`;
        
        tr.innerHTML = html;
        tbody.appendChild(tr);
    });
}

// Refrescar Datos
async function refreshData() {
    try {
        // Dashboard Stats
        if(document.getElementById("module-dashboard").classList.contains("active")) {
            const stats = await api("/api/dashboard/stats");
            document.getElementById("stat-clientes").textContent = stats.clientes;
            document.getElementById("stat-proyectos").textContent = stats.proyectos;
            document.getElementById("stat-presupuestos").textContent = stats.presupuestos;
            document.getElementById("stat-ordenes").textContent = stats.ordenes;
        }

        // Clientes y Proyectos
        if(document.getElementById("module-clientes").classList.contains("active")) {
            const [clientes, proyectos] = await Promise.all([api("/api/clientes"), api("/api/proyectos")]);
            renderTable("table-clientes", clientes, [
                {key: "id", endpoint: "/api/clientes"}, {key: "nombre"}, {key: "telefono"}, {key: "clasificacion"}
            ]);
            renderTable("table-proyectos", proyectos, [
                {key: "id", endpoint: "/api/proyectos"}, {key: "nombre"}, {key: "cliente_id"}, {key: "estado", type: "status"}
            ]);
        }
        
        // Presupuestos
        if(document.getElementById("module-presupuestos").classList.contains("active")) {
            const presupuestos = await api("/api/presupuestos");
            renderTable("table-presupuestos", presupuestos, [
                {key: "id", endpoint: "/api/presupuestos"}, {key: "proyecto_id"}, {key: "total_final", type: "currency"}, {key: "estado", type: "status"}
            ]);
        }

        // Producción
        if(document.getElementById("module-produccion").classList.contains("active")) {
            const ordenes = await api("/api/ordenes");
            renderTable("table-ordenes", ordenes, [
                {key: "id", endpoint: "/api/ordenes"}, {key: "proyecto_id"}, {key: "prioridad", type: "status"}, {key: "estado", type: "status"}
            ]);
        }

        // Almacén
        if(document.getElementById("module-almacen").classList.contains("active")) {
            const materiales = await api("/api/materiales");
            renderTable("table-materiales", materiales, [
                {key: "referencia", endpoint: "/api/materiales"}, {key: "tipo"}, {key: "stock_actual"}, {key: "precio_unitario", type: "currency"}
            ]);
        }

    } catch (e) {
        console.error("Error al cargar datos:", e);
        showToast("Error de conexión con el servidor", true);
    }
}

// Configurar Formularios
function wireForm(formId, endpoint, modalId) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            await api(endpoint, { method: "POST", body: JSON.stringify(getFormData(form)) });
            if(modalId) closeModal(modalId);
            showToast("Guardado correctamente");
            refreshData();
        } catch (err) {
            showToast(err.message, true);
        }
    });
}

// Inicialización
document.addEventListener("DOMContentLoaded", () => {
    wireForm("form-clientes", "/api/clientes", "modal-cliente");
    wireForm("form-proyectos", "/api/proyectos", "modal-proyecto");
    wireForm("form-presupuestos", "/api/presupuestos", "modal-presupuesto");
    wireForm("form-ordenes", "/api/ordenes", "modal-orden");
    wireForm("form-materiales", "/api/materiales", "modal-material");

    // Inicializar menú
    const firstNav = document.querySelector(".nav-link");
    if(firstNav) firstNav.classList.add("border-l-4", "border-brand-500");
    
    refreshData();
});
