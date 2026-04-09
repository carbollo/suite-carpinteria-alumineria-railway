from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Suite Carpinteria y Alumineria Pro")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


# --- Clientes ---
@app.post("/api/clientes", response_model=schemas.ClienteOut)
def crear_cliente(item: schemas.ClienteCreate, db: Session = Depends(get_db)):
    nuevo = models.Cliente(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/api/clientes", response_model=list[schemas.ClienteOut])
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(models.Cliente).order_by(models.Cliente.id.desc()).all()


# --- Proveedores ---
@app.post("/api/proveedores", response_model=schemas.ProveedorOut)
def crear_proveedor(item: schemas.ProveedorCreate, db: Session = Depends(get_db)):
    nuevo = models.Proveedor(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/api/proveedores", response_model=list[schemas.ProveedorOut])
def listar_proveedores(db: Session = Depends(get_db)):
    return db.query(models.Proveedor).order_by(models.Proveedor.id.desc()).all()


# --- Materiales ---
@app.post("/api/materiales", response_model=schemas.MaterialOut)
def crear_material(item: schemas.MaterialCreate, db: Session = Depends(get_db)):
    nuevo = models.Material(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/api/materiales", response_model=list[schemas.MaterialOut])
def listar_materiales(db: Session = Depends(get_db)):
    return db.query(models.Material).order_by(models.Material.id.desc()).all()


# --- Proyectos ---
@app.post("/api/proyectos", response_model=schemas.ProyectoOut)
def crear_proyecto(item: schemas.ProyectoCreate, db: Session = Depends(get_db)):
    if not db.get(models.Cliente, item.cliente_id):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    nuevo = models.Proyecto(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/api/proyectos", response_model=list[schemas.ProyectoOut])
def listar_proyectos(db: Session = Depends(get_db)):
    return db.query(models.Proyecto).order_by(models.Proyecto.id.desc()).all()


# --- Presupuestos ---
@app.post("/api/presupuestos", response_model=schemas.PresupuestoOut)
def crear_presupuesto(item: schemas.PresupuestoCreate, db: Session = Depends(get_db)):
    if not db.get(models.Proyecto, item.proyecto_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Calculate totals
    total_base = item.total_materiales + item.total_mano_obra + item.total_transporte
    total_final = total_base + (total_base * (item.margen_porcentaje / 100))
    
    nuevo_presupuesto = models.Presupuesto(
        proyecto_id=item.proyecto_id,
        version=item.version,
        estado=item.estado,
        total_materiales=item.total_materiales,
        total_mano_obra=item.total_mano_obra,
        total_transporte=item.total_transporte,
        margen_porcentaje=item.margen_porcentaje,
        total_final=round(total_final, 2),
        firma_digital=item.firma_digital
    )
    db.add(nuevo_presupuesto)
    db.commit()
    db.refresh(nuevo_presupuesto)
    
    for p_item in item.items:
        subtotal = p_item.cantidad * p_item.precio_unitario
        nuevo_item = models.PresupuestoItem(
            presupuesto_id=nuevo_presupuesto.id,
            material_id=p_item.material_id,
            descripcion=p_item.descripcion,
            cantidad=p_item.cantidad,
            precio_unitario=p_item.precio_unitario,
            subtotal=round(subtotal, 2)
        )
        db.add(nuevo_item)
    db.commit()
    db.refresh(nuevo_presupuesto)
    return nuevo_presupuesto

@app.get("/api/presupuestos", response_model=list[schemas.PresupuestoOut])
def listar_presupuestos(db: Session = Depends(get_db)):
    return db.query(models.Presupuesto).order_by(models.Presupuesto.id.desc()).all()


# --- Empleados ---
@app.post("/api/empleados", response_model=schemas.EmpleadoOut)
def crear_empleado(item: schemas.EmpleadoCreate, db: Session = Depends(get_db)):
    nuevo = models.Empleado(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/api/empleados", response_model=list[schemas.EmpleadoOut])
def listar_empleados(db: Session = Depends(get_db)):
    return db.query(models.Empleado).order_by(models.Empleado.id.desc()).all()


# --- Ordenes Produccion ---
@app.post("/api/ordenes", response_model=schemas.OrdenProduccionOut)
def crear_orden(item: schemas.OrdenProduccionCreate, db: Session = Depends(get_db)):
    nuevo = models.OrdenProduccion(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/api/ordenes", response_model=list[schemas.OrdenProduccionOut])
def listar_ordenes(db: Session = Depends(get_db)):
    return db.query(models.OrdenProduccion).order_by(models.OrdenProduccion.id.desc()).all()


# --- Tareas Produccion ---
@app.post("/api/tareas", response_model=schemas.TareaProduccionOut)
def crear_tarea(item: schemas.TareaProduccionCreate, db: Session = Depends(get_db)):
    nuevo = models.TareaProduccion(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/api/tareas", response_model=list[schemas.TareaProduccionOut])
def listar_tareas(db: Session = Depends(get_db)):
    return db.query(models.TareaProduccion).order_by(models.TareaProduccion.id.desc()).all()


# --- Instalaciones ---
@app.post("/api/instalaciones", response_model=schemas.InstalacionOut)
def crear_instalacion(item: schemas.InstalacionCreate, db: Session = Depends(get_db)):
    nuevo = models.Instalacion(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/api/instalaciones", response_model=list[schemas.InstalacionOut])
def listar_instalaciones(db: Session = Depends(get_db)):
    return db.query(models.Instalacion).order_by(models.Instalacion.id.desc()).all()


# --- Facturas ---
@app.post("/api/facturas", response_model=schemas.FacturaOut)
def crear_factura(item: schemas.FacturaCreate, db: Session = Depends(get_db)):
    nuevo = models.Factura(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/api/facturas", response_model=list[schemas.FacturaOut])
def listar_facturas(db: Session = Depends(get_db)):
    return db.query(models.Factura).order_by(models.Factura.id.desc()).all()


# --- Incidencias ---
@app.post("/api/incidencias", response_model=schemas.IncidenciaOut)
def crear_incidencia(item: schemas.IncidenciaCreate, db: Session = Depends(get_db)):
    nuevo = models.Incidencia(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.get("/api/incidencias", response_model=list[schemas.IncidenciaOut])
def listar_incidencias(db: Session = Depends(get_db)):
    return db.query(models.Incidencia).order_by(models.Incidencia.id.desc()).all()
