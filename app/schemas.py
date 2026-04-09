from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


# --- Cliente ---
class ClienteBase(BaseModel):
    nombre: str
    nif: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    sitio_web: Optional[str] = None
    clasificacion: str = "particular"
    portal_acceso: bool = False

class ClienteCreate(ClienteBase):
    pass

class ClienteOut(ClienteBase):
    id: int

    class Config:
        from_attributes = True


# --- Proveedor ---
class ProveedorBase(BaseModel):
    nombre: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorOut(ProveedorBase):
    id: int

    class Config:
        from_attributes = True


# --- Material ---
class MaterialBase(BaseModel):
    tipo: str
    referencia: str
    descripcion: Optional[str] = None
    proveedor_id: Optional[int] = None
    precio_unitario: float = 0.0
    stock_actual: float = 0.0
    stock_minimo: float = 0.0
    unidad_medida: str = "unidad"
    longitud_restante: Optional[float] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialOut(MaterialBase):
    id: int

    class Config:
        from_attributes = True


# --- Proyecto ---
class ProyectoBase(BaseModel):
    nombre: str
    tipo: str
    estado: str = "planificacion"
    descripcion: Optional[str] = None
    direccion_obra: Optional[str] = None
    geolocalizacion: Optional[str] = None
    cliente_id: int

class ProyectoCreate(ProyectoBase):
    pass

class ProyectoOut(ProyectoBase):
    id: int
    creado_en: datetime

    class Config:
        from_attributes = True


# --- PresupuestoItem ---
class PresupuestoItemBase(BaseModel):
    material_id: Optional[int] = None
    descripcion: str
    cantidad: float = 1.0
    precio_unitario: float = 0.0

class PresupuestoItemCreate(PresupuestoItemBase):
    pass

class PresupuestoItemOut(PresupuestoItemBase):
    id: int
    presupuesto_id: int
    subtotal: float

    class Config:
        from_attributes = True


# --- Presupuesto ---
class PresupuestoBase(BaseModel):
    proyecto_id: int
    version: int = 1
    estado: str = "pendiente"
    total_materiales: float = 0.0
    total_mano_obra: float = 0.0
    total_transporte: float = 0.0
    margen_porcentaje: float = 0.0
    firma_digital: bool = False

class PresupuestoCreate(PresupuestoBase):
    items: Optional[List[PresupuestoItemCreate]] = []

class PresupuestoOut(PresupuestoBase):
    id: int
    total_final: float
    fecha_creacion: datetime
    items: List[PresupuestoItemOut] = []

    class Config:
        from_attributes = True


# --- Empleado ---
class EmpleadoBase(BaseModel):
    nombre: str
    rol: str
    telefono: Optional[str] = None

class EmpleadoCreate(EmpleadoBase):
    pass

class EmpleadoOut(EmpleadoBase):
    id: int

    class Config:
        from_attributes = True


# --- OrdenProduccion ---
class OrdenProduccionBase(BaseModel):
    proyecto_id: int
    presupuesto_id: Optional[int] = None
    estado: str = "pendiente"
    fecha_limite: Optional[datetime] = None
    prioridad: str = "normal"

class OrdenProduccionCreate(OrdenProduccionBase):
    pass

class OrdenProduccionOut(OrdenProduccionBase):
    id: int

    class Config:
        from_attributes = True


# --- TareaProduccion ---
class TareaProduccionBase(BaseModel):
    orden_id: int
    operario_id: Optional[int] = None
    descripcion: str
    estado: str = "pendiente"
    tiempo_registrado_horas: float = 0.0

class TareaProduccionCreate(TareaProduccionBase):
    pass

class TareaProduccionOut(TareaProduccionBase):
    id: int

    class Config:
        from_attributes = True


# --- Instalacion ---
class InstalacionBase(BaseModel):
    proyecto_id: int
    fecha_programada: Optional[datetime] = None
    vehiculo: Optional[str] = None
    estado: str = "programada"
    firma_cliente: bool = False
    notas: Optional[str] = None

class InstalacionCreate(InstalacionBase):
    pass

class InstalacionOut(InstalacionBase):
    id: int

    class Config:
        from_attributes = True


# --- Factura ---
class FacturaBase(BaseModel):
    cliente_id: int
    proyecto_id: Optional[int] = None
    monto: float
    estado: str = "emitida"
    fecha_vencimiento: Optional[datetime] = None

class FacturaCreate(FacturaBase):
    pass

class FacturaOut(FacturaBase):
    id: int
    fecha_emision: datetime

    class Config:
        from_attributes = True


# --- Incidencia ---
class IncidenciaBase(BaseModel):
    proyecto_id: int
    descripcion: str
    estado: str = "abierta"
    resolucion: Optional[str] = None

class IncidenciaCreate(IncidenciaBase):
    pass

class IncidenciaOut(IncidenciaBase):
    id: int
    fecha_reporte: datetime

    class Config:
        from_attributes = True


# --- Empresa ---
class EmpresaBase(BaseModel):
    nombre: str
    nif: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    sitio_web: Optional[str] = None

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaOut(EmpresaBase):
    id: int

    class Config:
        from_attributes = True
