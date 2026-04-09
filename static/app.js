async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Error en solicitud");
  }
  return response.json();
}

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

function renderList(id, rows, mapper) {
  const container = document.getElementById(id);
  if (!container) return;
  container.innerHTML = "";
  for (const row of rows) {
    const li = document.createElement("li");
    li.textContent = mapper(row);
    container.appendChild(li);
  }
}

async function refresh() {
  try {
    const [clientes, proyectos, presupuestos, ordenes] = await Promise.all([
      api("/api/clientes"),
      api("/api/proyectos"),
      api("/api/presupuestos"),
      api("/api/ordenes"),
    ]);

    renderList("list-clientes", clientes, (c) => `#${c.id} ${c.nombre} (${c.clasificacion})`);
    renderList("list-proyectos", proyectos, (p) => `#${p.id} ${p.nombre} - ${p.estado}`);
    renderList("list-presupuestos", presupuestos, (p) => `#${p.id} Proyecto ${p.proyecto_id}: $${p.total_final} (${p.estado})`);
    renderList("list-ordenes", ordenes, (o) => `#${o.id} Proyecto ${o.proyecto_id} - ${o.estado}`);
  } catch (e) {
    console.error("Error al cargar datos:", e);
  }
}

function wireForm(formId, endpoint) {
  const form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api(endpoint, { method: "POST", body: JSON.stringify(getFormData(form)) });
      form.reset();
      alert("Guardado correctamente");
      await refresh();
    } catch (err) {
      alert(err.message);
    }
  });
}

function showModule(moduleId) {
  document.querySelectorAll(".module").forEach(m => m.classList.remove("active"));
  document.getElementById("module-" + moduleId).classList.add("active");
  refresh();
}

// Wire all forms
wireForm("form-clientes", "/api/clientes");
wireForm("form-proyectos", "/api/proyectos");
wireForm("form-presupuestos", "/api/presupuestos");
wireForm("form-ordenes", "/api/ordenes");
wireForm("form-tareas", "/api/tareas");
wireForm("form-materiales", "/api/materiales");
wireForm("form-instalaciones", "/api/instalaciones");
wireForm("form-facturas", "/api/facturas");
wireForm("form-proveedores", "/api/proveedores");
wireForm("form-incidencias", "/api/incidencias");

refresh();
