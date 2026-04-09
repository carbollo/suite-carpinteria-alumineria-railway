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
    if (["cliente_id", "proyecto_id"].includes(key)) data[key] = Number(value);
    else if (["material", "mano_obra", "transporte", "margen"].includes(key)) data[key] = Number(value);
    else data[key] = value;
  }
  return data;
}

function renderList(id, rows, mapper) {
  const container = document.getElementById(id);
  container.innerHTML = "";
  for (const row of rows) {
    const li = document.createElement("li");
    li.textContent = mapper(row);
    container.appendChild(li);
  }
}

async function refresh() {
  const [clientes, proyectos, presupuestos, tareas] = await Promise.all([
    api("/api/clientes"),
    api("/api/proyectos"),
    api("/api/presupuestos"),
    api("/api/tareas"),
  ]);

  renderList("clientes", clientes, (c) => `#${c.id} ${c.nombre}`);
  renderList("proyectos", proyectos, (p) => `#${p.id} ${p.nombre} (${p.tipo})`);
  renderList("presupuestos", presupuestos, (p) => `#${p.id} proyecto ${p.proyecto_id}: $${p.total}`);
  renderList("tareas", tareas, (t) => `#${t.id} ${t.titulo} (${t.estado})`);
}

function wireForm(formId, endpoint) {
  document.getElementById(formId).addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    try {
      await api(endpoint, { method: "POST", body: JSON.stringify(getFormData(form)) });
      form.reset();
      await refresh();
    } catch (err) {
      alert(err.message);
    }
  });
}

wireForm("cliente-form", "/api/clientes");
wireForm("proyecto-form", "/api/proyectos");
wireForm("presupuesto-form", "/api/presupuestos");
wireForm("tarea-form", "/api/tareas");
refresh();
