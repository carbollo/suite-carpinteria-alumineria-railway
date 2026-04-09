from pydantic import BaseModel


class ClienteBase(BaseModel):
    nombre: str
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None


class ClienteCreate(ClienteBase):
    pass


class ClienteOut(ClienteBase):
    id: int

    class Config:
        from_attributes = True


class ProyectoBase(BaseModel):
    nombre: str
    tipo: str
    estado: str = "planificacion"
    descripcion: str | None = None
    cliente_id: int


class ProyectoCreate(ProyectoBase):
    pass


class ProyectoOut(ProyectoBase):
    id: int

    class Config:
        from_attributes = True


class PresupuestoBase(BaseModel):
    proyecto_id: int
    material: float = 0
    mano_obra: float = 0
    transporte: float = 0
    margen: float = 0


class PresupuestoCreate(PresupuestoBase):
    pass


class PresupuestoOut(PresupuestoBase):
    id: int
    total: float

    class Config:
        from_attributes = True


class TareaBase(BaseModel):
    proyecto_id: int
    titulo: str
    estado: str = "pendiente"
    responsable: str | None = None


class TareaCreate(TareaBase):
    pass


class TareaOut(TareaBase):
    id: int

    class Config:
        from_attributes = True
