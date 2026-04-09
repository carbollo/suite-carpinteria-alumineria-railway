import os
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Form, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from fpdf import FPDF

from . import models, schemas
from .database import Base, engine, get_db

# --- MIGRATION HACK FOR DEVELOPMENT ---
# To apply new columns to existing DBs without Alembic,
# we can try to add them dynamically if they don't exist.
try:
    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate columns for SQLite/Postgres
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # Check Cliente columns
        if "clientes" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("clientes")]
            if "nif" not in columns:
                conn.execute(text("ALTER TABLE clientes ADD COLUMN nif VARCHAR(50)"))
            if "sitio_web" not in columns:
                conn.execute(text("ALTER TABLE clientes ADD COLUMN sitio_web VARCHAR(120)"))
        if "presupuestos" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("presupuestos")]
            if "subtotal" not in columns:
                conn.execute(text("ALTER TABLE presupuestos ADD COLUMN subtotal FLOAT DEFAULT 0.0"))
            if "total_iva" not in columns:
                conn.execute(text("ALTER TABLE presupuestos ADD COLUMN total_iva FLOAT DEFAULT 0.0"))
        if "presupuesto_items" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("presupuesto_items")]
            if "iva_porcentaje" not in columns:
                conn.execute(text("ALTER TABLE presupuesto_items ADD COLUMN iva_porcentaje FLOAT DEFAULT 21.0"))
        
        conn.commit()
except Exception as e:
    print(f"Migration error: {e}")

app = FastAPI(title="Suite Carpinteria y Alumineria Pro")

# Configuración de Sesiones para el Login
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SECRET_KEY", "taller-super-secret-key-123")
)

# Credenciales de Administrador
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependencia de Autenticación
def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return user

# --- Rutas de Autenticación y Vistas ---

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["user"] = username
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request, 
        name="login.html", 
        context={"error": "Usuario o contraseña incorrectos"}
    )

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/health")
def health():
    return {"status": "ok"}


# --- Router de la API (Protegido) ---
api_router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])

@api_router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    clientes = db.query(func.count(models.Cliente.id)).scalar()
    proyectos = db.query(func.count(models.Proyecto.id)).scalar()
    presupuestos = db.query(func.count(models.Presupuesto.id)).scalar()
    ordenes = db.query(func.count(models.OrdenProduccion.id)).scalar()
    
    return {
        "clientes": clientes,
        "proyectos": proyectos,
        "presupuestos": presupuestos,
        "ordenes": ordenes
    }

# --- Empresa ---
@api_router.get("/empresa", response_model=schemas.EmpresaOut)
def obtener_empresa(db: Session = Depends(get_db)):
    empresa = db.query(models.Empresa).first()
    if not empresa:
        empresa = models.Empresa(nombre="TallerPro")
        db.add(empresa)
        db.commit()
        db.refresh(empresa)
    return empresa

@api_router.post("/empresa", response_model=schemas.EmpresaOut)
def actualizar_empresa(item: schemas.EmpresaCreate, db: Session = Depends(get_db)):
    empresa = db.query(models.Empresa).first()
    if not empresa:
        empresa = models.Empresa(**item.model_dump())
        db.add(empresa)
    else:
        for key, value in item.model_dump().items():
            setattr(empresa, key, value)
    db.commit()
    db.refresh(empresa)
    return empresa

# --- Clientes ---
@api_router.post("/clientes", response_model=schemas.ClienteOut)
def crear_cliente(item: schemas.ClienteCreate, db: Session = Depends(get_db)):
    nuevo = models.Cliente(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@api_router.get("/clientes", response_model=list[schemas.ClienteOut])
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(models.Cliente).order_by(models.Cliente.id.desc()).all()

@api_router.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

# --- Proveedores ---
@api_router.post("/proveedores", response_model=schemas.ProveedorOut)
def crear_proveedor(item: schemas.ProveedorCreate, db: Session = Depends(get_db)):
    nuevo = models.Proveedor(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@api_router.get("/proveedores", response_model=list[schemas.ProveedorOut])
def listar_proveedores(db: Session = Depends(get_db)):
    return db.query(models.Proveedor).order_by(models.Proveedor.id.desc()).all()

@api_router.delete("/proveedores/{proveedor_id}")
def eliminar_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Proveedor).filter(models.Proveedor.id == proveedor_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

# --- Materiales ---
@api_router.post("/materiales", response_model=schemas.MaterialOut)
def crear_material(item: schemas.MaterialCreate, db: Session = Depends(get_db)):
    nuevo = models.Material(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@api_router.get("/materiales", response_model=list[schemas.MaterialOut])
def listar_materiales(db: Session = Depends(get_db)):
    return db.query(models.Material).order_by(models.Material.id.desc()).all()

@api_router.delete("/materiales/{material_id}")
def eliminar_material(material_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

# --- Proyectos ---
@api_router.post("/proyectos", response_model=schemas.ProyectoOut)
def crear_proyecto(item: schemas.ProyectoCreate, db: Session = Depends(get_db)):
    if not db.get(models.Cliente, item.cliente_id):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    nuevo = models.Proyecto(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@api_router.get("/proyectos", response_model=list[schemas.ProyectoOut])
def listar_proyectos(db: Session = Depends(get_db)):
    return db.query(models.Proyecto).order_by(models.Proyecto.id.desc()).all()

@api_router.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Proyecto).filter(models.Proyecto.id == proyecto_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

# --- Presupuestos ---
@api_router.post("/presupuestos", response_model=schemas.PresupuestoOut)
def crear_presupuesto(item: schemas.PresupuestoCreate, db: Session = Depends(get_db)):
    if not db.get(models.Proyecto, item.proyecto_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    subtotal = 0.0
    total_iva = 0.0
    
    nuevo_presupuesto = models.Presupuesto(
        proyecto_id=item.proyecto_id,
        version=item.version,
        estado=item.estado,
        margen_porcentaje=item.margen_porcentaje,
        firma_digital=item.firma_digital
    )
    db.add(nuevo_presupuesto)
    db.commit()
    db.refresh(nuevo_presupuesto)
    
    for p_item in item.items:
        item_subtotal = p_item.cantidad * p_item.precio_unitario
        subtotal += item_subtotal
        
        item_base = item_subtotal * (1 + (item.margen_porcentaje / 100))
        item_iva = item_base * (p_item.iva_porcentaje / 100)
        total_iva += item_iva
        
        nuevo_item = models.PresupuestoItem(
            presupuesto_id=nuevo_presupuesto.id,
            material_id=p_item.material_id,
            descripcion=p_item.descripcion,
            cantidad=p_item.cantidad,
            precio_unitario=p_item.precio_unitario,
            iva_porcentaje=p_item.iva_porcentaje,
            subtotal=round(item_subtotal, 2)
        )
        db.add(nuevo_item)
        
    margen_total = subtotal * (item.margen_porcentaje / 100)
    total_final = subtotal + margen_total + total_iva
    
    nuevo_presupuesto.subtotal = round(subtotal, 2)
    nuevo_presupuesto.total_iva = round(total_iva, 2)
    nuevo_presupuesto.total_final = round(total_final, 2)
    
    db.commit()
    db.refresh(nuevo_presupuesto)
    return nuevo_presupuesto

@api_router.get("/presupuestos", response_model=list[schemas.PresupuestoOut])
def listar_presupuestos(db: Session = Depends(get_db)):
    return db.query(models.Presupuesto).order_by(models.Presupuesto.id.desc()).all()

@api_router.delete("/presupuestos/{presupuesto_id}")
def eliminar_presupuesto(presupuesto_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Presupuesto).filter(models.Presupuesto.id == presupuesto_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

@api_router.get("/presupuestos/{presupuesto_id}/pdf")
def generar_pdf_presupuesto(presupuesto_id: int, db: Session = Depends(get_db)):
    presupuesto = db.query(models.Presupuesto).filter(models.Presupuesto.id == presupuesto_id).first()
    if not presupuesto:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    proyecto = presupuesto.proyecto
    cliente = proyecto.cliente
    empresa = db.query(models.Empresa).first()
    nombre_empresa = empresa.nombre if empresa else "TallerPro"

    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(0, 10, f"{nombre_empresa} - Presupuesto #{presupuesto.id}", ln=True, align="C")
    pdf.ln(5)
    
    if empresa:
        pdf.set_font("helvetica", "", 10)
        if empresa.nif: pdf.cell(0, 5, f"NIF: {empresa.nif}", ln=True, align="C")
        if empresa.direccion: pdf.cell(0, 5, f"{empresa.direccion}", ln=True, align="C")
        if empresa.telefono or empresa.email: 
            contacto = " | ".join(filter(None, [empresa.telefono or "", empresa.email or ""]))
            pdf.cell(0, 5, contacto, ln=True, align="C")
    pdf.ln(10)
    
    # Info Cliente
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Datos del Cliente:", ln=True)
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, f"Nombre: {cliente.nombre}", ln=True)
    if cliente.nif:
        pdf.cell(0, 8, f"NIF/CIF: {cliente.nif}", ln=True)
    if cliente.direccion:
        pdf.cell(0, 8, f"Direccion: {cliente.direccion}", ln=True)
    pdf.cell(0, 8, f"Telefono: {cliente.telefono or 'N/A'}", ln=True)
    pdf.cell(0, 8, f"Email: {cliente.email or 'N/A'}", ln=True)
    pdf.ln(5)
    
    # Info Proyecto
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Datos del Proyecto:", ln=True)
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, f"Proyecto: {proyecto.nombre} (#{proyecto.id})", ln=True)
    pdf.cell(0, 8, f"Tipo: {proyecto.tipo.capitalize()}", ln=True)
    pdf.ln(10)
    
    # Desglose
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Conceptos:", ln=True)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(80, 8, "Descripcion", border=1)
    pdf.cell(20, 8, "Cant.", border=1, align="C")
    pdf.cell(30, 8, "Precio U.", border=1, align="C")
    pdf.cell(20, 8, "IVA %", border=1, align="C")
    pdf.cell(40, 8, "Subtotal", border=1, align="C")
    pdf.ln()
    
    pdf.set_font("helvetica", "", 10)
    for item in presupuesto.items:
        pdf.cell(80, 8, item.descripcion[:45], border=1)
        pdf.cell(20, 8, str(item.cantidad), border=1, align="C")
        pdf.cell(30, 8, f"${item.precio_unitario:.2f}", border=1, align="R")
        pdf.cell(20, 8, f"{item.iva_porcentaje}%", border=1, align="C")
        pdf.cell(40, 8, f"${item.subtotal:.2f}", border=1, align="R")
        pdf.ln()
        
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(130, 8, "", border=0)
    pdf.cell(20, 8, "Subtotal:", border=0, align="R")
    pdf.cell(40, 8, f"${presupuesto.subtotal:.2f}", border=1, ln=True, align="R")
    
    margen_val = presupuesto.subtotal * (presupuesto.margen_porcentaje / 100)
    pdf.cell(130, 8, "", border=0)
    pdf.cell(20, 8, f"Margen ({presupuesto.margen_porcentaje}%):", border=0, align="R")
    pdf.cell(40, 8, f"${margen_val:.2f}", border=1, ln=True, align="R")
    
    base_imponible = presupuesto.subtotal + margen_val
    pdf.cell(130, 8, "", border=0)
    pdf.cell(20, 8, "Base Imp.:", border=0, align="R")
    pdf.cell(40, 8, f"${base_imponible:.2f}", border=1, ln=True, align="R")
    
    pdf.cell(130, 8, "", border=0)
    pdf.cell(20, 8, "Total IVA:", border=0, align="R")
    pdf.cell(40, 8, f"${presupuesto.total_iva:.2f}", border=1, ln=True, align="R")
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(130, 10, "", border=0)
    pdf.cell(20, 10, "TOTAL:", border=0, align="R")
    pdf.cell(40, 10, f"${presupuesto.total_final:.2f}", border=1, ln=True, align="R")
    
    pdf.ln(20)
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(0, 10, "Documento generado automaticamente por TallerPro.", ln=True, align="C")

    pdf_bytes = pdf.output()
    
    return Response(content=bytes(pdf_bytes), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=presupuesto_{presupuesto_id}.pdf"
    })

# --- Empleados ---
@api_router.post("/empleados", response_model=schemas.EmpleadoOut)
def crear_empleado(item: schemas.EmpleadoCreate, db: Session = Depends(get_db)):
    nuevo = models.Empleado(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@api_router.get("/empleados", response_model=list[schemas.EmpleadoOut])
def listar_empleados(db: Session = Depends(get_db)):
    return db.query(models.Empleado).order_by(models.Empleado.id.desc()).all()

@api_router.delete("/empleados/{empleado_id}")
def eliminar_empleado(empleado_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Empleado).filter(models.Empleado.id == empleado_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

# --- Ordenes Produccion ---
@api_router.post("/ordenes", response_model=schemas.OrdenProduccionOut)
def crear_orden(item: schemas.OrdenProduccionCreate, db: Session = Depends(get_db)):
    nuevo = models.OrdenProduccion(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@api_router.get("/ordenes", response_model=list[schemas.OrdenProduccionOut])
def listar_ordenes(db: Session = Depends(get_db)):
    return db.query(models.OrdenProduccion).order_by(models.OrdenProduccion.id.desc()).all()

@api_router.delete("/ordenes/{orden_id}")
def eliminar_orden(orden_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.OrdenProduccion).filter(models.OrdenProduccion.id == orden_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

# --- Tareas Produccion ---
@api_router.post("/tareas", response_model=schemas.TareaProduccionOut)
def crear_tarea(item: schemas.TareaProduccionCreate, db: Session = Depends(get_db)):
    nuevo = models.TareaProduccion(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@api_router.get("/tareas", response_model=list[schemas.TareaProduccionOut])
def listar_tareas(db: Session = Depends(get_db)):
    return db.query(models.TareaProduccion).order_by(models.TareaProduccion.id.desc()).all()

@api_router.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.TareaProduccion).filter(models.TareaProduccion.id == tarea_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

# --- Instalaciones ---
@api_router.post("/instalaciones", response_model=schemas.InstalacionOut)
def crear_instalacion(item: schemas.InstalacionCreate, db: Session = Depends(get_db)):
    nuevo = models.Instalacion(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@api_router.get("/instalaciones", response_model=list[schemas.InstalacionOut])
def listar_instalaciones(db: Session = Depends(get_db)):
    return db.query(models.Instalacion).order_by(models.Instalacion.id.desc()).all()

@api_router.delete("/instalaciones/{instalacion_id}")
def eliminar_instalacion(instalacion_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Instalacion).filter(models.Instalacion.id == instalacion_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

# --- Facturas ---
@api_router.post("/facturas", response_model=schemas.FacturaOut)
def crear_factura(item: schemas.FacturaCreate, db: Session = Depends(get_db)):
    nuevo = models.Factura(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@api_router.get("/facturas", response_model=list[schemas.FacturaOut])
def listar_facturas(db: Session = Depends(get_db)):
    return db.query(models.Factura).order_by(models.Factura.id.desc()).all()

@api_router.delete("/facturas/{factura_id}")
def eliminar_factura(factura_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Factura).filter(models.Factura.id == factura_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

# --- Incidencias ---
@api_router.post("/incidencias", response_model=schemas.IncidenciaOut)
def crear_incidencia(item: schemas.IncidenciaCreate, db: Session = Depends(get_db)):
    nuevo = models.Incidencia(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@api_router.get("/incidencias", response_model=list[schemas.IncidenciaOut])
def listar_incidencias(db: Session = Depends(get_db)):
    return db.query(models.Incidencia).order_by(models.Incidencia.id.desc()).all()

@api_router.delete("/incidencias/{incidencia_id}")
def eliminar_incidencia(incidencia_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Incidencia).filter(models.Incidencia.id == incidencia_id).first()
    if not obj: raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(obj)
    db.commit()
    return {"status": "eliminado"}

# Incluir el router en la app
app.include_router(api_router)
