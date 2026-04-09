from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Suite Carpinteria y Alumineria")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/clientes", response_model=schemas.ClienteOut)
def crear_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    nuevo = models.Cliente(**cliente.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@app.get("/api/clientes", response_model=list[schemas.ClienteOut])
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(models.Cliente).order_by(models.Cliente.id.desc()).all()


@app.post("/api/proyectos", response_model=schemas.ProyectoOut)
def crear_proyecto(proyecto: schemas.ProyectoCreate, db: Session = Depends(get_db)):
    if not db.get(models.Cliente, proyecto.cliente_id):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    nuevo = models.Proyecto(**proyecto.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@app.get("/api/proyectos", response_model=list[schemas.ProyectoOut])
def listar_proyectos(db: Session = Depends(get_db)):
    return db.query(models.Proyecto).order_by(models.Proyecto.id.desc()).all()


@app.post("/api/presupuestos", response_model=schemas.PresupuestoOut)
def crear_presupuesto(item: schemas.PresupuestoCreate, db: Session = Depends(get_db)):
    if not db.get(models.Proyecto, item.proyecto_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    total_base = item.material + item.mano_obra + item.transporte
    total = total_base + (total_base * (item.margen / 100))
    nuevo = models.Presupuesto(**item.model_dump(), total=round(total, 2))
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@app.get("/api/presupuestos", response_model=list[schemas.PresupuestoOut])
def listar_presupuestos(db: Session = Depends(get_db)):
    return db.query(models.Presupuesto).order_by(models.Presupuesto.id.desc()).all()


@app.post("/api/tareas", response_model=schemas.TareaOut)
def crear_tarea(item: schemas.TareaCreate, db: Session = Depends(get_db)):
    if not db.get(models.Proyecto, item.proyecto_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    nuevo = models.Tarea(**item.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@app.get("/api/tareas", response_model=list[schemas.TareaOut])
def listar_tareas(db: Session = Depends(get_db)):
    return db.query(models.Tarea).order_by(models.Tarea.id.desc()).all()
